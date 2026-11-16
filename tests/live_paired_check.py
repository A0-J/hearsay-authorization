"""Live check for the dataset task T0007 (run by tests/test_authbench_runtime.py in a UTF-8 subprocess).

Drives the router directly (no LLM) with the dataset's policy and approval state: select
charges, open the checkout, pay. Prints JSON per case.
"""

import json

from hearsay.authbench import dataset
from hearsay.authbench.runtime import Environment, ToolRouter, default_transport
from hearsay.authbench.task import load_task
from hearsay.authbench.verify import Verification

TASK = "T0007-a-g-h"
task = load_task(TASK)
out = {}
for case, condition, select in (("valid", "valid", ["li-001", "li-004"]),
                                ("scope_exceeded", "scope_exceeded", ["li-001", "li-004"]),
                                ("valid_default_selection", "valid", None)):
    registry, sent, base = dataset.registry(TASK, condition), [], default_transport()

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
    out[case] = {"sent": sent, "verified": [e.get("verified") for e in router.events],
                 "effect_observed": [e.get("effect_observed") for e in router.events],
                 "contexts": [p["call"].get("context") for p in router.proposals],
                 "allowed": [p["allowed"] for p in router.proposals],
                 "reasons": [p["record_verdict"]["reason"] for p in router.proposals], "receipts": receipts}
print(json.dumps(out))
