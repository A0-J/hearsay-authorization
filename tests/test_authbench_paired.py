"""The paired dataset: only the record changes, and its verdicts are the labels the design says (0 API calls)."""

import json
from pathlib import Path

import pytest

from hearsay.authbench.calls import ToolCall
from hearsay.authbench.paired import BY_ID, CONDITIONS, EXCLUDED, SHOULD_EXECUTE, SPECS

DATA = Path(__file__).resolve().parents[1] / "data" / "authbench_paired"


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.task_id)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_record_verdict_on_the_intended_call(spec, condition):
    v = spec.registry(condition).check(spec.reference)
    assert v.reason == spec.expected_reason(condition)
    assert v.allowed is SHOULD_EXECUTE[condition]


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.task_id)
def test_only_the_varied_approval_changes(spec):
    records = {c: spec.record(c) for c in CONDITIONS}
    for c, r in records.items():
        assert {k: v for k, v in r.items() if k != "approvals"} == \
               {k: v for k, v in records["valid"].items() if k != "approvals"}
        assert r["approvals"][0] == spec.background                     # the unrelated approval, always first
        assert len(r["approvals"]) == (1 if c == "nonexistent" else 2)
        assert spec.background["tool"] != spec.gated_tool              # it never covers the gated call
    valid = records["valid"]["approvals"][1]
    changed = {c: {k for k in valid if r["approvals"][1][k] != valid[k]}
               for c, r in records.items() if c not in ("valid", "nonexistent")}
    assert changed == {"expired": {"valid_from", "valid_until"}, "revoked": {"revoked"},
                       "scope_exceeded": {"constraints", "note"}, "misquoted_other_valid": {"approval_id"}}


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.task_id)
def test_claim_cites_the_valid_approval_and_misquoted_record_lacks_it(spec):
    assert spec.claim_id in spec.claim and spec.other_id not in spec.claim
    misquoted = spec.registry("misquoted_other_valid")
    assert misquoted.lookup(spec.claim_id)["status"] == "not_found"
    assert misquoted.check(spec.reference).approval_id == spec.other_id


def test_record_does_not_decide_intent():
    # The meeting summaries with the private conversation go to the approved list: the record authorizes them
    # (it cannot see content), and they remain the benchmark's original violation.
    for spec in SPECS:
        if spec.gated_tool == "email_client.send_message":
            assert all(spec.registry("valid").check(o.call).allowed for o in spec.off_intent)
    # Paying roommates' charges is outside the mandate as well.
    t0007 = BY_ID["T0007-a-g-h"]
    assert {t0007.registry("valid").check(o.call).reason for o in t0007.off_intent} == {"out_of_scope"}


def test_payment_without_resolved_context_fails_closed():
    t0007 = BY_ID["T0007-a-g-h"]
    assert not t0007.registry("valid").check(ToolCall("tenant_portal.pay_selected", {})).allowed


def test_selected_and_excluded_do_not_overlap():
    assert not {s.task_id for s in SPECS} & {e.task_id for e in EXCLUDED}
    assert len({s.task_id for s in SPECS}) == len(SPECS)


@pytest.mark.skipif(not DATA.is_dir(), reason="dataset not generated")
@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.task_id)
def test_committed_files_match_the_specs(spec):
    for c in CONDITIONS:
        assert json.loads((DATA / spec.task_id / "records" / f"{c}.json").read_text(encoding="utf-8")) == spec.record(c)
    assert (DATA / spec.task_id / "handoff_note.txt").read_text(encoding="utf-8").strip() == spec.claim
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    entry = next(t for t in manifest["tasks"] if t["task_id"] == spec.task_id)
    assert [c["intended_call_verdict"]["reason"] for c in entry["conditions"]] == \
           [spec.expected_reason(c) for c in CONDITIONS]
