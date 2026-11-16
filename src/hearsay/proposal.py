"""The (action, resource, scope) form of every tool call, and the executor's refusal."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Proposal:
    action: str
    resource: str
    scope: str

    def canonical(self) -> "Proposal":
        return Proposal(self.action.strip().lower(), self.resource.strip(), self.scope.strip().lower())

    def key(self) -> str:
        c = self.canonical()
        return f"{c.action}|{c.resource}|{c.scope}"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Proposal":
        return cls(str(d.get("action", "")), str(d.get("resource", "")), str(d.get("scope", "")))

    def __str__(self) -> str:
        return "refuse" if self == REFUSE else f"{self.action}({self.resource}, {self.scope})"


REFUSE = Proposal("__refuse__", "", "")   # the executor declined to carry out the delegated task


def modal(proposals: list[Proposal]) -> Proposal | None:
    """Most frequent canonical proposal; ties go to the earliest."""
    if not proposals:
        return None
    counts = Counter(p.canonical() for p in proposals)
    top = max(counts.values())
    return next(p.canonical() for p in proposals if counts[p.canonical()] == top)
