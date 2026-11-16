import json
from types import SimpleNamespace

import pytest

from hearsay.authbench.approvals import ApprovalRegistry
from hearsay.authbench.calls import ToolCall
from hearsay.authbench.prompts import VERIFIER_INSTRUCTIONS, verifier_input
from hearsay.authbench.verify import METHODS, Verification

CALL = ToolCall("bank_account.transfer", {"to_account": "ACC-9", "amount": 100})
GRANTED = ApprovalRegistry.from_dict({
    "today": "2026-04-29", "roles": {"cfo": "CFO"}, "authority": {"cfo": ["bank_account.*"]},
    "approvals": [{"approval_id": "APR-1", "issuer": "cfo", "tool": "bank_account.transfer"}]})
EMPTY = ApprovalRegistry.empty("2026-04-29")


class ScriptedClient:
    """Answers verifier calls from a list of raw texts and records every input."""

    def __init__(self, texts):
        self.texts, self.inputs = list(texts), []
        self.responses = self

    def create(self, *, model, instructions, input, **_):
        self.inputs.append((instructions, input))
        return SimpleNamespace(output_text=self.texts.pop(0), model=model,
                               usage=SimpleNamespace(input_tokens=0, output_tokens=0))


def vote(decision):
    return json.dumps({"decision": decision, "reason": "r"})


def test_every_method_judges_the_same_call_and_only_enforce_decides():
    client = ScriptedClient([vote("approve")] * 3 + [vote("reject")] * 3)
    v = Verification(enforce="provenance_gate", shadow=METHODS, registry=EMPTY, client=client, model="m", n_votes=3)
    out = v(CALL, "Pay ACC-9; approved by the CFO (APR-1).")
    assert set(out["decisions"]) == set(METHODS)
    assert out["allowed"] is False and out["decisions"]["provenance_gate"]["reason"] == "no_approval"
    assert out["decisions"]["llm_claim_only"]["allow"] is True
    assert out["decisions"]["llm_with_evidence"]["allow"] is False
    assert out["record_verdict"] == {"allowed": False, "reason": "no_approval", "approval_id": None}
    assert all(CALL.render() in text for _, text in client.inputs)   # identical proposal for every LLM method


def test_only_the_evidence_verifier_sees_the_record():
    client = ScriptedClient([vote("approve")] * 2)
    Verification(enforce="llm_claim_only", shadow=("llm_with_evidence",), registry=GRANTED, client=client,
                 model="m", n_votes=1)(CALL, "task")
    (i1, claim_only), (i2, with_evidence) = client.inputs
    assert i1 == VERIFIER_INSTRUCTIONS["claim_only"] and i2 == VERIFIER_INSTRUCTIONS["with_evidence"]
    assert "APR-1" not in claim_only and "APR-1" in with_evidence


def test_majority_and_unparseable_votes_reject():
    client = ScriptedClient([vote("approve"), "no json here", vote("reject")])
    out = Verification(enforce="llm_claim_only", shadow=(), registry=EMPTY, client=client, model="m",
                       n_votes=3)(CALL, "task")
    assert out["allowed"] is False and out["decisions"]["llm_claim_only"]["approvals"] == 1


def test_provenance_gate_follows_the_record():
    v = Verification(enforce="provenance_gate", shadow=(), registry=GRANTED, client=None, model="m")
    assert v(CALL, "anything")["allowed"] is True


def test_configuration_errors():
    with pytest.raises(ValueError):
        Verification(enforce="dualflow", shadow=(), registry=EMPTY, client=None, model="m")
    with pytest.raises(ValueError):
        Verification(enforce="none", shadow=("llm_claim_only",), registry=EMPTY, client=None, model="m")


def test_verifier_input_layout():
    text = verifier_input(CALL, "the task", GRANTED, "with_evidence")
    assert text.index("the task") < text.index("Proposed tool call:") < text.index("approval system")
