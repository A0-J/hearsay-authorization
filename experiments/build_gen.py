"""Build the generalization datasets (docs/GENERALIZATION_PREREG.md). No API calls.

    python experiments/build_gen.py

Writes dataset/exp1_gen/ (Experiment 1's cells for the new tasks; spec, cells, labels, manifest with each task's
case and reporting group) and docs/screening/generalization_review.{csv,md}, then the Experiment 2 and ablation
datasets for the same tasks (build_exp2.py --tasks gen: exp2_gen, exp2_defer_gen, ablation_*_gen). The build refuses
to write if any cell's gate verdict differs from its side.
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

if os.name == "nt" and not sys.flags.utf8_mode:
    os.environ["PYTHONUTF8"] = "1"
    sys.exit(subprocess.call([sys.executable, *sys.argv]))

from common import ROOT  # noqa: E402

from hearsay.authbench import exp1  # noqa: E402
from hearsay.authbench.locate import PINNED_COMMIT, checkout_commit  # noqa: E402
from hearsay.authbench.prompts import VERIFIER_INSTRUCTIONS  # noqa: E402

SCREEN = ROOT / "docs" / "screening"
SOURCES = {  # --source: (module, dataset suffix, review file stem, title, source modules hashed in the manifest)
    "ab": ("gen_tasks", "_gen", "generalization_review", "AuthorizationBench",
           ("gen_tasks.py", *(f"gen_tasks_g{k}.py" for k in range(1, 6)))),
    "ad": ("ad_tasks", "_ad", "generalization_review_agentdojo", "AgentDojo v1 (second source)",
           ("ad_tasks.py", "ad_tasks_bank_travel.py", "ad_tasks_slack_work.py")),
}


def jsonl(rows) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def main() -> None:
    import argparse
    import importlib
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=tuple(SOURCES), default="ab")
    a = ap.parse_args()
    mod_name, suffix, stem, title, hashed = SOURCES[a.source]
    mod = importlib.import_module(f"hearsay.authbench.{mod_name}")
    REVIEW, SELECTED, build_tasks, group = mod.REVIEW, mod.SELECTED, mod.build_tasks, mod.group
    OUT = ROOT / "dataset" / f"exp1{suffix}"
    if checkout_commit() != PINNED_COMMIT:
        raise SystemExit("the AuthorizationBench checkout is not at the pinned commit")
    tasks = build_tasks()
    per = {}
    for t in tasks:
        cells = exp1.cells(t)
        labels = [exp1.label(t, c) for c in cells]
        bad = [lab["cell_id"] for lab in labels if lab["gate_allowed"] != (lab["expected"] == "approve")]
        if bad:
            raise SystemExit(f"gate verdict differs from the side: {bad[:5]}")
        per[t.task_id] = (t, cells, labels)
    if OUT.exists():
        shutil.rmtree(OUT)
    for tid, (t, cells, labels) in per.items():
        d = OUT / "tasks" / tid
        d.mkdir(parents=True)
        (d / "spec.json").write_text(exp1.dumps({**exp1.spec_dict(t), "reporting_group": group(t),
                                                 "bg_tools": list(t.bg_tools)}), encoding="utf-8")
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
    n = sum(len(c) for _, c, _ in per.values())
    tag = suffix.replace("_", "-")
    manifest = {"dataset": f"hearsay-exp1{tag}", "version": f"1.0.0-exp1{tag}", "source": a.source,
                "prereg": "docs/GENERALIZATION_PREREG.md",
                "authbench_commit": PINNED_COMMIT, "tasks": SELECTED, "cells": n, "cells_per_task": n // len(per),
                "case_of_task": {t.task_id: t.case for t in tasks},
                "group_of_task": {t.task_id: group(t) for t in tasks}, "tasks_sha256": h.hexdigest(),
                "spec_sha256": {m: exp1.sha((ROOT / "src" / "hearsay" / "authbench" / m).read_text(encoding="utf-8"))
                                for m in ("exp1.py", *hashed)},
                "experiment1_dataset": "dataset/exp1/ is separate and unchanged"}
    (OUT / "manifest.json").write_text(exp1.dumps(manifest), encoding="utf-8")

    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["case", "domain", "task_id", "stage", "decision", "reason"])
    w.writerows(REVIEW)
    (SCREEN / f"{stem}.csv").write_text(buf.getvalue(), encoding="utf-8")
    md = [f"# Generalization review ({title})", "",
          "Rule: docs/GENERALIZATION_PREREG.md. Every `to_review` task of docs/screening/generalization_candidates.csv "
          "is listed; within a (case, domain) pair the first passing task in ascending id is selected. Reviewed "
          "before any generalization call, from request text, fixtures and tool definitions only.", "",
          f"Selected {len(SELECTED)} tasks in {len({t.case for t in tasks})} cases "
          f"({sum(group(t) == 'new_case' for t in tasks)} tasks in new cases).", "",
          "| case | domain | task | stage | decision | reason |", "|---|---|---|---|---|---|"]
    md += [f"| {c} | {dm} | {t} | {s} | {dec} | {r} |" for c, dm, t, s, dec, r in REVIEW]
    (SCREEN / f"{stem}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"exp1{suffix}: {len(per)} tasks, {n} cells")
    subprocess.check_call([sys.executable, str(ROOT / "experiments" / "build_exp2.py"), "--tasks",
                           {"ab": "gen", "ad": "ad"}[a.source]])


if __name__ == "__main__":
    main()
