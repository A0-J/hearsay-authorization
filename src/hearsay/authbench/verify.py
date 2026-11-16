"""The verification methods for AuthorizationBench calls.

  none               run every call (the executor's own judgement is the only check)
  llm_claim_only     an LLM verifier sees the task message (with any inherited claim) and the call
  llm_with_evidence  the same, plus the independent approval record
  provenance_gate    the record's own semantics (ApprovalRegistry.check); the claim is never read

One method is enforced: its decision alone determines whether the call runs. The
other methods judge the same call in shadow, so every method is compared on
identical proposals and verifier differences are not mixed with differences in
what the executor proposed. Each proposal is saved with everything a verifier
saw, so it can also be re-judged offline (experiments/replay_verifiers.py).

The record's verdict is stored with every proposal as the authorization label.
Whether the call is what the principal asked for (intent alignment) is a separate
label, added with the paired conditions; the two are never merged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..guards import majority_vote
from ..llm import sampling_for
from .approvals import ApprovalRegistry
from .calls import ToolCall
from .prompts import VERIFIER_INSTRUCTIONS, verifier_input

METHODS = ("none", "llm_claim_only", "llm_with_evidence", "provenance_gate")
LLM_KIND = {"llm_claim_only": "claim_only", "llm_with_evidence": "with_evidence"}


def judge(method: str, call: ToolCall, delegation: str, registry: ApprovalRegistry, *, client: Any, model: str,
          n_votes: int) -> dict[str, Any]:
    if method == "none":
        return {"method": method, "allow": True}
    if method == "provenance_gate":
        v = registry.check(call)
        return {"method": method, "allow": v.allowed, "reason": v.reason, "approval_id": v.approval_id}
    if method in LLM_KIND:
        kind = LLM_KIND[method]
        out = majority_vote(client, model, VERIFIER_INSTRUCTIONS[kind],
                            verifier_input(call, delegation, registry, kind), n_votes)
        return {"method": method, "allow": out["approve"], "model": model, "sampling": sampling_for(model), **out}
    raise ValueError(f"unknown verification method {method!r}")


@dataclass
class Verification:
    enforce: str
    shadow: tuple[str, ...]
    registry: ApprovalRegistry
    client: Any
    model: str
    n_votes: int = 3

    def __post_init__(self) -> None:
        for m in (self.enforce, *self.shadow):
            if m not in METHODS:
                raise ValueError(f"unknown verification method {m!r}; choose from {METHODS}")
        if any(m in LLM_KIND for m in (self.enforce, *self.shadow)) and self.client is None:
            raise ValueError("LLM verification methods need a client")

    @property
    def methods(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((self.enforce, *self.shadow)))

    def __call__(self, call: ToolCall, delegation: str) -> dict[str, Any]:
        decisions = {m: judge(m, call, delegation, self.registry, client=self.client, model=self.model,
                              n_votes=self.n_votes) for m in self.methods}
        return {"enforce": self.enforce, "allowed": decisions[self.enforce]["allow"], "decisions": decisions,
                "record_verdict": self.registry.check(call).to_dict()}
