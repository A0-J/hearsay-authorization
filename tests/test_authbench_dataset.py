"""The committed dataset (dataset/): generated from the specs, labels consistent, inputs free of answers.

Runs from the committed files; the AuthorizationBench checkout is not needed (0 API calls).
"""

import csv
import json
from pathlib import Path

import jsonschema
import pytest

from hearsay.authbench import dataset
from hearsay.authbench.calls import READ, effect
from hearsay.authbench.paired import BY_ID, CONDITIONS, REVIEW, SPECS, labels

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dataset"
SELECTION = {r["task_id"]: r for r in csv.DictReader(open(DATA / "selection.csv", encoding="utf-8"))}
SCHEMA = json.loads((DATA / "schema.json").read_text(encoding="utf-8"))
ANSWER_KEYS = {"authorization_valid", "intent_aligned", "final_allow", "claimed_approval_on_record",
               "claimed_approval_authorizes", "authorization_reason", "basis"}
IDS = [s.task_id for s in SPECS]


def validate(instance, definition):
    jsonschema.validate(instance, {**SCHEMA, "$ref": f"#/$defs/{definition}"})


def test_selection_covers_every_original_task_and_marks_unreviewed():
    assert len(SELECTION) == 286
    for task_id, row in SELECTION.items():
        validate(row, "selection_row")
        if task_id in REVIEW:
            assert row["reviewed"] == "yes" and row["usage"] == REVIEW[task_id].usage
        else:
            assert row["reviewed"] == "no" and row["usage"] == "unreviewed"
            assert row["state_change_requested"] == row["legitimate_approval_constructible"] == "unverified"
    runnable = {t for t, r in SELECTION.items() if r["runs_without_workspace"] == "yes"}
    assert runnable == set(REVIEW)                       # every runnable task is reviewed
    assert {t for t, r in SELECTION.items() if r["usage"] == "paired_authorization"} == set(IDS)


@pytest.mark.parametrize("task_id", IDS)
def test_files_are_generated_from_the_specs(task_id):
    spec = BY_ID[task_id]
    assert dataset.load_policy(task_id) == spec.policy()
    for c in CONDITIONS:
        assert dataset.load_condition(task_id, c) == spec.condition_file(c)
    inputs = dataset.load_inputs(task_id)
    assert inputs["handoff_note"] == spec.handoff_note
    assert inputs["delegations"] == spec.delegations(SELECTION[task_id]["instruction"])
    for name, definition in (("metadata.json", "metadata"), ("policy.json", "policy"), ("inputs.json", "inputs"),
                             ("ground_truth.json", "ground_truth")):
        validate(json.loads((DATA / "tasks" / task_id / name).read_text(encoding="utf-8")), definition)
    for c in CONDITIONS:
        validate(dataset.load_condition(task_id, c), "condition")


@pytest.mark.parametrize("task_id", IDS)
def test_policy_is_explicit_for_every_tool_that_is_not_read_only(task_id):
    policy = dataset.load_policy(task_id)
    non_read = set(SELECTION[task_id]["non_read_tools"].split("; "))
    assert set(policy["tool_policy"]) == non_read == {t for t in SELECTION[task_id]["tools"].split("; ")
                                                       if effect(t) != READ}
    assert policy["tool_policy"][BY_ID[task_id].gated_tool] == "required"


@pytest.mark.parametrize("task_id", IDS)
def test_approvals_are_judged_on_the_tasks_reference_date(task_id):
    assert dataset.load_policy(task_id)["reference_date"] == SELECTION[task_id]["reference_time"][:10]
    for c in CONDITIONS:
        assert dataset.registry(task_id, c).today == SELECTION[task_id]["reference_time"][:10]


@pytest.mark.parametrize("task_id", IDS)
def test_labels_follow_from_the_record_and_the_probe(task_id):
    spec, truth = BY_ID[task_id], dataset.load_ground_truth(task_id)
    stored = truth["extension"]["labels"]
    assert stored == labels(spec, dataset.probes(task_id))   # recomputed from the committed inputs
    assert len(stored) == len(CONDITIONS) * len(spec.probes)
    for lab in stored:
        assert lab["final_allow"] == (lab["authorization_valid"] and lab["intent_aligned"])
        if lab["condition"] in ("valid", "misquoted_other_valid") and lab["intent_aligned"]:
            assert lab["authorization_valid"] and lab["final_allow"]
        if lab["condition"] not in ("valid", "misquoted_other_valid"):
            assert not lab["authorization_valid"] and not lab["final_allow"]
        if lab["condition"] == "misquoted_other_valid":
            assert not lab["claimed_approval_on_record"] and not lab["claimed_approval_authorizes"]


def test_the_four_authorization_intent_cases_exist():
    cases = {(lab["authorization_valid"], lab["intent_aligned"], lab["final_allow"])
             for t in IDS for lab in dataset.load_ground_truth(t)["extension"]["labels"]}
    assert cases == {(True, True, True), (True, False, False), (False, True, False), (False, False, False)}


@pytest.mark.parametrize("task_id", IDS)
def test_run_inputs_hold_no_answers(task_id):
    text = "".join((DATA / "tasks" / task_id / name).read_text(encoding="utf-8") for name in dataset.RUN_INPUTS)
    for key in ANSWER_KEYS:
        assert f'"{key}"' not in text
    for probe in dataset.load_ground_truth(task_id)["extension"]["probes"]:   # the evaluation-side descriptions
        assert probe["description"] not in text and probe["basis"] not in text
    assert all(p["probe_id"].startswith("probe-") for p in dataset.load_inputs(task_id)["probes"])


@pytest.mark.parametrize("task_id", IDS)
def test_original_contract_is_kept_apart_and_verbatim(task_id):
    truth = dataset.load_ground_truth(task_id)
    assert set(truth) == {"task_id", "original", "extension"}
    assert truth["original"]["sha256"] == SELECTION[task_id]["task_config_sha256"]
    assert " || ".join(truth["original"]["authorization_scope"]["violated_actions"]) == \
        SELECTION[task_id]["violated_actions"]


@pytest.mark.parametrize("task_id", [t for t in IDS if t.startswith("T0010")])
def test_meeting_probes_differ_only_by_the_post_meeting_conversation(task_id):
    p1, p2 = (dataset.probes(task_id)[k] for k in ("probe-1", "probe-2"))
    assert {k: v for k, v in p1.arguments.items() if k != "body"} == \
        {k: v for k, v in p2.arguments.items() if k != "body"}
    assert p2.arguments["body"].startswith(p1.arguments["body"])
    assert len(p2.arguments["body"]) > len(p1.arguments["body"])


def test_source_manifest_pins_the_benchmark():
    m = json.loads((DATA / "source_manifest.json").read_text(encoding="utf-8"))
    validate(m, "source_manifest")
    assert m["source"]["commit"] == m["source"]["checkout_commit_at_build"]
    assert m["source"]["task_count"] == len(SELECTION)
