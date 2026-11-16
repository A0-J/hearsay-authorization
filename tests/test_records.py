from hearsay.proposal import REFUSE, Proposal, modal
from hearsay.records import Grant, RecordStore, provenance_gate


def store(*grants, **kw):
    return RecordStore(today="2026-11-16", grants=grants, authority={"boss": frozenset({"pay"}), "clerk": frozenset()},
                       roles={"boss": "Boss", "clerk": "Clerk"}, amounts={"inv:1": 100, "inv:2": 900},
                       open_actions=frozenset({"view"}), **kw)


G = Grant("A-1", "boss", "pay", "inv:*", "vendor:x", "2026-12-31", max_amount=500)


def reason(p, s):
    return provenance_gate(p, s).reason


def test_gate_reasons():
    pay1 = Proposal("pay", "inv:1", "vendor:x")
    assert reason(pay1, store(G)) == "authorized"
    assert reason(pay1, store()) == "no_grant"
    assert reason(pay1, store(G.with_(revoked=True))) == "revoked"
    assert reason(pay1, store(G.with_(valid_until="2026-11-15"))) == "expired"
    assert reason(pay1, store(G.with_(valid_until="2026-11-16"))) == "authorized"   # inclusive
    assert reason(pay1, store(G.with_(issuer="clerk"))) == "issuer_lacks_authority"
    assert reason(Proposal("pay", "inv:1", "vendor:y"), store(G)) == "no_grant"   # another scope: not covered
    assert reason(Proposal("pay", "inv:2", "vendor:x"), store(G)) == "exceeds_limit"
    assert reason(Proposal("pay", "inv:9", "vendor:x"), store(G)) == "exceeds_limit"   # unknown amount fails closed
    assert reason(Proposal("view", "inv:1", ""), store()) == "no_approval_needed"
    assert reason(REFUSE, store(G)) == "refused"


def test_any_covering_grant_suffices():
    bad, good = G.with_(grant_id="A-0", revoked=True), G
    assert provenance_gate(Proposal("pay", "inv:1", "vendor:x"), store(bad, good)).grant_id == "A-1"


def test_prefix_and_exact_resources():
    assert G.matches_resource("inv:77") and not G.matches_resource("invoice:1")
    assert Grant("B", "boss", "pay", "inv:1", "s", "2027-01-01").matches_resource("inv:1")
    assert not Grant("B", "boss", "pay", "inv:1", "s", "2027-01-01").matches_resource("inv:10")


def test_render_mentions_every_record():
    text = store(G, G.with_(grant_id="A-2", revoked=True)).render()
    assert "A-1" in text and "A-2" in text and "revoked" in text and "Today: 2026-11-16" in text


def test_modal_ties_go_to_the_earliest():
    a, b = Proposal("pay", "x", "s"), Proposal("hold", "x", "s")
    assert modal([a, b, b, a]) == a and modal([b, a, a]) == a and modal([]) is None
