"""The executor's tools as mock services. Every state-changing call passes the guard before it runs.

Each catalog action becomes a function tool taking a resource and (for
state-changing actions) a scope. Read-only actions return the resource's
facts. A state-changing call is executed only if the guard allows it; the
executor then sees either a confirmation or a generic "blocked" result.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from .proposal import Proposal
from .scenarios import Scenario


@dataclass(frozen=True)
class GuardDecision:
    allowed: bool
    detail: dict[str, Any] = field(default_factory=dict)   # what the verification method saw and said


Guard = Callable[[Proposal, str], GuardDecision]


@dataclass
class ToolEvent:
    tool: str
    proposal: dict[str, str]
    guarded: bool
    executed: bool
    delegation_index: int
    guard: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


BLOCKED = {"status": "blocked", "message": "The authorization check did not approve this call; it was not run."}


class Sandbox:
    def __init__(self, scenario: Scenario, guard: Guard, *, record_lookup: bool = False) -> None:
        self.s = scenario
        self.guard = guard
        self.record_lookup = record_lookup
        self.delegation = ""            # the message the executor is currently working from
        self.delegation_index = -1
        self.events: list[ToolEvent] = []

    def tools(self) -> list[dict[str, Any]]:
        out = []
        for action, description in self.s.catalog.items():
            props: dict[str, Any] = {"resource": {"type": "string", "enum": list(self.s.resources)}}
            if action not in self.s.store.open_actions:
                props["scope"] = {"type": "string", "enum": list(self.s.scopes)}
            out.append({"type": "function", "name": action, "description": description, "strict": True,
                        "parameters": {"type": "object", "properties": props, "required": list(props),
                                       "additionalProperties": False}})
        if self.record_lookup:
            out.append({"type": "function", "name": "lookup_approval", "strict": True,
                        "description": "Look up an approval in the organization's approval system by its id.",
                        "parameters": {"type": "object", "properties": {"approval_id": {"type": "string"}},
                                       "required": ["approval_id"], "additionalProperties": False}})
        return out

    def handle(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name == "lookup_approval" and self.record_lookup:
            g = self.s.store.grant(str(args.get("approval_id", "")).strip())
            if g is None:
                return {"status": "not_found"}
            return {"status": "found", "record": g.to_dict(), "issuer_title": self.s.store.roles.get(g.issuer)}
        if name not in self.s.catalog:
            return {"error": f"unknown tool {name}"}
        p = Proposal(name, str(args.get("resource", "")), str(args.get("scope", ""))).canonical()
        if name in self.s.store.open_actions:
            self.events.append(ToolEvent(name, p.to_dict(), guarded=False, executed=True,
                                         delegation_index=self.delegation_index))
            facts = self.s.facts.get(p.resource)
            return {"status": "ok", "resource": p.resource, "details": dict(facts)} if facts else {"status": "not_found"}
        decision = self.guard(p, self.delegation)
        self.events.append(ToolEvent(name, p.to_dict(), guarded=True, executed=decision.allowed,
                                     delegation_index=self.delegation_index, guard=decision.detail))
        if not decision.allowed:
            return BLOCKED
        return {"status": "done", "action": p.action, "resource": p.resource, "scope": p.scope}

    def guarded_events(self) -> list[ToolEvent]:
        return [e for e in self.events if e.guarded]
