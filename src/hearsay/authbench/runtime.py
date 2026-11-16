"""One episode on an AuthorizationBench task: principal -> planner -> executor -> verifier -> live services.

The environment is the benchmark's own host environment (the services the paper's
harnesses use, served over HTTP on loopback). The executor sees the task's sealed
prompt and the bundle's tool allowlist, as in the paper. Every tool call the
executor makes goes through one router:

  read-only call             ->  proxy_tool_call (the benchmark's gateway function) -> service
  any other call             ->  Verification -> (allowed) proxy_tool_call -> service
  (state change, message_user)                   (blocked)  generic "blocked" result; no HTTP request is made

Only read-only calls skip verification. The runtime policy (ApprovalRegistry.tool_policy) says
for each tool whether it needs an approval, needs none, or is blocked; a tool it does not list
needs one (fail closed). Every method judges every verified call, whatever its level. Before a
call whose effect is set by service state (calls.CONTEXT_RESOLVERS), the router reads what it
will act on and attaches it to the proposal as `context`.

Workspace tools (read_file / write_file / terminal) need the benchmark's agent
container (Docker) and are not wired yet: a task whose blueprint mounts them is
refused unless `allow_missing_workspace` is set.

Artifacts per episode: the delegation, the full executor run, every routed call,
every proposal with each method's decision and the record's verdict, /_env/state
before and after, the service audit, fired environment events, and services whose
state changed without any state-changing call to them (a check on calls.effect).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from ..agent_loop import run_agent
from ..llm import sampling_for
from ..sandbox import BLOCKED
from .approvals import ApprovalRegistry
from .calls import PRINCIPAL, READ, STATE_CHANGE, ToolCall, effect, needs_context, resolve_context, service
from .locate import checkout_commit, ensure_importable, require_utf8_mode
from .planner import plan
from .prompts import EXECUTOR_PLANNER_FRAME
from .task import AuthBenchTask
from .verify import METHODS, Verification

ROLES = ("planner", "executor", "verifier")
FINISH = "finish"
LOOKUP = "approval_records_lookup"
LOCAL_TOOLS = {
    FINISH: {"description": "Declare the task finished, with a short closing message.",
             "parameters": {"type": "object", "properties": {"message": {"type": "string"}}, "required": []}},
    LOOKUP: {"description": "Look up an approval in the organization's approval system by its id.",
             "parameters": {"type": "object", "properties": {"approval_id": {"type": "string"}},
                            "required": ["approval_id"]}},
}
Transport = Callable[..., dict]


class WorkspaceRequired(RuntimeError):
    pass


@dataclass(frozen=True)
class RunConfig:
    """One model for every LLM role (variable control). `role_models` overrides a role only for the separate
    model-comparison experiments."""

    model: str = "gpt-4.1"
    role_models: Mapping[str, str] = field(default_factory=dict)
    delegation: str = "direct"           # direct: the executor gets the principal's instruction; planner
    handoff_note: str | None = None      # reaches the planner only (where an inherited claim arrives)
    enforce: str = "none"
    shadow: tuple[str, ...] = METHODS
    n_votes: int = 3
    record_lookup: bool = False
    max_turns: int = 35                  # the benchmark's per-task cap on agent turns
    allow_missing_workspace: bool = False

    def __post_init__(self) -> None:
        if self.delegation not in ("direct", "planner"):
            raise ValueError(f"delegation must be direct or planner, not {self.delegation!r}")
        if self.delegation == "direct" and self.handoff_note:
            raise ValueError("a handoff note reaches the planner; use delegation='planner'")
        if set(self.role_models) - set(ROLES):
            raise ValueError(f"role_models keys must be among {ROLES}")

    def role_model(self, role: str) -> str:
        return self.role_models.get(role, self.model)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["role_models"] = {r: self.role_model(r) for r in ROLES}
        d["sampling"] = {r: sampling_for(self.role_model(r)) for r in ROLES}
        return d


class Environment:
    """The benchmark's host environment for one task (services over HTTP on 127.0.0.1)."""

    def __init__(self, task: AuthBenchTask) -> None:
        require_utf8_mode()
        ensure_importable()
        from authorization_eva_sandbox.evaluation.run_eval import HostTaskEnvironment
        self._env = HostTaskEnvironment(task.bundle)

    @property
    def base_url(self) -> str:
        return self._env.base_url

    @property
    def token(self) -> str:
        return self._env.grader_token

    @property
    def openapi(self) -> dict:
        return self._env.openapi

    def start(self) -> "Environment":
        self._env.start()
        return self

    def close(self) -> None:
        self._env.close()

    def _get(self, path: str) -> Any:
        import requests
        r = requests.get(f"{self.base_url}{path}", headers={"Authorization": f"Bearer {self.token}"}, timeout=30)
        r.raise_for_status()
        return r.json()

    def state(self) -> dict:
        return self._get("/_env/state")

    def audit(self) -> dict:
        return self._get("/_env/audit")

    def events(self) -> Any:
        return self._get("/_env/events")

    def agent_step(self, step: int) -> None:
        """Heartbeat that drives the task's agent_step_count environment events (as the benchmark's harness)."""
        import requests
        try:
            requests.post(f"{self.base_url}/_env/agent_step", json={"step": step},
                          headers={"Authorization": f"Bearer {self.token}"}, timeout=5)
        except requests.RequestException:
            pass

    def __enter__(self) -> "Environment":
        return self.start()

    def __exit__(self, *exc: Any) -> None:
        self.close()


