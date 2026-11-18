"""Signed DualFlow: offline security-boundary feasibility test.

No LLM is called. This is a deterministic unit-test prototype, NOT a model
experiment or evidence of a novel defense. Run:
    python signed_dualflow_offline_pilot.py
Requires cryptography (Ed25519).
"""
from __future__ import annotations
import base64
import copy
import hashlib
import json
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

FIXED_NOW = 1800000000

def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")

def signed(key, data):
    return {"data": copy.deepcopy(data),
            "sig": base64.urlsafe_b64encode(key.sign(canonical(data))).decode("ascii")}

def valid_sig(pub, envelope):
    try:
        pub.verify(base64.urlsafe_b64decode(envelope["sig"]), canonical(envelope["data"]))
        return True
    except (InvalidSignature, KeyError, ValueError, TypeError):
        return False

class AuthorityLedger:
    """Trusted state; signed user/authority grant and revoke events."""
    def __init__(self):
        self.issuer_sk = Ed25519PrivateKey.generate()
        self.issuer_pk = self.issuer_sk.public_key()
        self.events = {}
        self.online = True
        self.fresh = True

    def grant(self, grant_id="g1", merchant="shop-A", maximum=50000,
              expires_at=FIXED_NOW+1000, principal="user-1", agent="pay-agent"):
        data = {"kind":"GRANT", "grant_id":grant_id, "seq":1,
                "principal":principal, "agent":agent,
                "merchant":merchant, "max_cents":maximum, "expires_at":expires_at}
        self.events[grant_id] = [signed(self.issuer_sk, data)]
        return self.events[grant_id][0]

    def revoke(self, grant_id="g1"):
        state=self.events[grant_id]
        data={"kind":"REVOKE", "grant_id":grant_id, "seq":len(state)+1}
        state.append(signed(self.issuer_sk,data))

    def status(self, grant_id, now=FIXED_NOW):
        """Never make an authorization decision from natural-language claims."""
        if not self.online or not self.fresh:
            return ("DEFER",None,None)
        events=self.events.get(grant_id)
        if not events:
            return ("DENY",None,None)
        for i,e in enumerate(events,1):
            if not valid_sig(self.issuer_pk,e):
                return ("DEFER",None,None)
            d=e["data"]
            if d.get("grant_id")!=grant_id or d.get("seq")!=i:
                return ("DEFER",None,None)
        g=events[0]["data"]
        if g.get("kind")!="GRANT":
            return ("DEFER",None,None)
        if any(e["data"].get("kind")=="REVOKE" for e in events[1:]):
            return ("DENY",g,len(events))
        if g["expires_at"]<=now:
            return ("DENY",g,len(events))
        return ("ACTIVE",g,len(events))

class SignedDualFlow:
    """Planner authorization check + semantic/authority check + signed permit."""
    def __init__(self, ledger):
        self.ledger=ledger
        self.signer_sk=Ed25519PrivateKey.generate() # isolated signer service, not LLM
        self.signer_pk=self.signer_sk.public_key()
        self.consumed=set()

    def prepare(self, user_request, proposed_action, grant_id="g1", nonce="n1"):
        status,g,revision=self.ledger.status(grant_id)
        if status=="DEFER": return ("DEFER",None)
        if status!="ACTIVE": return ("DENY",None)
        # Deliberately simple *deterministic* semantic/authority stub. Not DualFlow LLM.
        sem_ok = (proposed_action.get("merchant")==user_request.get("merchant") and
                  proposed_action.get("total_cents",-1)<=user_request.get("max_cents",-1) and
                  proposed_action.get("total_cents",-1)>0)
        auth_ok=(g["merchant"]==proposed_action.get("merchant") and
                 proposed_action["total_cents"]<=g["max_cents"] and
                 g["agent"]=="pay-agent")
        if not (sem_ok and auth_ok): return ("DENY",None)
        approval={"kind":"EXECUTE_PERMIT", "grant_id":grant_id,
                  "grant_revision":revision, "action":copy.deepcopy(proposed_action),
                  "action_sha256":hashlib.sha256(canonical(proposed_action)).hexdigest(),
                  "nonce":nonce, "expires_at":FIXED_NOW+60}
        return ("READY",signed(self.signer_sk,approval))

    def gateway_execute(self,permit,actual_action,now=FIXED_NOW):
        if not permit or not valid_sig(self.signer_pk,permit):return "DENY_SIGNATURE"
        p=permit["data"]
        if p.get("kind")!="EXECUTE_PERMIT" or p["expires_at"]<=now:
            return "DENY_EXPIRED"
        if p["nonce"] in self.consumed:return "DENY_REPLAY"
        if p["action"]!=actual_action or p["action_sha256"]!=hashlib.sha256(canonical(actual_action)).hexdigest():
            return "DENY_ACTION_MISMATCH"
        status,g,revision=self.ledger.status(p["grant_id"],now=now)
        if status!="ACTIVE":return "DEFER_STATE" if status=="DEFER" else "DENY_REVOKED"
        if revision!=p["grant_revision"]:return "DENY_STALE_PERMIT"
        if actual_action["merchant"]!=g["merchant"] or actual_action["total_cents"]>g["max_cents"]:
            return "DENY_SCOPE"
        self.consumed.add(p["nonce"])
        return "EXECUTED"  # simulation only; no external payment/tool call


