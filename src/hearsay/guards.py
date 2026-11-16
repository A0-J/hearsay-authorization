"""The verification methods, each as a guard in front of the executor's state-changing tools.

  none               run every call (the executor's own judgement is the only check)
  llm_claim_only     an LLM verifier sees the delegation message (with any inherited claim) and the call
  llm_with_evidence  the same, plus the independent record of the approval system
  provenance_gate    deterministic check of the call against the record; the claim is never read
  dualflow           semantic check (call == the coordinator's restated intent) AND the provenance gate
"""

from __future__ import annotations

import threading
from typing import Any

from .llm import complete
from .parsing import parse_json_object
from .prompts import RESTATE_INSTRUCTIONS, VERIFIER_INSTRUCTIONS, restate_input, verifier_input
from .proposal import Proposal, modal
from .records import provenance_gate
from .sandbox import GuardDecision
from .scenarios import Scenario

METHODS = ("none", "llm_claim_only", "llm_with_evidence", "provenance_gate", "dualflow")


class IntentCache:
    """The coordinator's restated intent per base task (the semantic flow's reference), computed once per run.

    It depends only on the principal's request, not on the claim or the record, so all conditions and
    episodes of a base task share it."""

    def __init__(self, client_for, model: str, n: int) -> None:
        self.client_for, self.model, self.n = client_for, model, n
        self._lock = threading.Lock()
        self._intent: dict[str, dict[str, Any]] = {}

    def get(self, s: Scenario) -> dict[str, Any]:
        with self._lock:
            if s.base_id in self._intent:
                return self._intent[s.base_id]
            samples, proposals = [], []
            client = self.client_for(s)
            for _ in range(self.n):
                call = complete(client, self.model, RESTATE_INSTRUCTIONS, restate_input(s))
                try:
                    p = Proposal.from_dict(parse_json_object(call["text"])).canonical()
                    proposals.append(p)
                    call["proposal"] = p.to_dict()
                except (ValueError, TypeError) as e:
                    call["parse_error"] = str(e)
                samples.append(call)
            intent = modal(proposals)
            self._intent[s.base_id] = {"intent": intent.to_dict() if intent else None, "samples": samples}
            return self._intent[s.base_id]


def majority_vote(client: Any, model: str, instructions: str, input_text: str, n: int) -> dict[str, Any]:
    """n verifier calls; approve on a strict majority of parseable "approve" votes (a tie or a parse error
    rejects)."""
    votes = []
    for _ in range(n):
        call = complete(client, model, instructions, input_text)
        try:
            obj = parse_json_object(call["text"])
            call["approve"] = str(obj.get("decision", "")).strip().lower() == "approve"
            call["reason"] = obj.get("reason")
        except ValueError as e:
            call["approve"], call["parse_error"] = False, str(e)
        votes.append(call)
    approvals = sum(v["approve"] for v in votes)
    return {"approve": approvals * 2 > n, "approvals": approvals, "n": n, "votes": votes}


def llm_verify(client: Any, model: str, s: Scenario, p: Proposal, delegation: str, kind: str,
               n: int) -> dict[str, Any]:
    return majority_vote(client, model, VERIFIER_INSTRUCTIONS[kind], verifier_input(s, p, delegation, kind), n)


class Guard:
    def __init__(self, method: str, s: Scenario, *, client: Any, verifier_model: str, n_verify: int,
                 intents: IntentCache | None) -> None:
        if method not in METHODS:
            raise ValueError(method)
        if method == "dualflow" and intents is None:
            raise ValueError("dualflow needs an IntentCache")
        self.method, self.s, self.client = method, s, client
        self.verifier_model, self.n_verify, self.intents = verifier_model, n_verify, intents

    def __call__(self, p: Proposal, delegation: str) -> GuardDecision:
        m, s = self.method, self.s
        if m == "none":
            return GuardDecision(True, {"method": m})
        if m == "provenance_gate":
            v = provenance_gate(p, s.store)
            return GuardDecision(v.allowed, {"method": m, "reason": v.reason, "grant_id": v.grant_id})
        if m == "dualflow":
            v = provenance_gate(p, s.store)
            intent = self.intents.get(s)["intent"]
            semantic = intent is not None and Proposal.from_dict(intent).canonical() == p.canonical()
            return GuardDecision(semantic and v.allowed, {"method": m, "semantic": semantic, "intent": intent,
                                                         "reason": v.reason, "grant_id": v.grant_id})
        kind = "claim_only" if m == "llm_claim_only" else "with_evidence"
        out = llm_verify(self.client, self.verifier_model, s, p, delegation, kind, self.n_verify)
        return GuardDecision(out["approve"], {"method": m, **out})