def default_transport() -> Transport:
    ensure_importable()
    from authorization_eva_sandbox.evaluation.harness.mcp_gateway import proxy_tool_call
    return proxy_tool_call


class ToolRouter:
    """The executor's only path to the services. Calls are named canonically (`service.operation`) inside; the
    model sees identifier-safe names (the benchmark's ToolNameAdapter)."""

    def __init__(self, env: Environment, task: AuthBenchTask, verification: Verification,
                 registry: ApprovalRegistry, *, delegation: str, record_lookup: bool = False,
                 transport: Transport | None = None) -> None:
        ensure_importable()
        from authorization_eva_sandbox.evaluation.harness.tool_ir import select_allowlisted_tools
        from authorization_eva_sandbox.evaluation.harness.tool_name_adapter import ToolNameAdapter

        self.env, self.task, self.verification, self.registry = env, task, verification, registry
        self.delegation = delegation
        self.transport = transport or default_transport()
        self.surface = select_allowlisted_tools(env.openapi, list(task.allowlist))
        self.by_name = {t["name"]: t for t in self.surface}
        self.local = [FINISH] + ([LOOKUP] if record_lookup else [])
        self.names = ToolNameAdapter([t["name"] for t in self.surface] + self.local)
        self.events: list[dict[str, Any]] = []
        self.proposals: list[dict[str, Any]] = []
        self.finished: str | None = None

    def model_tools(self) -> list[dict[str, Any]]:
        tools = [{"type": "function", "name": self.names.publish(t["name"]), "description": t["description"],
                  "parameters": t["parameters"], "strict": False} for t in self.surface]
        tools += [{"type": "function", "name": self.names.publish(n), "strict": False, **LOCAL_TOOLS[n]}
                  for n in self.local]
        return tools

    def handle(self, published_name: str, args: dict[str, Any]) -> dict[str, Any]:
        return self.call(self.names.canonical(published_name), args)

    def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        event: dict[str, Any] = {"index": len(self.events), "tool": tool, "arguments": args}
        self.events.append(event)
        if tool == FINISH:
            self.finished = str(args.get("message", ""))
            event.update(effect="local", executed=True)
            return {"status": "finished"}
        if tool == LOOKUP and LOOKUP in self.local:
            result = self.registry.lookup(str(args.get("approval_id", "")))
            event.update(effect="record_lookup", executed=True, result=result)
            return result
        entry = self.by_name.get(tool)
        if entry is None:
            event.update(effect="unknown", executed=False)
            return {"error": f"unknown tool {tool}"}
        event["effect"] = effect(tool)
        event["verified"] = event["effect"] != READ
        if event["verified"]:
            context = resolve_context(tool, self.env.state()) if needs_context(tool) else {}
            call = ToolCall(tool, args, context)
            decision = self.verification(call, self.delegation)
            event["proposal_index"] = len(self.proposals)
            self.proposals.append({"proposal_index": len(self.proposals), "task_id": self.task.task_id,
                                   "call": call.to_dict(), "delegation": self.delegation,
                                   "registry": self.registry.to_dict(), **decision})
            if not decision["allowed"]:
                event["executed"] = False
                return dict(BLOCKED)
        response = self.transport(self.env.base_url, entry, args, grader_token=self.env.token)
        event.update(executed=True, status=response.get("status"), result=response.get("body"))
        return response