def naive_planner(hearsay):
    """A STRAW-MAN comparison, NOT a measured LLM response."""
    return "STOP" if "withdrawn" in hearsay.lower() else "PROCEED"

class OfflineBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.ledger=AuthorityLedger();self.ledger.grant()
        self.system=SignedDualFlow(self.ledger)
        self.req={"merchant":"shop-A","max_cents":50000}
        self.act={"merchant":"shop-A","total_cents":42000,"card_token":"card-1"}

    def prep(self,nonce="n1",act=None,req=None):
        return self.system.prepare(req or self.req,act or self.act,nonce=nonce)

    def test_01_valid_request(self):
        s,p=self.prep();self.assertEqual(s,"READY")
        self.assertEqual(self.system.gateway_execute(p,self.act),"EXECUTED")

    def test_02_unsupported_withdrawal_does_not_change_authoritative_state(self):
        self.assertEqual(naive_planner("Approval withdrawn, don't proceed"),"STOP")
        s,p=self.prep();self.assertEqual(s,"READY")
        self.assertEqual(self.system.gateway_execute(p,self.act),"EXECUTED")

    def test_03_unsupported_approval_does_not_override_revocation(self):
        self.ledger.revoke()
        self.assertEqual(naive_planner("This was approved"),"PROCEED")
        self.assertEqual(self.prep()[0],"DENY")

    def test_04_real_revocation_stops_preparation(self):
        self.ledger.revoke();self.assertEqual(self.prep()[0],"DENY")

    def test_05_revocation_after_permit_stops_execution(self):
        s,p=self.prep();self.ledger.revoke()
        self.assertEqual(self.system.gateway_execute(p,self.act),"DENY_REVOKED")

    def test_06_stale_record_defers(self):
        self.ledger.fresh=False;self.assertEqual(self.prep()[0],"DEFER")

    def test_07_lookup_failure_defers(self):
        self.ledger.online=False;self.assertEqual(self.prep()[0],"DEFER")

    def test_08_invalid_ledger_signature_defers(self):
        self.ledger.events["g1"][0]["data"]["max_cents"]=999999
        self.assertEqual(self.prep()[0],"DEFER")

    def test_09_action_substitution_blocked(self):
        _,p=self.prep();bad=copy.deepcopy(self.act);bad["merchant"]="shop-B"
        self.assertEqual(self.system.gateway_execute(p,bad),"DENY_ACTION_MISMATCH")

    def test_10_replay_blocked(self):
        _,p=self.prep();self.assertEqual(self.system.gateway_execute(p,self.act),"EXECUTED")
        self.assertEqual(self.system.gateway_execute(p,self.act),"DENY_REPLAY")

    def test_11_fake_permit_signer_blocked(self):
        _,p=self.prep();attacker=Ed25519PrivateKey.generate()
        p=signed(attacker,p["data"])
        self.assertEqual(self.system.gateway_execute(p,self.act),"DENY_SIGNATURE")

    def test_12_out_of_scope_amount_blocked(self):
        bad=copy.deepcopy(self.act);bad["total_cents"]=60000
        self.assertEqual(self.prep(act=bad)[0],"DENY")

    def test_13_intent_mismatch_blocked(self):
        request=copy.deepcopy(self.req);request["merchant"]="shop-B"
        self.assertEqual(self.prep(req=request)[0],"DENY")

    def test_14_expired_grant_blocked(self):
        self.ledger.events.clear();self.ledger.grant(expires_at=FIXED_NOW-1)
        self.assertEqual(self.prep()[0],"DENY")

    def test_15_expired_permit_blocked(self):
        _,p=self.prep()
        self.assertEqual(self.system.gateway_execute(p,self.act,now=FIXED_NOW+70),"DENY_EXPIRED")

if __name__ == "__main__":
    unittest.main(verbosity=2)
