"""Live check for the paired T0007 task (run by tests/test_authbench_runtime.py in a UTF-8 subprocess).

Drives the router directly (no LLM): select items, open checkout, pay. Prints JSON per case.
"""

import json

from hearsay.authbench.paired import BY_ID
from hearsay.authbench.runtime import Environment, ToolRouter, default_transport
from hearsay.authbench.task import load_task
from hearsay.authbench.verify import Verification

spec = BY_ID["T0007-a-g-h"]
task = load_task(spec.task_id)
out = {}
for case, condition, select in (("valid", "valid", ["li-001", "li-004"]),
                                ("scope_exceeded", "scope_exceeded", ["li-001", "li-004"]),
                                ("valid_default_selection", "valid", None)):
    registry, sent, base = spec.registry(condition), [], default_transport()

    def transport(url, entry, args, **kw):
        sent.append(entry["name"])
        return base(url, entry, args, **kw)

    with Environment(task) as env:
        verification = Verification(enforce="provenance_gate", shadow=("provenance_gate",), registry=registry,
                                    client=None, model="none")
        router = ToolRouter(env, task, verification, registry, delegation=task.instruction, transport=transport)
        if select is not None:
            router.call("tenant_portal.update_selection", {"selected_ids": select})
        router.call("tenant_portal.begin_checkout", {})
        router.call("tenant_portal.pay_selected", {})
        receipts = len(env.state()["tenant_portal"]["receipts"])
    out[case] = {"sent": sent, "gated": [e.get("gated") for e in router.events],
                 "contexts": [p["call"].get("context") for p in router.proposals],
                 "allowed": [p["allowed"] for p in router.proposals],
                 "reasons": [p["record_verdict"]["reason"] for p in router.proposals], "receipts": receipts}
print(json.dumps(out))
