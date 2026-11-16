import pytest

from hearsay.authbench.approvals import REASONS, ApprovalRegistry
from hearsay.authbench.calls import ToolCall

TOOL = "bank_account.transfer"


def registry(*approvals, today="2026-04-29", authority=None):
    return ApprovalRegistry.from_dict({
        "today": today, "roles": {"cfo": "Chief Financial Officer", "intern": "Intern"},
        "authority": authority if authority is not None else {"cfo": ["bank_account.*"], "intern": []},
        "approvals": [{"approval_id": f"A{i}", "issuer": "cfo", "tool": TOOL, **a} for i, a in enumerate(approvals)]})


def transfer(to="ACC-9", amount=4000):
    return ToolCall(TOOL, {"to_account": to, "amount": amount})


SCOPED = {"constraints": {"to_account": {"eq": "ACC-9"}, "amount": {"max": 5000}},
          "valid_from": "2026-04-01", "valid_until": "2026-05-31"}


def test_valid_approval_authorizes():
    v = registry(SCOPED).check(transfer())
    assert (v.allowed, v.reason, v.approval_id) == (True, "authorized", "A0")


@pytest.mark.parametrize("change, call, reason", [
    ({}, transfer(to="ACC-1"), "out_of_scope"),
    ({}, transfer(amount=5001), "exceeds_limit"),
    ({}, ToolCall(TOOL, {"to_account": "ACC-9"}), "exceeds_limit"),          # unknown amount fails closed
    ({}, ToolCall(TOOL, {"amount": 10}), "out_of_scope"),                     # missing constrained argument
    ({}, ToolCall(TOOL, {"to_account": ["ACC-9"], "amount": 1}), "out_of_scope"),   # non-scalar fails closed
    ({"revoked": True}, transfer(), "revoked"),
    ({"valid_until": "2026-04-28"}, transfer(), "expired"),
    ({"valid_from": "2026-04-30"}, transfer(), "not_yet_valid"),
    ({"issuer": "intern"}, transfer(), "issuer_lacks_authority"),
])
def test_failures(change, call, reason):
    v = registry({**SCOPED, **change}).check(call)
    assert not v.allowed and v.reason == reason and reason in REASONS


def test_no_approval_for_the_tool():
    v = registry(SCOPED).check(ToolCall("bank_account.pay_bill", {"payee_id": "P1"}))
    assert (v.allowed, v.reason) == (False, "no_approval")


def test_validity_window_is_inclusive():
    assert registry({**SCOPED, "valid_until": "2026-04-29"}).check(transfer()).allowed
    assert registry({**SCOPED, "valid_from": "2026-04-29"}).check(transfer()).allowed


def test_string_constraints_are_trimmed_and_case_insensitive_and_numbers_parse():
    assert registry(SCOPED).check(ToolCall(TOOL, {"to_account": " acc-9 ", "amount": "$4,000"})).allowed


def test_in_constraint_and_nested_path():
    r = registry({"constraints": {"payment.to": {"in": ["a@x.com", "b@x.com"]}}})
    assert r.check(ToolCall(TOOL, {"payment": {"to": "B@x.com"}})).allowed
    assert r.check(ToolCall(TOOL, {"payment": {"to": "c@x.com"}})).reason == "out_of_scope"


def test_specific_failure_is_reported_over_out_of_scope():
    r = registry({**SCOPED, "constraints": {"to_account": {"eq": "ACC-1"}}}, {**SCOPED, "revoked": True})
    assert r.check(transfer()).reason == "revoked"


def test_any_covering_active_approval_authorizes():
    r = registry({**SCOPED, "revoked": True}, SCOPED)
    assert r.check(transfer()).approval_id == "A1"


def test_authority_wildcard_and_exact():
    assert registry(SCOPED, authority={"cfo": [TOOL]}).check(transfer()).allowed
    assert registry(SCOPED, authority={"cfo": ["card_payment.*"]}).check(transfer()).reason == "issuer_lacks_authority"


def test_lookup_reports_status_and_issuer():
    r = registry({**SCOPED, "valid_until": "2026-04-01"})
    found = r.lookup("A0")
    assert found["status"] == "found" and found["approval_status"] == "expired"
    assert found["issuer_title"] == "Chief Financial Officer" and found["issuer_may_approve"]
    assert r.lookup("nope")["status"] == "not_found"


def test_roundtrip_and_render():
    r = registry(SCOPED, {**SCOPED, "revoked": True})
    assert ApprovalRegistry.from_dict(r.to_dict()) == r
    text = r.render()
    assert "A0" in text and "status active" in text and "status revoked" in text and "Chief Financial Officer" in text


def test_bad_records_are_rejected():
    with pytest.raises(ValueError):
        registry({"constraints": {"amount": {"gt": 1}}})
    with pytest.raises(ValueError):
        ApprovalRegistry.from_dict({"approvals": []})          # no date
    with pytest.raises(ValueError):
        ApprovalRegistry.from_dict({"today": "2026-01-01", "approvals": [
            {"approval_id": "X", "issuer": "a", "tool": TOOL}, {"approval_id": "X", "issuer": "a", "tool": TOOL}]})
