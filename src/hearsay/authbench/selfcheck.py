"""Check the routed call path against a live AuthorizationBench environment, without any LLM call.

    PYTHONUTF8=1 python -m hearsay.authbench.selfcheck --task T0010-l-b-h

Uses the same ToolRouter as an episode, with the provenance gate enforced, and
counts every request the router hands to the HTTP transport:
  1. a read call runs without a proposal
  2. a state-changing call with no approval is blocked: no request, service audit and /state unchanged
  3. the same call with a revoked approval is blocked the same way
  4. the same call with a valid approval runs: one request, and the service audit records it
Prints a JSON report; exit code 0 iff every check passed.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .approvals import ApprovalRegistry
from .calls import READ, STATE_CHANGE, effect, service
from .runtime import Environment, ToolRouter, default_transport
from .task import load_task
from .verify import Verification

ROLE = "selfcheck_approver"


def sample_arguments(schema: dict[str, Any]) -> dict[str, Any]:
    """Placeholder values for the required arguments of a tool schema."""
    out: dict[str, Any] = {}
    for name in schema.get("required", []):
        spec = schema.get("properties", {}).get(name, {})
        t = spec.get("type") or next((s.get("type") for s in spec.get("anyOf", []) if s.get("type") != "null"), "string")
        if spec.get("enum"):
            out[name] = spec["enum"][0]
        elif t == "array":
            item = (spec.get("items") or {}).get("type", "string")
            out[name] = ["selfcheck@example.com"] if item == "string" else []
        elif t in ("integer", "number"):
            out[name] = 1
        elif t == "boolean":
            out[name] = False
        elif t == "object":
            out[name] = {}
        else:
            out[name] = "selfcheck@example.com" if "email" in name or name in ("to", "recipient") else "selfcheck"
    return out


def audit_count(audit: dict, svc: str) -> int:
    entries = audit.get(svc, [])
    if isinstance(entries, dict):
        entries = entries.get("actions", [])
    return len(entries)


def registry_for(tool: str, today: str, *, revoked: bool) -> ApprovalRegistry:
    return ApprovalRegistry.from_dict({
        "today": today, "roles": {ROLE: "Self-check approver"}, "authority": {ROLE: [tool]},
        "approvals": [{"approval_id": "SELFCHECK-1", "issuer": ROLE, "tool": tool, "revoked": revoked,
                       "note": "self-check"}]})


def run(task_id: str, tool: str | None, args: dict[str, Any] | None) -> dict[str, Any]:
    task = load_task(task_id)
    sent: list[str] = []
    real = default_transport()

    def transport(base_url: str, entry: dict, arguments: dict, **kw: Any) -> dict:
        sent.append(entry["name"])
        return real(base_url, entry, arguments, **kw)

    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, **detail: Any) -> None:
        checks.append({"check": name, "passed": bool(passed), **detail})

    with Environment(task) as env:
        def router(registry: ApprovalRegistry) -> ToolRouter:
            v = Verification(enforce="provenance_gate", shadow=("none",), registry=registry, client=None, model="-")
            return ToolRouter(env, task, v, registry, delegation=task.instruction, transport=transport)

        probe = router(ApprovalRegistry.empty(task.today))
        writes = [t for t in probe.surface if effect(t["name"]) == STATE_CHANGE]
        reads = [t for t in probe.surface if effect(t["name"]) == READ]
        target = next((t for t in writes if t["name"] == tool), None) if tool else (writes[0] if writes else None)
        if target is None:
            raise SystemExit(f"{task.task_id}: no state-changing tool {tool or ''} in {list(task.allowlist)}")
        name, svc = target["name"], service(target["name"])
        call_args = args if args is not None else sample_arguments(target["parameters"])

        if reads:
            r = reads[0]
            n0 = len(sent)
            probe.call(r["name"], sample_arguments(r["parameters"]))
            check("read call runs without a proposal", len(sent) == n0 + 1 and not probe.proposals,
                  tool=r["name"], status=probe.events[-1].get("status"))

        for label, registry in (("no approval", ApprovalRegistry.empty(task.today)),
                                ("revoked approval", registry_for(name, task.today, revoked=True))):
            rt = router(registry)
            state0, audit0, n0 = env.state(), env.audit(), len(sent)
            result = rt.call(name, call_args)
            state1, audit1 = env.state(), env.audit()
            check(f"state-changing call with {label} is blocked before any request",
                  result.get("status") == "blocked" and len(sent) == n0
                  and audit_count(audit1, svc) == audit_count(audit0, svc)
                  and json.dumps(state1.get(svc), sort_keys=True) == json.dumps(state0.get(svc), sort_keys=True),
                  tool=name, gate_reason=rt.proposals[-1]["decisions"]["provenance_gate"]["reason"],
                  requests_sent=len(sent) - n0)

        rt = router(registry_for(name, task.today, revoked=False))
        state0, audit0, n0 = env.state(), env.audit(), len(sent)
        result = rt.call(name, call_args)
        state1, audit1 = env.state(), env.audit()
        status = result.get("status")
        ok_status = isinstance(status, int) and 200 <= status < 300
        changed = json.dumps(state1.get(svc), sort_keys=True) != json.dumps(state0.get(svc), sort_keys=True)
        check("state-changing call with a valid approval reaches the service",
              len(sent) == n0 + 1 and rt.events[-1].get("executed") is True
              and audit_count(audit1, svc) > audit_count(audit0, svc),
              tool=name, arguments=call_args, http_status=status,
              audit_entries_added=audit_count(audit1, svc) - audit_count(audit0, svc))
        if ok_status:
            check("a successful state-changing call changes the service state", changed, tool=name)

    return {"task_id": task.task_id, "passed": all(c["passed"] for c in checks), "checks": checks}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", default="T0010-l-b-h")
    ap.add_argument("--tool", help="canonical state-changing tool to probe (default: the first in the allowlist)")
    ap.add_argument("--args", help="JSON arguments for that tool (default: placeholders for required fields)")
    a = ap.parse_args(argv)
    report = run(a.task, a.tool, json.loads(a.args) if a.args else None)
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
