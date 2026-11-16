"""Build the Experiment 2 datasets from the pinned AuthorizationBench checkout. No API calls.

    python experiments/build_exp2.py                 # the 11 Experiment 1 tasks
    python experiments/build_exp2.py --tasks gen     # the generalization tasks (when they exist)

Writes, for the chosen task set (suffix "" for the Experiment 1 tasks, "_gen" for the generalization tasks):
  dataset/exp2<suffix>/             Experiment 2, blocks A and B (docs/EXPERIMENT2_PREREG.md)
  dataset/exp2_defer<suffix>/       the DEFER arm (docs/EXPERIMENT2_DEFER_PREREG.md)
  dataset/ablation_claim_only<suffix>/, dataset/ablation_semantic<suffix>/   (docs/ABLATION_PREREG.md)
each with manifest.json, instructions.json (texts, SHA-256, allowed decisions) and tasks/<id>/{cells,labels}.jsonl.
Experiment 1's dataset (dataset/exp1/) is not touched. The build refuses to write if a block A input differs from
Experiment 1's cell or if a gate verdict differs from the cell's side.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

if os.name == "nt" and not sys.flags.utf8_mode:   # the benchmark reads its bundles with the default encoding
    os.environ["PYTHONUTF8"] = "1"
    sys.exit(subprocess.call([sys.executable, *sys.argv]))

from common import ROOT  # noqa: E402

from hearsay.authbench import exp1, exp2  # noqa: E402
from hearsay.authbench.locate import PINNED_COMMIT, checkout_commit  # noqa: E402
from hearsay.authbench.prompts import SEMANTIC_INSTRUCTIONS  # noqa: E402

APPROVE_REJECT = ["approve", "reject"]


def jsonl(rows) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def load_tasks(which: str) -> list:
    if which == "e1":
        from hearsay.authbench.exp1_tasks import build_tasks
        return build_tasks()
    if which == "ad":
        from hearsay.authbench.ad_tasks import build_tasks as build_ad
        return build_ad()
    from hearsay.authbench.gen_tasks import build_tasks as build_gen
    return build_gen()


def write(name: str, version: str, prereg: str, tasks, make_cells, make_label, instructions: dict, which: str) -> int:
    out = ROOT / "dataset" / name
    per_task = {}
    for t in tasks:
        cells = make_cells(t)
        labels = [make_label(t, c) if make_label else {"cell_id": c["cell_id"]} for c in cells]
        per_task[t.task_id] = (cells, labels)
    if out.exists():
        shutil.rmtree(out)
    for task_id, (cells, labels) in per_task.items():
        d = out / "tasks" / task_id
        d.mkdir(parents=True)
        (d / "cells.jsonl").write_text(jsonl(cells), encoding="utf-8")
        (d / "labels.jsonl").write_text(jsonl(labels), encoding="utf-8")
    (out / "instructions.json").write_text(exp1.dumps(
        {k: {"text": v, "sha256": exp1.sha(v), "decisions": dec} for k, (v, dec) in instructions.items()}),
        encoding="utf-8")
    h = hashlib.sha256()
    for p in sorted((out / "tasks").rglob("*")):
        if p.is_file():
            h.update(p.relative_to(out).as_posix().encode() + b"\0" + p.read_bytes())
    n = sum(len(c) for c, _ in per_task.values())
    manifest = {"dataset": f"hearsay-{name}", "version": version, "prereg": prereg, "task_set": which,
                "authbench_commit": PINNED_COMMIT, "tasks": list(per_task), "cells": n,
                "cells_per_task": n // max(1, len(per_task)), "tasks_sha256": h.hexdigest(),
                "spec_sha256": {m: exp1.sha((ROOT / "src" / "hearsay" / "authbench" / m).read_text(encoding="utf-8"))
                                for m in ("exp1.py", "exp2.py")},
                "experiment1_dataset": "dataset/exp1/ is separate and unchanged"}
    (out / "manifest.json").write_text(exp1.dumps(manifest), encoding="utf-8")
    print(f"{name}: {len(per_task)} tasks, {n} cells")
    return n


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", choices=("e1", "gen", "ad"), default="e1")
    a = ap.parse_args()
    if checkout_commit() != PINNED_COMMIT:
        raise SystemExit("the AuthorizationBench checkout is not at the pinned commit")
    tasks = load_tasks(a.tasks)
    suffix = {"e1": "", "gen": "_gen", "ad": "_ad"}[a.tasks]

    for t in tasks:                                   # build-time checks
        e1 = {c["cell_id"]: c for c in exp1.cells(t)}
        for c in exp2.exp2_cells(t):
            lab = exp2.exp2_label(t, c)
            if lab["gate_allowed"] != (c["side"] == "valid"):
                raise SystemExit(f"gate verdict differs from the side: {c['cell_id']}")
            if c["block"] == "A" and e1[c["e1_cell_id"]]["input_sha256"] != c["input_sha256"]:
                raise SystemExit(f"block A input differs from Experiment 1: {c['cell_id']}")

    write(f"exp2{suffix}", exp2.EXP2_VERSION, "docs/EXPERIMENT2_PREREG.md", tasks, exp2.exp2_cells, exp2.exp2_label,
          {k: (exp1.E1_INSTRUCTIONS[k], APPROVE_REJECT) for k in exp1.INSTRUCTIONS}, a.tasks)
    write(f"exp2_defer{suffix}", exp2.DEFER_VERSION, "docs/EXPERIMENT2_DEFER_PREREG.md", tasks, exp2.defer_cells,
          exp2.defer_label, {k: (v, ["approve", "reject", "defer"]) for k, v in exp2.DEFER_INSTRUCTIONS.items()},
          a.tasks)
    write(f"ablation_claim_only{suffix}", exp2.ABLATION_VERSION, "docs/ABLATION_PREREG.md", tasks,
          exp2.claim_only_cells, None, {"claim_only": (exp2.CLAIM_ONLY_INSTRUCTIONS, APPROVE_REJECT)}, a.tasks)
    write(f"ablation_semantic{suffix}", exp2.ABLATION_VERSION, "docs/ABLATION_PREREG.md", tasks,
          exp2.semantic_cells, None, {"semantic": (SEMANTIC_INSTRUCTIONS, list(exp2.SEMANTIC_DECISIONS))}, a.tasks)


if __name__ == "__main__":
    main()
