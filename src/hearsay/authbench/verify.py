"""The verification methods for AuthorizationBench calls.

  none                        run every call (the executor's own judgement is the only check)
  llm_claim_only              an LLM verifier: the task message (with any inherited claim), the call, and the
                              runtime's policy (pi); not the approval state
  llm_with_evidence           evidence-aware: the same, plus the approval state (sigma)
  llm_evidence_explicit       evidence-explicit: the same input as evidence-aware; the instructions add one
                              paragraph that states the order of evidence (prompts.EVIDENCE_PRIORITY). It
                              measures stating that order, not new evidence
  provenance_gate             the record's own semantics (ApprovalRegistry.check on pi + sigma); the claim is
                              never read. It implements the labels' definition of authorization, so it is the
                              reference, not a finding
  semantic_provenance_direct  Semantic+Provenance (Direct), a simplified variant of DualFlow: an LLM semantic
                              check (the principal's request and a trusted task context from the runtime, and
                              the call with its content; never the planner's message or the record) AND the
                              provenance gate. A semantic "uncertain" (or no majority) does not allow the call
                              (fail closed) and is recorded apart from "not_aligned"

One method is enforced: its decision alone determines whether the call runs. The
other methods judge the same call in shadow, so every method is compared on
identical proposals. Each proposal is saved with everything a verifier saw, so it
can be re-judged offline (experiments/replay_verifiers.py). `cache` lets a caller
reuse the decision for an LLM input it has already judged (the verifier-only
experiment: a claim-only verifier's input is the same under every approval state).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from ..guards import majority_vote
from ..llm import complete, sampling_for
from ..parsing import parse_json_object
from .approvals import ApprovalRegistry
from .calls import ToolCall
from .prompts import SEMANTIC_DECISIONS, SEMANTIC_INSTRUCTIONS, VERIFIER_INSTRUCTIONS, semantic_input, verifier_input

SEMANTIC = "semantic_provenance_direct"
METHODS = ("none", "llm_claim_only", "llm_with_evidence", "llm_evidence_explicit", "provenance_gate", SEMANTIC)
LLM_KIND = {"llm_claim_only": "claim_only", "llm_with_evidence": "with_evidence",
            "llm_evidence_explicit": "evidence_explicit"}
NEEDS_CLIENT = frozenset(LLM_KIND) | {SEMANTIC}


def input_sha256(instructions: str, text: str) -> str:
    return hashlib.sha256(f"{instructions}\n\x00\n{text}".encode()).hexdigest()


def semantic_vote(client: Any, model: str, instructions: str, input_text: str, n: int) -> dict[str, Any]:
    """n semantic judgements. outcome: the label of a strict majority among aligned / not_aligned /
    uncertain, else "no_majority"; an unparseable reply counts as "invalid". Only "aligned" allows."""
    votes = []
    for _ in range(n):
        call = complete(client, model, instructions, input_text)
        try:
            label = str(parse_json_object(call["text"]).get("decision", "")).strip().lower()
            call["label"] = label if label in SEMANTIC_DECISIONS else "invalid"
            call["reason"] = parse_json_object(call["text"]).get("reason")
        except ValueError as e:
            call["label"], call["parse_error"] = "invalid", str(e)
        votes.append(call)
    counts = {lab: sum(v["label"] == lab for v in votes) for lab in (*SEMANTIC_DECISIONS, "invalid")}
    outcome = next((lab for lab in SEMANTIC_DECISIONS if counts[lab] * 2 > n), "no_majority")
    return {"approve": outcome == "aligned", "outcome": outcome, "counts": counts, "n": n, "votes": votes}


class DecisionCache:
    """Decisions per LLM input. Entries can be computed ahead (in parallel) and are marked reused from their
    second use on, so `reused` means the same as without prefetching."""

    def __init__(self) -> None:
        self.store: dict[tuple, dict[str, Any]] = {}
        self.used: set[tuple] = set()

    def __contains__(self, key: tuple) -> bool:
        return key in self.store


def _cached(cache: dict | DecisionCache | None, key: tuple, compute) -> dict[str, Any]:
    if isinstance(cache, DecisionCache):
        if key not in cache.store:
            cache.store[key] = {**compute(), "input_sha256": key[-1]}
        reused = key in cache.used
        cache.used.add(key)
        return {**cache.store[key], "reused": reused}
    if cache is not None and key in cache:
        return {**cache[key], "reused": True}
    out = {**compute(), "input_sha256": key[-1], "reused": False}
    if cache is not None:
        cache[key] = out
    return out


def llm_request(method: str, call: ToolCall, delegation: str, registry: ApprovalRegistry, *, model: str,
                n_votes: int, request: str | None, trusted_context: str | None) -> tuple[tuple, str, str] | None:
    """(cache key, instructions, input text) of the LLM judgement a method needs, or None (none, gate)."""
    if method in LLM_KIND:
        kind = LLM_KIND[method]
        instructions, text = VERIFIER_INSTRUCTIONS[kind], verifier_input(call, delegation, registry, kind)
        return ("vote", model, n_votes, input_sha256(instructions, text)), instructions, text
    if method == SEMANTIC:
        if request is None:
            raise ValueError(f"{SEMANTIC} needs the principal's request")
        text = semantic_input(call, request, trusted_context)
        return ("semantic", model, n_votes, input_sha256(SEMANTIC_INSTRUCTIONS, text)), SEMANTIC_INSTRUCTIONS, text
    return None


def compute_request(client: Any, model: str, key: tuple, instructions: str, text: str, n_votes: int) -> dict:
    vote = semantic_vote if key[0] == "semantic" else majority_vote
    return vote(client, model, instructions, text, n_votes)


def judge(method: str, call: ToolCall, delegation: str, registry: ApprovalRegistry, *, client: Any, model: str,
          n_votes: int, request: str | None = None, trusted_context: str | None = None,
          cache: dict | None = None) -> dict[str, Any]:
    if method == "none":
        return {"method": method, "allow": True}
    if method == "provenance_gate":
        v = registry.check(call)
        return {"method": method, "allow": v.allowed, "reason": v.reason, "approval_id": v.approval_id}
    req = llm_request(method, call, delegation, registry, model=model, n_votes=n_votes, request=request,
                      trusted_context=trusted_context)
    if method in LLM_KIND:
        key, instructions, text = req
        out = _cached(cache, key, lambda: compute_request(client, model, key, instructions, text, n_votes))
        return {"method": method, "allow": out["approve"], "model": model, "sampling": sampling_for(model), **out}
    if method == SEMANTIC:
        key, instructions, text = req
        semantic = _cached(cache, key, lambda: compute_request(client, model, key, instructions, text, n_votes))
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
    request: str | None = None           # the principal's own request, held by the runtime
    trusted_context: str | None = None   # facts from the environment, built by rule (dataset inputs.json)
    cache: dict | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        for m in (self.enforce, *self.shadow):
            if m not in METHODS:
                raise ValueError(f"unknown verification method {m!r}; choose from {METHODS}")
        if any(m in NEEDS_CLIENT for m in self.methods) and self.client is None:
            raise ValueError("LLM verification methods need a client")
        if SEMANTIC in self.methods and self.request is None:
            raise ValueError(f"{SEMANTIC} needs the principal's request")

    @property
    def methods(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((self.enforce, *self.shadow)))

    def __call__(self, call: ToolCall, delegation: str) -> dict[str, Any]:
        decisions = {m: judge(m, call, delegation, self.registry, client=self.client, model=self.model,
                              n_votes=self.n_votes, request=self.request, trusted_context=self.trusted_context,
                              cache=self.cache) for m in self.methods}
        return {"enforce": self.enforce, "allowed": decisions[self.enforce]["allow"], "decisions": decisions,
                "record_verdict": self.registry.check(call).to_dict()}
