"""The reviewer's offline Signed DualFlow pilot (experiments/signed_dualflow_offline_pilot.py, kept as received).

Runs its 15 unit tests, and records the gaps found on 2026-11-18 as strict xfails: each states the property the
design document claims or the cited drafts require, and fails today. A fix turns the xfail into an XPASS, which
strict mode reports, so the marker must then be removed. No LLM call; nothing here is an experiment result.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("cryptography")

_PATH = Path(__file__).resolve().parents[1] / "experiments" / "signed_dualflow_offline_pilot.py"
_spec = importlib.util.spec_from_file_location("signed_dualflow_offline_pilot", _PATH)
pilot = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pilot)

# The pilot's own 15 tests, collected by pytest as a unittest.TestCase.
OfflineBoundaryTests = pilot.OfflineBoundaryTests

REQ = {"merchant": "shop-A", "max_cents": 50000}
ACT = {"merchant": "shop-A", "total_cents": 42000, "card_token": "card-1"}


def _system():
    ledger = pilot.AuthorityLedger()
    ledger.grant()
    return ledger, pilot.SignedDualFlow(ledger)


@pytest.mark.xfail(strict=True, reason="gap: a grant can be spent again with each fresh nonce; replay protection "
                   "covers one permit only (cf. draft-gruszka-audit-decision-receipts-10 Section 4, at most once)")
def test_grant_is_not_spent_beyond_its_maximum():
    _, system = _system()
    executed = 0
    for nonce in ("n1", "n2", "n3"):
        status, permit = system.prepare(REQ, ACT, nonce=nonce)
        if status == "READY" and system.gateway_execute(permit, ACT) == "EXECUTED":
            executed += ACT["total_cents"]
    assert executed <= 50000


@pytest.mark.xfail(strict=True, reason="gap: the design document says the permit names its target gateway; "
                   "the permit carries no audience field")
def test_permit_names_its_gateway():
    _, system = _system()
    _, permit = system.prepare(REQ, ACT)
    assert {"audience", "gateway"} & set(permit["data"])


@pytest.mark.xfail(strict=True, reason="gap: GRANT/REVOKE are signed with the ledger's own key; no principal "
                   "(wallet) key exists, so the ledger operator can issue approvals")
def test_grant_is_signed_by_a_principal_key_distinct_from_the_ledger():
    ledger, _ = _system()
    assert any(k.endswith("_sk") and k != "issuer_sk" for k in vars(ledger))


def test_hearsay_is_not_an_input_of_the_checks():
    """Tests 02 and 03 hold by construction: no natural-language claim reaches prepare() or the gateway."""
    import inspect

    params = set(inspect.signature(pilot.SignedDualFlow.prepare).parameters) | set(
        inspect.signature(pilot.SignedDualFlow.gateway_execute).parameters)
    assert not {"hearsay", "claim", "message", "note"} & params
