"""Reading the Hearsay dataset (dataset/) at run time.

Run-time inputs come from three files per task, and only these reach agents or verifiers:
  policy.json        the runtime policy (pi)
  <condition>.json   the approval state (sigma)
  inputs.json        the planner's handoff note, the scripted delegations, the probe calls

ground_truth.json is read only by `load_ground_truth`, which evaluation code calls; nothing in
the runtime or the prompts imports it. metadata.json documents lineage and is not a run input.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .approvals import ApprovalRegistry
from .calls import ToolCall
from .paired import CONDITIONS, compose_registry

DATASET_DIR = Path(__file__).resolve().parents[3] / "dataset"
RUN_INPUTS = ("policy.json", "inputs.json") + tuple(f"{c}.json" for c in CONDITIONS)


def task_dir(task_id: str, root: Path = DATASET_DIR) -> Path:
    d = root / "tasks" / task_id
    if not d.is_dir():
        raise FileNotFoundError(f"{task_id} is not in the dataset ({root}); run experiments/build_dataset.py")
    return d


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_policy(task_id: str, root: Path = DATASET_DIR) -> dict[str, Any]:
    return _read(task_dir(task_id, root) / "policy.json")


def load_condition(task_id: str, condition: str, root: Path = DATASET_DIR) -> dict[str, Any]:
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition {condition!r}; choose from {CONDITIONS}")
    return _read(task_dir(task_id, root) / f"{condition}.json")


def load_inputs(task_id: str, root: Path = DATASET_DIR) -> dict[str, Any]:
    return _read(task_dir(task_id, root) / "inputs.json")


def registry(task_id: str, condition: str, root: Path = DATASET_DIR) -> ApprovalRegistry:
    """pi + sigma for one condition, judged on the task's reference date."""
    return compose_registry(load_policy(task_id, root), load_condition(task_id, condition, root))


def probes(task_id: str, root: Path = DATASET_DIR) -> dict[str, ToolCall]:
    return {p["probe_id"]: ToolCall(**p["call"]) for p in load_inputs(task_id, root)["probes"]}


def task_ids(root: Path = DATASET_DIR) -> list[str]:
    return sorted(p.name for p in (root / "tasks").iterdir() if p.is_dir())


def load_ground_truth(task_id: str, root: Path = DATASET_DIR) -> dict[str, Any]:
    """Evaluation only."""
    return _read(task_dir(task_id, root) / "ground_truth.json")
