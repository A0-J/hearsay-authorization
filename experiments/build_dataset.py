"""Build dataset/ (the Hearsay pilot dataset) from the pinned AuthorizationBench checkout.

    python experiments/build_dataset.py

Writes, from src/hearsay/authbench/paired.py and the original task bundles (read only):

  dataset/selection.csv          every original task (286): source fields, tools, and the review
                                 (reviewed tasks only; the rest are marked unreviewed/unverified)
  dataset/source_manifest.json   repository, commit, license, paper, hashes of the benchmark code used
  dataset/tasks/<task_id>/       metadata.json, policy.json, inputs.json, <condition>.json x 6,
                                 ground_truth.json

Every check runs before anything is written: reference dates, explicit policy levels for every
tool that is not read-only, probe tools in the allowlist, and the expected labels. The files are
generated; change paired.py and re-run, never edit them by hand. dataset/README.md and
dataset/schema.json are written by hand.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys

if os.name == "nt" and not sys.flags.utf8_mode:   # the benchmark reads its bundles with the default encoding
    os.environ["PYTHONUTF8"] = "1"
    sys.exit(subprocess.call([sys.executable, *sys.argv]))

from common import ROOT  # noqa: E402

from hearsay.authbench import paired  # noqa: E402
from hearsay.authbench.calls import READ, effect  # noqa: E402
from hearsay.authbench.locate import PINNED_COMMIT, REPO_URL, authbench_root, checkout_commit, tasks_dir  # noqa: E402
from hearsay.authbench.paired import (CONDITIONS, DATASET_VERSION, RECORD_CHANGE, REVIEW, SPECS,  # noqa: E402
                                      PairedSpec)
from hearsay.authbench.task import AuthBenchTask, load_task  # noqa: E402

OUT = ROOT / "dataset"
GENERATED = ("selection.csv", "source_manifest.json", "tasks")
RUNTIME_CODE = ("authorization_eva_sandbox/evaluation/run_eval.py",
                "authorization_eva_sandbox/evaluation/task_bundle.py",
                "authorization_eva_sandbox/evaluation/harness/mcp_gateway.py",
                "authorization_eva_sandbox/evaluation/harness/tool_ir.py",
                "authorization_eva_sandbox/evaluation/harness/tool_name_adapter.py",
                "authorization_eva_sandbox/services/multi_server.py")
UNREVIEWED = "unverified"


def sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path) -> str:
    return path.relative_to(authbench_root()).as_posix()


def bundle_files(task: AuthBenchTask) -> list[dict]:
    return [{"path": rel(p), "sha256": sha256(p)} for p in sorted(task.bundle.rglob("*")) if p.is_file()]


def vignette(task: AuthBenchTask) -> dict:
    return json.loads((task.bundle / "vignette.json").read_text(encoding="utf-8"))


def task_config(task: AuthBenchTask) -> dict:
    return json.loads((task.bundle / "task_config.json").read_text(encoding="utf-8"))


# --- selection.csv --------------------------------------------------------------------------------------------

COLUMNS = ("task_id", "source_vignette", "source_seed", "domain", "situational_trigger", "harm", "reference_time",
           "instruction", "completion_criteria", "intention_clarification", "violated_actions", "tools",
           "non_read_tools", "workspace_tools", "runs_without_workspace", "reviewed", "state_change_requested",
           "legitimate_approval_constructible", "usage", "reason", "task_config_sha256")


def selection_row(task: AuthBenchTask) -> dict:
    cfg, scope = task_config(task), task.contract.get("authorization_scope", {})
    review = REVIEW.get(task.task_id)
    if not task.needs_workspace and review is None:
        raise SystemExit(f"{task.task_id} runs without the workspace but has no review in paired.REVIEW")
    return {
        "task_id": task.task_id, "source_vignette": cfg.get("source_vignette", ""),
        "source_seed": vignette(task).get("source_seed", ""), "domain": task.domain,
        "situational_trigger": task.trigger, "harm": task.harm, "reference_time": task.reference_time,
        "instruction": task.instruction, "completion_criteria": " || ".join(task.contract.get("completion_criteria", [])),
        "intention_clarification": scope.get("intention_clarification", ""),
        "violated_actions": " || ".join(scope.get("violated_actions", [])),
        "tools": "; ".join(task.allowlist), "non_read_tools": "; ".join(t for t in task.allowlist if effect(t) != READ),
        "workspace_tools": "; ".join(task.shell_tools), "runs_without_workspace": "no" if task.needs_workspace else "yes",
        "reviewed": "yes" if review else "no",
        "state_change_requested": review.state_change_requested if review else UNREVIEWED,
        "legitimate_approval_constructible": review.legitimate_approval_constructible if review else UNREVIEWED,
        "usage": review.usage if review else "unreviewed",
        "reason": review.reason if review else "needs the workspace container (not wired); not reviewed",
        "task_config_sha256": sha256(task.bundle / "task_config.json"),
    }


# --- one paired task ------------------------------------------------------------------------------------------

def check(spec: PairedSpec, task: AuthBenchTask, calls: dict, labels: list[dict]) -> list[str]:
    problems = []
    if spec.reference_date != task.today:
        problems.append(f"reference date {spec.reference_date} != the task's reference_time {task.reference_time}")
    non_read = {t for t in task.allowlist if effect(t) != READ}
    if set(spec.tool_policy) != non_read:
        problems.append(f"policy levels {sorted(spec.tool_policy)} != the non-read tools {sorted(non_read)}")
    if set(spec.tool_policy) != set(spec.tool_policy_reasons):
        problems.append("every policy level needs a reason")
    if spec.tool_policy.get(spec.gated_tool) != "required":
        problems.append(f"{spec.gated_tool} must need an approval")
    problems += [f"probe {k} calls {c.tool}, not in the allowlist" for k, c in calls.items() if c.tool not in task.allowlist]
    if task.needs_workspace:
        problems.append("the task needs the workspace container")
    aligned = [p.probe_id for p in spec.probes if p.intent_aligned]
    for lab in labels:
        if lab["probe_id"] in aligned and lab["authorization_reason"] != spec.expected_reason(lab["condition"]):
            problems.append(f"{lab['condition']}/{lab['probe_id']}: {lab['authorization_reason']}, "
                            f"expected {spec.expected_reason(lab['condition'])}")
        if lab["condition"] == "misquoted_other_valid" and lab["claimed_approval_on_record"]:
            problems.append("misquoted_other_valid must not have the claimed id on record")
    return problems


def task_files(spec: PairedSpec) -> dict[str, dict]:
    task = load_task(spec.task_id)
    calls = paired.probe_calls(spec, task.bundle)
    labels = paired.labels(spec, calls)
    problems = check(spec, task, calls, labels)
    if problems:
        raise SystemExit(f"{spec.task_id}: " + "; ".join(problems))
    cfg, review = task_config(task), REVIEW[spec.task_id]
    added = ["policy.json: the runtime policy (pi): a level for every tool that is not read-only, the approver "
             "and its authority, the reference date",
             "inputs.json: the planner's handoff note with the authority claim; scripted delegations with and "
             "without it; probe calls built by rule from the original fixtures",
             "<condition>.json: the approval state (sigma), one file per condition",
             "ground_truth.json/extension: authorization, intent and final labels per probe x condition"]
    if any(c.context for c in calls.values()):
        added.append("runtime: the payment's context (selected line items, total) is read from the service state "
                     "before verification (hearsay.authbench.calls.CONTEXT_RESOLVERS)")
    metadata = {
        "task_id": spec.task_id, "dataset_version": DATASET_VERSION,
        "source": {"benchmark": "AuthorizationBench", "repository": REPO_URL, "commit": PINNED_COMMIT,
                   "bundle": rel(task.bundle), "source_vignette": cfg.get("source_vignette"),
                   "source_seed": vignette(task).get("source_seed"), "files": bundle_files(task)},
        "original": {"instruction": task.instruction, "domain": task.domain, "situational_trigger": task.trigger,
                     "harm": task.harm, "reference_time": task.reference_time, "tools": list(task.allowlist),
                     "read_only_tools": [t for t in task.allowlist if effect(t) == READ],
                     "workspace_tools": list(task.shell_tools)},
        "modifications": {"user_request": "unchanged", "system_prompt": "unchanged", "fixtures": "unchanged",
                          "tool_allowlist": "unchanged",
                          "contract": "unchanged; copied verbatim to ground_truth.json/original", "added": added},
        "selection": {"usage": review.usage, "reason": review.reason},
        "information_flow": {
            "planner": ["the original request", "inputs.json/handoff_note"],
            "executor": ["the original sealed system prompt", "the planner's message",
                         "the approval lookup tool, only with --record-lookup"],
            "every verifier": ["the task message", "the proposed call (with its context)", "policy.json"],
            "llm_with_evidence and provenance_gate": ["<condition>.json"],
            "evaluation only": ["ground_truth.json"]},
        "evaluation_scope": ("the original blueprint mounts no workspace tools; every call that is not read-only "
                             "passes the verifier"),
        "gated_tool": spec.gated_tool, "approver": spec.approver_title, "reference_date": spec.reference_date,
        "conditions": [{"condition": c, "file": f"{c}.json", "record_change": RECORD_CHANGE[c]} for c in CONDITIONS],
        "generation": {"generator": "experiments/build_dataset.py", "spec": "src/hearsay/authbench/paired.py",
                       "spec_sha256": sha256(ROOT / "src" / "hearsay" / "authbench" / "paired.py"),
                       "probe_rules": {p.probe_id: p.rule or "fixed call in paired.py" for p in spec.probes}},
    }
    inputs = {"task_id": spec.task_id, "request": task.instruction, "handoff_note": spec.handoff_note,
              "delegations": spec.delegations(task.instruction),
              "probes": [{"probe_id": k, "call": c.to_dict()} for k, c in calls.items()]}
    ground_truth = {
        "task_id": spec.task_id,
        "original": {"source_file": rel(task.bundle / "task_config.json"),
                     "sha256": sha256(task.bundle / "task_config.json"),
                     "completion_criteria": cfg["completion_criteria"],
                     "authorization_scope": cfg["authorization_scope"]},
        "extension": {"probes": [{"probe_id": p.probe_id, "description": p.description,
                                  "intent_aligned": p.intent_aligned, "basis": p.basis} for p in spec.probes],
                      "labels": labels}}
    files = {"metadata.json": metadata, "policy.json": spec.policy(), "inputs.json": inputs,
             "ground_truth.json": ground_truth}
    files.update({f"{c}.json": spec.condition_file(c) for c in CONDITIONS})
    return files


def source_manifest(n_tasks: int) -> dict:
    root = authbench_root()
    return {
        "dataset": "hearsay-authbench", "dataset_version": DATASET_VERSION,
        "source": {"benchmark": "AuthorizationBench", "repository": REPO_URL, "commit": PINNED_COMMIT,
                   "checkout_commit_at_build": checkout_commit(), "license": "MIT",
                   "license_sha256": sha256(root / "LICENSE"),
                   "paper": {"title": "Act on Your Behalf, Beyond Your Authorization: Benchmarking LLM Agent "
                                      "Authorization Alignment",
                             "authors": "Zhang, Zhiping; Li, Franklin Mingzhe; Huang, Raio Zihao; Li, Tianshi",
                             "arxiv": "2610.27548", "year": 2026},
                   "tasks_dir": rel(tasks_dir()), "task_count": n_tasks},
        "benchmark_code_used_at_run_time": [{"path": p, "sha256": sha256(root / p)} for p in RUNTIME_CODE],
        "modifications_to_source": "none: the checkout is read-only input; everything added is under dataset/tasks/",
        "generation": {"generator": "experiments/build_dataset.py", "spec": "src/hearsay/authbench/paired.py",
                       "rules": "see dataset/README.md (Construction)"},
    }


def main() -> None:
    if checkout_commit() != PINNED_COMMIT:
        raise SystemExit(f"the checkout is at {checkout_commit()}, not the pinned {PINNED_COMMIT}")
    tasks = [load_task(p.name) for p in sorted(tasks_dir().iterdir()) if (p / "task_config.json").is_file()]
    rows = [selection_row(t) for t in tasks]
    per_task = {s.task_id: task_files(s) for s in SPECS}            # every check before any write
    for name in GENERATED:
        target = OUT / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    OUT.mkdir(exist_ok=True)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    (OUT / "selection.csv").write_text(buf.getvalue(), encoding="utf-8")
    (OUT / "source_manifest.json").write_text(json.dumps(source_manifest(len(tasks)), indent=2, ensure_ascii=False)
                                              + "\n", encoding="utf-8")
    for task_id, files in per_task.items():
        d = OUT / "tasks" / task_id
        d.mkdir(parents=True)
        for name, content in files.items():
            (d / name).write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    usage = {u: sum(r["usage"] == u for r in rows) for u in paired.USAGES}
    print(f"{len(rows)} tasks in selection.csv {usage}; {len(per_task)} tasks x {len(CONDITIONS)} conditions "
          f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
