"""One AuthorizationBench task bundle, as the runtime needs it.

The agent-facing parts come from the benchmark unchanged: the principal's
instruction (resolved and identity-substituted by the benchmark's own helpers),
the sealed task prompt (system_prompt.txt), and the tool allowlist derived from the
bundle's assembly blueprint, which is how the paper's harnesses build the agent's
tool surface. The authorization contract (completion criteria, violated actions)
is loaded for evaluation only and never reaches an agent.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .locate import ensure_importable, tasks_dir


@dataclass(frozen=True)
class AuthBenchTask:
    task_id: str
    bundle: Path
    instruction: str
    system_prompt: str
    allowlist: tuple[str, ...]          # canonical business tool names; message_user last
    shell_tools: tuple[str, ...]        # read_file / write_file / terminal the blueprint mounts
    reference_time: str
    domain: str
    trigger: Any
    harm: str
    contract: dict[str, Any] = field(default_factory=dict)   # evaluation only

    @property
    def today(self) -> str:
        return self.reference_time[:10]

    @property
    def needs_workspace(self) -> bool:
        return bool(self.shell_tools)

    def summary(self) -> dict[str, Any]:
        return {"task_id": self.task_id, "domain": self.domain, "trigger": self.trigger, "harm": self.harm,
                "reference_time": self.reference_time, "allowlist": list(self.allowlist),
                "shell_tools": list(self.shell_tools)}


def resolve_bundle(task: str | Path) -> Path:
    p = Path(task)
    if not p.is_dir():
        p = tasks_dir() / str(task)
    if not (p / "task_config.json").is_file():
        raise FileNotFoundError(f"no AuthorizationBench task bundle at {p}")
    return p.resolve()


def load_task(task: str | Path) -> AuthBenchTask:
    ensure_importable()
    from authorization_eva_sandbox.evaluation.harness.tool_ir import allowlist_from_actions, shell_tool_names
    from authorization_eva_sandbox.evaluation.task_bundle import (_substitute_placeholders, load_task_config,
                                                                  resolve_instruction, resolve_user_identity,
                                                                  resolve_vignette_refs)

    bundle = resolve_bundle(task)
    config = load_task_config(str(bundle))
    resolve_vignette_refs(config, str(bundle))
    identity = resolve_user_identity(config, str(bundle))
    instruction = _substitute_placeholders(resolve_instruction(config, str(bundle)), identity)
    system_prompt = _substitute_placeholders((bundle / "system_prompt.txt").read_text(encoding="utf-8"), identity)
    vignette = json.loads((bundle / "vignette.json").read_text(encoding="utf-8"))
    actions = [step["action"] for step in vignette["assembly_blueprint"]["actions"]]
    names, _files = allowlist_from_actions(actions)
    return AuthBenchTask(
        task_id=str(config.get("task_id") or bundle.name), bundle=bundle, instruction=instruction,
        system_prompt=system_prompt, allowlist=tuple(names), shell_tools=tuple(shell_tool_names(actions)),
        reference_time=str(config.get("reference_time") or ""), domain=str(vignette.get("domain", "")),
        trigger=config.get("situational_trigger"), harm=str(config.get("harm", "")),
        contract={"completion_criteria": config.get("completion_criteria"),
                  "authorization_scope": config.get("authorization_scope")})
