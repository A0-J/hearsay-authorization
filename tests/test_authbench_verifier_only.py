"""Experiment A before any API call: the items, what each method sees, and the scoring against expected judgments."""

from hearsay.authbench import dataset, evaluate, verifier_only
from hearsay.authbench.fake import ClaimFollowerClient
from hearsay.authbench.paired import CONDITIONS, DELEGATION_VARIANTS, SPECS

WORK = verifier_only.items()
N_PROBES = sum(len(s.probes) for s in SPECS)


def scored_with(rule):
    """Synthetic verdicts: allow = rule(item, label) for every item, one method."""
    index = evaluate.labels()
    verdicts = [{**it, "method": "m", "allow": rule(it, index[(it["task_id"], it["probe_id"], it["condition"])])}
                for it in WORK]
    return evaluate.score(verdicts)


def test_items_cover_probes_delegations_and_conditions():
    assert len(WORK) == N_PROBES * len(DELEGATION_VARIANTS) * len(CONDITIONS)
    assert len({it["item_id"] for it in WORK}) == len(WORK)


def test_label_totals():
    m = evaluate.metrics(scored_with(lambda it, lab: True))["m"]
    assert (m["n"], m["n_unauthorized"], m["n_valid"], m["n_off_intent"]) == (132, 96, 20, 16)


def test_expected_judgments_of_reference_verifiers():
    final = evaluate.metrics(scored_with(lambda it, lab: lab["final_allow"]))["m"]
    assert final["unauthorized_accepted"] == final["valid_rejected"] == final["off_intent_accepted"] == 0
    assert final["agree_final"] == final["n"] and final["claim_dependence"]["changed"] == 0

    authz = evaluate.metrics(scored_with(lambda it, lab: lab["authorization_valid"]))["m"]
    assert authz["unauthorized_accepted"] == authz["valid_rejected"] == 0
    assert authz["off_intent_accepted"] == authz["n_off_intent"]          # authorization alone lets them through

    always = evaluate.metrics(scored_with(lambda it, lab: True))["m"]
    assert always["unauthorized_accepted"] == always["n_unauthorized"] and always["valid_rejected"] == 0

    follower = evaluate.metrics(scored_with(lambda it, lab: it["delegation"] == "claim"))["m"]
    dep = follower["claim_dependence"]
    assert dep["pairs"] == N_PROBES * len(CONDITIONS) == dep["changed"] == dep["approve_only_with_claim"]
    assert follower["unauthorized_accepted"] == follower["n_unauthorized"] // 2   # the claim half
    assert follower["valid_rejected"] == follower["n_valid"] // 2                 # the no-claim half


def test_provenance_gate_decides_exactly_the_authorization_label():
    verdicts = list(verifier_only.run(WORK, ("provenance_gate",), client=None, model="-", n_votes=1))
    assert all(r["allow"] == r["A"] for r in evaluate.score(verdicts))


def test_claim_only_and_semantic_inputs_are_reused_across_approval_states():
    client = ClaimFollowerClient()
    verdicts = list(verifier_only.run(WORK, ("llm_claim_only", "dualflow"), client=client, model="m", n_votes=1))
    claim_only = [v for v in verdicts if v["method"] == "llm_claim_only"]
    semantic = [v["decision"]["semantic"] for v in verdicts if v["method"] == "dualflow"]
    # claim-only: one input per probe x delegation; the semantic flow: one per probe
    assert sum(not v["decision"]["reused"] for v in claim_only) == N_PROBES * len(DELEGATION_VARIANTS)
    assert sum(not s["reused"] for s in semantic) == N_PROBES
    assert client.calls == N_PROBES * len(DELEGATION_VARIANTS) + N_PROBES
    # what claim-only sees is the same under every approval state of a probe and delegation
    by_key = {}
    for v in claim_only:
        by_key.setdefault((v["task_id"], v["probe_id"], v["delegation"]), set()).add(v["decision"]["input_sha256"])
    assert all(len(h) == 1 for h in by_key.values())


def test_evidence_inputs_differ_across_approval_states_only_in_the_record():
    from hearsay.authbench.calls import ToolCall
    from hearsay.authbench.prompts import verifier_input
    task = SPECS[0].task_id
    inputs = dataset.load_inputs(task)
    call = ToolCall(**inputs["probes"][0]["call"])
    texts = {c: verifier_input(call, inputs["delegations"]["claim"], dataset.registry(task, c), "with_evidence")
             for c in CONDITIONS}
    heads = {t.split("Records of the organization's approval system:")[0] for t in texts.values()}
    assert len(heads) == 1 and len(set(texts.values())) == len(CONDITIONS)


def test_experiment_a_config_pins_the_current_prompts_and_sampling():
    import json
    from pathlib import Path

    from hearsay.authbench import prompts
    from hearsay.authbench.paired import DATASET_VERSION
    from hearsay.llm import sampling_for
    cfg = json.loads((Path(__file__).resolve().parents[1] / "configs" / "experiment_a.json").read_text(encoding="utf-8"))
    assert cfg["prompts_sha256"] == prompts.fingerprints()
    assert cfg["sampling"] == sampling_for(cfg["model"]) and cfg["model"] == "gpt-4.1"
    assert cfg["dataset"]["version"] == DATASET_VERSION and cfg["tasks"] == [s.task_id for s in SPECS]
