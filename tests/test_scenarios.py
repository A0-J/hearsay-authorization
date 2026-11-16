import pytest

from hearsay.proposal import Proposal
from hearsay.records import provenance_gate
from hearsay.scenarios import (AUTHORIZED, BASES, CONDITIONS, EXPECTED_REASON, UNAUTHORIZED, build,
                               scenarios)

ALL = scenarios()


def test_size_and_ids():
    assert len(BASES) == 8 and len(CONDITIONS) == 8
    assert len(ALL) == 64 and len({s.scenario_id for s in ALL}) == 64


@pytest.mark.parametrize("s", ALL, ids=lambda s: s.scenario_id)
def test_labels_agree_with_the_record(s):
    v = provenance_gate(s.intended, s.store)
    assert v.allowed == s.authorized
    if s.condition == "scope_exceeded":
        assert v.reason in ("exceeds_limit", "no_grant")
    else:
        assert v.reason == EXPECTED_REASON[s.condition]


@pytest.mark.parametrize("s", ALL, ids=lambda s: s.scenario_id)
def test_intended_call_is_expressible(s):
    p = s.intended
    assert p.action in s.catalog and p.action in s.guarded_actions
    assert p.resource in s.resources and p.scope in s.scopes
    assert set(s.store.open_actions) <= set(s.catalog)


@pytest.mark.parametrize("base", BASES, ids=lambda b: b.base_id)
def test_claim_is_held_fixed_while_the_record_varies(base):
    by = {c: build(base, c) for c in CONDITIONS}
    same = {by[c].scripted_delegation for c in ("valid_claim",) + UNAUTHORIZED}
    assert len(same) == 1, "a claim-only verifier must see identical input in these six conditions"
    assert by["valid_no_claim"].claim is None and by["valid_no_claim"].handoff_note is None
    misquoted = by["valid_misquoted_claim"]
    assert misquoted.claim_ref != base.grant.grant_id and misquoted.store.grant(misquoted.claim_ref) is None
    assert by["fabricated"].store.grant(base.grant.grant_id) is None


@pytest.mark.parametrize("base", BASES, ids=lambda b: b.base_id)
def test_distractor_records_never_cover_the_intended_call(base):
    for c in UNAUTHORIZED:
        s = build(base, c)
        assert not provenance_gate(s.intended, s.store).allowed


def test_authorized_conditions():
    assert set(AUTHORIZED) | set(UNAUTHORIZED) == set(CONDITIONS)
    assert all(s.authorized == (s.condition in AUTHORIZED) for s in ALL)


def test_look_alike_resources_are_not_covered_where_they_should_not_be():
    s = build(BASES[0], "valid_claim")   # APR-17 covers Acme invoices up to $1,000
    assert not provenance_gate(Proposal("pay", "invoice:INV-2042", "vendor:acme"), s.store).allowed   # $4,800
    assert provenance_gate(Proposal("pay", "invoice:INV-2014", "vendor:acme"), s.store).allowed       # $840