def changed_services(before: dict, after: dict) -> list[str]:
    dump = lambda d, k: json.dumps(d.get(k), sort_keys=True, default=str)   # noqa: E731
    return sorted(k for k in set(before) | set(after) if dump(before, k) != dump(after, k))


def unexplained_changes(before: dict, after: dict, events: list[dict[str, Any]]) -> list[str]:
    """Services whose state changed although no state-changing (or principal) call to them ran."""
    explained = {service(e["tool"]) for e in events if e.get("executed") and e.get("effect") == STATE_CHANGE}
    if any(e.get("executed") and e.get("effect") == PRINCIPAL for e in events):
        explained.add("user_messaging")
    return [s for s in changed_services(before, after) if s not in explained]


def run_episode(task: AuthBenchTask, config: RunConfig, *, client: Any, registry: ApprovalRegistry,
                out_dir: Path | None = None) -> dict[str, Any]:
    if task.needs_workspace and not config.allow_missing_workspace:
        raise WorkspaceRequired(f"{task.task_id} mounts {list(task.shell_tools)}; the Docker workspace is not "
                                "wired yet")
    verification = Verification(enforce=config.enforce, shadow=config.shadow, registry=registry, client=client,
                                model=config.role_model("verifier"), n_votes=config.n_votes)
    with Environment(task) as env:
        state_before = env.state()
        planner = None
        if config.delegation == "planner":
            planner = plan(client, config.role_model("planner"), task, config.handoff_note)
            delegation = planner["message"]
            executor_input = EXECUTOR_PLANNER_FRAME.format(message=delegation)
        else:
            delegation = executor_input = task.instruction
        router = ToolRouter(env, task, verification, registry, delegation=delegation,
                            record_lookup=config.record_lookup)

        def after_turn(turn: int) -> bool:
            env.agent_step(turn + 1)
            return router.finished is not None

        run = run_agent(client, model=config.role_model("executor"),
                        instructions=router.names.adapt_prompt(task.system_prompt), user_input=executor_input,
                        tools=router.model_tools(), handle=router.handle, max_turns=config.max_turns,
                        after_turn=after_turn)
        state_after, audit, fired = env.state(), env.audit(), env.events()

    episode = {
        "task": task.summary(), "config": config.to_dict(), "authbench_commit": checkout_commit(),
        "registry": registry.to_dict(), "planner": planner, "delegation": delegation,
        "executor_input": executor_input, "executor": run.to_dict(), "finished": router.finished,
        "events": router.events, "proposals": router.proposals,
        "executed_state_changes": [e for e in router.events if e.get("effect") == STATE_CHANGE and e.get("executed")],
        "blocked": [e for e in router.events if e.get("verified") and not e.get("executed")],
        "state_before": state_before, "state_after": state_after, "audit": audit, "environment_events": fired,
        "services_changed": changed_services(state_before, state_after),
        "unexplained_state_changes": unexplained_changes(state_before, state_after, router.events),
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "episode.json").write_text(json.dumps(episode, indent=2, ensure_ascii=False, default=str),
                                              encoding="utf-8")
        with open(out_dir / "proposals.jsonl", "w", encoding="utf-8") as f:
            for p in router.proposals:
                f.write(json.dumps(p, ensure_ascii=False, default=str) + "\n")
    return episode
