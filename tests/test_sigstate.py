"""Signed-state experiment (SIG) cells: docs/SIGNED_STATE_PREREG_DRAFT.md."""
from __future__ import annotations

import json
from collections import Counter

import pytest

pytest.importorskip("cryptography")

from hearsay.authbench import exp1  # noqa: E402
from hearsay.authbench.locate import DEFAULT_ROOT  # noqa: E402

pytestmark = pytest.mark.skipif(not (DEFAULT_ROOT / "authorization_eva_sandbox").is_dir(),
                                reason="no AuthorizationBench checkout")


@pytest.fixture(scope="module")
def tasks():
    from hearsay.authbench.exp1_tasks import build_tasks
    return build_tasks()


@pytest.fixture(scope="module")
def sig():
    from hearsay.authbench import sigstate
    return sigstate


def test_cell_counts(tasks, sig):
    for t in tasks:
        cells = sig.cells(t)
        assert len(cells) == 3 * (16 + 12) + 16 == 100
        assert len({c["cell_id"] for c in cells}) == 100
        assert Counter((c["side"], c["claim"]) for c in cells) == Counter(
            {("valid", "none"): 28, ("valid", "negative"): 28, ("valid", "bare"): 16,
             ("invalid", "none"): 14, ("invalid", "specific"): 14})
        assert {c["instruction"] for c in cells if c["presentation"] == "signed_claim_label"} == {"aware"}
        assert {c["instruction"] for c in cells if c["claim"] == "bare"} == {"aware"}
        assert len(sig.observer_cells(t)) == 12


def test_claim_arms_differ_from_signed_by_one_line(tasks, sig):
    """signed_claim_* = signed + one line after the signature check; the two claim arms differ only in note cells,
    and there only by the reason after the verdict."""
    assert sig.CLAIM_LINES["claim"].startswith(sig.CLAIM_LINES["claim_label"] + " - ")
    for t in tasks:
        by = {(c["presentation"], c["instruction"], c["side"], c["condition"], c["claim"]): c["input"]
              for c in sig.cells(t)}
        for (p, i, side, cond, claim), text in by.items():
            if p not in sig.CLAIM_PRESENTATIONS:
                continue
            signed = by[("signed", i, side, cond, claim)].split("\n")
            k = signed.index(sig.CHECK_LINE) + 1
            line = sig.CLAIM_LINES["none" if claim == "none" else sig.CLAIM_PRESENTATIONS[p]]
            assert text.split("\n") == signed[:k] + [line] + signed[k:]
            if p == "signed_claim_label" and claim == "none":
                assert text == by[("signed_claim_unproven", i, side, cond, claim)]


def test_plain_is_experiment1(tasks, sig):
    e1 = {c["cell_id"]: c["input"] for t in tasks for c in exp1.cells(t)}
    for t in tasks:
        for c in sig.cells(t):
            if c["presentation"] == "plain":
                assert c["input"] == e1[c["e1_cell_id"]]


def test_signed_only_adds_lines(tasks, sig):
    header = (sig.SOURCE_LINE, sig.CHECK_LINE, *sig.CLAIM_LINES.values())
    for t in tasks:
        for c in sig.cells(t):
            if c["presentation"] == "plain":
                continue
            plain = sig.sig_input(t, c["side"], c["condition"], c["claim"], "plain")
            kept = [x for x in c["input"].split("\n")
                    if x not in header and not x.startswith(("  signature: ", "  revocation: "))]
            assert "\n".join(kept) == plain
            lines = c["input"].split("\n")
            if c["presentation"] in sig.CLAIM_PRESENTATIONS:
                want = sig.CLAIM_LINES["none" if c["claim"] == "none" else sig.CLAIM_PRESENTATIONS[c["presentation"]]]
                assert [x for x in lines if x.startswith("claim_check: ")] == [want]
            else:
                assert not any(x.startswith("claim_check: ") for x in lines)
            assert sig.CHECK_LINE in c["input"]


def test_every_record_and_revocation_is_signed_and_verifies(tasks, sig):
    from hearsay.authbench.exp1 import registry
    for t in tasks:
        for side, condition, _ in sig.plan():
            text = sig.signed_evidence(t, side, condition)
            reg = registry(t, side, condition)
            assert text.count("  signature: ") == len(reg.approvals)
            assert text.count("  revocation: ") == sum(a.revoked for a in reg.approvals)
            for a in reg.approvals:
                s = sig.sign(a.issuer, sig.grant_event(a))
                assert sig.verify(sig.role_key(a.issuer).public_key(), sig.grant_event(a), s)
                other = {**sig.grant_event(a), "valid_until": "2099-01-01"}
                assert not sig.verify(sig.role_key(a.issuer).public_key(), other, s)


def test_labels_follow_the_gate(tasks, sig):
    for t in tasks:
        for c in sig.cells(t):
            lab = sig.label(t, c)
            assert lab["gate_allowed"] == (c["side"] == "valid")
            assert lab["expected"] == ("approve" if c["side"] == "valid" else "reject")


def test_observer_message_rules(tasks, sig):
    t = tasks[0]
    original = exp1.delegation(t, "negative", "direct")
    cleaned = exp1.delegation(t, "none", "direct")
    raw = json.dumps({"decision": "injection", "cleaned_message": cleaned})
    assert sig.observer_message(raw, original) == (cleaned, "injection")
    assert sig.observer_message(json.dumps({"decision": "clean", "cleaned_message": "x"}), original) == (original, "clean")
    assert sig.observer_message("not json", original) == (original, "unparsable")
    stage2 = sig.observer_stage2_input(t, "valid", "direct", "negative", cleaned)
    assert stage2 == exp1.e1_input(t, "valid", "direct", "none")
