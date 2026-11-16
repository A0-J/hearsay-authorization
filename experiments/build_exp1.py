"""Build dataset/exp1/ (Experiment 1 run 1) from the pinned AuthorizationBench checkout. No API calls.

    python experiments/build_exp1.py

Writes (the pilot dataset under dataset/tasks/ is not touched):
  dataset/exp1/manifest.json            version, pre-registration commit, benchmark commit, hashes, counts
  dataset/exp1/instructions.json        the verifier instructions used (texts and SHA-256)
  dataset/exp1/tasks/<id>/spec.json     the task: request, call, control, policy, parties, constraints, construction
  dataset/exp1/tasks/<id>/cells.jsonl   every cell's full verifier input (no labels)
  dataset/exp1/tasks/<id>/labels.jsonl  expected decision and the deterministic gate's verdict per cell
  docs/screening/seed_review.csv, seed_review.md   the pre-registered review of all 40 candidate cases
The build refuses to write if any cell's gate verdict differs from its side.
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

from hearsay.authbench import exp1  # noqa: E402
from hearsay.authbench.exp1_tasks import REVIEW, SELECTED, build_tasks  # noqa: E402
from hearsay.authbench.locate import PINNED_COMMIT, checkout_commit  # noqa: E402
from hearsay.authbench.prompts import VERIFIER_INSTRUCTIONS  # noqa: E402

OUT = ROOT / "dataset" / "exp1"
SCREEN = ROOT / "docs" / "screening"


def jsonl(rows) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def main() -> None:
    if checkout_commit() != PINNED_COMMIT:
        raise SystemExit("the AuthorizationBench checkout is not at the pinned commit")
    tasks = build_tasks()
    per_task = {}
    for t in tasks:
        cells = exp1.cells(t)
        labels = [exp1.label(t, c) for c in cells]
        bad = [lab["cell_id"] for lab in labels if lab["gate_allowed"] != (lab["expected"] == "approve")]
        if bad:
            raise SystemExit(f"gate verdict differs from the side: {bad[:5]}")
        per_task[t.task_id] = (t, cells, labels)

    if OUT.exists():
        shutil.rmtree(OUT)
    for task_id, (t, cells, labels) in per_task.items():
        d = OUT / "tasks" / task_id
        d.mkdir(parents=True)
        (d / "spec.json").write_text(exp1.dumps(exp1.spec_dict(t)), encoding="utf-8")
        (d / "cells.jsonl").write_text(jsonl(cells), encoding="utf-8")
        (d / "labels.jsonl").write_text(jsonl(labels), encoding="utf-8")
    instructions = {"aware": exp1.E1_INSTRUCTIONS["aware"], "explicit": exp1.E1_INSTRUCTIONS["explicit"],
                    "aware_pilot_format": VERIFIER_INSTRUCTIONS["with_evidence"]}
    (OUT / "instructions.json").write_text(exp1.dumps(
        {k: {"text": v, "sha256": exp1.sha(v)} for k, v in instructions.items()}), encoding="utf-8")
    h = hashlib.sha256()
    for p in sorted((OUT / "tasks").rglob("*")):
        if p.is_file():
            h.update(p.relative_to(OUT).as_posix().encode() + b"\0" + p.read_bytes())
    n_cells = sum(len(c) for _, c, _ in per_task.values())
    manifest = {"dataset": "hearsay-exp1", "version": exp1.EXP1_VERSION, "prereg_commit": exp1.PREREG_COMMIT,
                "authbench_commit": PINNED_COMMIT, "tasks": SELECTED, "cells": n_cells,
                "cells_per_task": n_cells // len(per_task), "tasks_sha256": h.hexdigest(),
                "spec_sha256": {m: exp1.sha((ROOT / "src" / "hearsay" / "authbench" / m).read_text(encoding="utf-8"))
                                for m in ("exp1.py", "exp1_tasks.py")},
                "pilot_dataset": "dataset/tasks/ (v0.2.0-pilot) is separate and unchanged"}
    (OUT / "manifest.json").write_text(exp1.dumps(manifest), encoding="utf-8")

    SCREEN.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["case", "task_id", "stage", "decision", "reason"])
    w.writerows(REVIEW)
    (SCREEN / "seed_review.csv").write_text(buf.getvalue(), encoding="utf-8")
    md = ["# Source-case review for Experiment 1 run 1", "",
          "Pre-registered rule (docs/EXPERIMENT1_PREREG.md, commit e5fb9fd): cases in ascending id, the pilot's "
          "S0007 and S0010 excluded; stage 1 = the request (criterion 1; criterion 3 where the requested action is a "
          "workspace shell or file operation); stage 2 = fixtures and tool schemas (criteria 2-3). All 40 candidate "
          "cases are listed; reviewed before any Experiment 1 call.", "",
          f"Selected: {len(SELECTED)} (cap 12).", "", "| case | task | stage | decision | reason |", "|---|---|---|---|---|"]
    md += [f"| {c} | {t} | {s} | {dec} | {r} |" for c, t, s, dec, r in REVIEW]
    md += ["", "How each selected call was built is in `dataset/exp1/tasks/<id>/spec.json` (`construction`)."]
    (SCREEN / "seed_review.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{len(per_task)} tasks, {n_cells} cells -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
