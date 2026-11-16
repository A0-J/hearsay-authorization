"""The verification methods for AuthorizationBench calls.

  none                   run every call (the executor's own judgement is the only check)
  llm_claim_only         an LLM verifier: the task message (with any inherited claim), the call, and the
                         runtime's policy (pi); not the approval state
  llm_with_evidence      evidence-aware: the same, plus the approval state (sigma)
  llm_evidence_explicit  evidence-explicit: the same as evidence-aware, and told that the records are the
                         authority and a claim in the task message is not evidence
  provenance_gate        the record's own semantics (ApprovalRegistry.check on pi + sigma); the claim is
                         never read. It implements the labels' definition of authorization, so it is the
                         reference, not a finding
  dualflow               semantic flow AND provenance_gate. The semantic flow is an LLM that sees the
                         principal's own request (from the runtime) and the call with its content, never
                         the planner's message or the record, and judges intent alignment

One method is enforced: its decision alone determines whether the call runs. The
other methods judge the same call in shadow, so every method is compared on
identical proposals. Each proposal is saved with everything a verifier saw, so it
can be re-judged offline (experiments/replay_verifiers.py). `cache` lets a caller
reuse the decision for an LLM input it has already judged (the verifier-only
experiment: a claim-only verifier's input is the same under every approval state).

The record's verdict is stored with every proposal as the authorization label; intent
labels come from the dataset's ground truth and are never merged with it.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from ..guards import majority_vote
from ..llm import sampling_for
from .approvals import ApprovalRegistry
from .calls import ToolCall
from .prompts import SEMANTIC_INSTRUCTIONS, VERIFIER_INSTRUCTIONS, semantic_input, verifier_input

METHODS = ("none", "llm_claim_only", "llm_with_evidence", "llm_evidence_explicit", "provenance_gate", "dualflow")
LLM_KIND = {"llm_claim_only": "claim_only", "llm_with_evidence": "with_evidence",
            "llm_evidence_explicit": "evidence_explicit"}
NEEDS_CLIENT = frozenset(LLM_KIND) | {"dualflow"}


def input_sha256(instructions: str, text: str) -> str:
    return hashlib.sha256(f"{instructions}\n\x00\n{text}".encode()).hexdigest()


def _vote(client: Any, model: str, instructions: str, text: str, n_votes: int,
          cache: dict[tuple, dict[str, Any]] | None) -> dict[str, Any]:
    key = (model, n_votes, input_sha256(instructions, text))
    if cache is not None and key in cache:
        return {**cache[key], "reused": True}
    out = {**majority_vote(client, model, instructions, text, n_votes), "input_sha256": key[2], "reused": False}
    if cache is not None:
        cache[key] = out
    return out


def judge(method: str, call: ToolCall, delegation: str, registry: ApprovalRegistry, *, client: Any, model: str,
          n_votes: int, request: str | None = None, cache: dict | None = None) -> dict[str, Any]:
    if method == "none":
        return {"method": method, "allow": True}
    if method == "provenance_gate":
        v = registry.check(call)
        return {"method": method, "allow": v.allowed, "reason": v.reason, "approval_id": v.approval_id}
    if method in LLM_KIND:
        kind = LLM_KIND[method]
        out = _vote(client, model, VERIFIER_INSTRUCTIONS[kind], verifier_input(call, delegation, registry, kind),
                    n_votes, cache)
        return {"method": method, "allow": out["approve"], "model": model, "sampling": sampling_for(model), **out}
    if method == "dualflow":
        if request is None:
            raise ValueError("dualflow needs the principal's request")
        semantic = _vote(client, model, SEMANTIC_INSTRUCTIONS, semantic_input(call, request), n_votes, cache)
        gate = registry.check(call)
        return {"method": method, "allow": semantic["approve"] and gate.allowed, "model": model,
                "sampling": sampling_for(model), "semantic": semantic, "provenance": gate.to_dict()}
    raise ValueError(f"unknown verification method {method!r}")


@dataclass
class Verification:
    enforce: str
    shadow: tuple[str, ...]
    registry: ApprovalRegistry
    client: Any
    model: str
    n_votes: int = 3
    request: str | None = None          # the principal's own request, held by the runtime (dualflow)
    cache: dict | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        for m in (self.enforce, *self.shadow):
            if m not in METHODS:
                raise ValueError(f"unknown verification method {m!r}; choose from {METHODS}")
        if any(m in NEEDS_CLIENT for m in self.methods) and self.client is None:
            raise ValueError("LLM verification methods need a client")
        if "dualflow" in self.methods and self.request is None:
            raise ValueError("dualflow needs the principal's request")

    @property
    def methods(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((self.enforce, *self.shadow)))

    def __call__(self, call: ToolCall, delegation: str) -> dict[str, Any]:
        decisions = {m: judge(m, call, delegation, self.registry, client=self.client, model=self.model,
                              n_votes=self.n_votes, request=self.request, cache=self.cache) for m in self.methods}
        return {"enforce": self.enforce, "allowed": decisions[self.enforce]["allow"], "decisions": decisions,
                "record_verdict": self.registry.check(call).to_dict()}
