"""Researcher-written summary probes: templates, checks, blind review sheets, reviewer agreement (no API calls).

    python experiments/summary_probes.py init           # templates in dataset/authoring/summary_probes/
    python experiments/summary_probes.py check          # every template filled and a valid minimal pair?
    python experiments/summary_probes.py review-sheets  # review/reviewer_{1,2}.csv (blind) + review/key.json
    python experiments/summary_probes.py agreement      # after both sheets are filled: kappa, and labels vs key

`init` never overwrites a template that already has text in it. The summaries are written by a person.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys

if os.name == "nt" and not sys.flags.utf8_mode:   # the benchmark reads its bundles with the default encoding
    os.environ["PYTHONUTF8"] = "1"
    sys.exit(subprocess.call([sys.executable, *sys.argv]))

from common import ROOT  # noqa: E402

from hearsay.authbench import dataset, summary_probes  # noqa: E402
from hearsay.authbench.paired import SPECS, _meeting, transcript_lines  # noqa: E402
from hearsay.authbench.task import load_task  # noqa: E402

DIR = ROOT / "dataset" / "authoring" / "summary_probes"
REVIEW = DIR / "review"
MEETING_TASKS = [s.task_id for s in SPECS if s.family == "meeting"]


def load(task_id: str) -> dict:
    return json.loads((DIR / f"{task_id}.json").read_text(encoding="utf-8"))


def cmd_init() -> None:
    DIR.mkdir(parents=True, exist_ok=True)
    for task_id in MEETING_TASKS:
        path = DIR / f"{task_id}.json"
        if path.exists() and any(load(task_id).get(f) for f in summary_probes.FIELDS_TO_WRITE):
            print(f"keep {path.name} (already being written)")
            continue
        task = load_task(task_id)
        official, after = transcript_lines(task.bundle)
        t = summary_probes.template(task_id, _meeting(task.bundle)["topic"], task.instruction, official, after)
        path.write_text(json.dumps(t, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


def cmd_check() -> int:
    bad = 0
    for task_id in MEETING_TASKS:
        issues = summary_probes.problems(load(task_id))
        bad += bool(issues)
        print(f"{task_id}: {'ok' if not issues else '; '.join(issues)}")
    return 1 if bad else 0


def cmd_review_sheets() -> int:
    if cmd_check():
        print("fill every template first")
        return 1
    rows, key = summary_probes.review_sheets([load(t) for t in MEETING_TASKS],
                                             {t: dataset.load_inputs(t)["trusted_context"] for t in MEETING_TASKS})
    REVIEW.mkdir(parents=True, exist_ok=True)
    for reviewer in (1, 2):
        with open(REVIEW / f"reviewer_{reviewer}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    (REVIEW / "key.json").write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")
    print(f"{len(rows)} items -> {REVIEW.relative_to(ROOT)}; give each reviewer only their sheet, never key.json")
    return 0


def cmd_agreement() -> int:
    sheets = []
    for reviewer in (1, 2):
        with open(REVIEW / f"reviewer_{reviewer}.csv", encoding="utf-8") as f:
            sheets.append({r["item_id"]: r["label"].strip() for r in csv.DictReader(f)})
    for i, s in enumerate(sheets, start=1):
        wrong = [k for k, v in s.items() if v not in summary_probes.REVIEW_LABELS]
        if wrong:
            print(f"reviewer {i}: missing or unknown labels for {wrong}")
            return 1
    key = json.loads((REVIEW / "key.json").read_text(encoding="utf-8"))
    intended = {k: "aligned" if v["version"] == "aligned" else "not_aligned" for k, v in key.items()}
    out = {"between_reviewers": summary_probes.agreement(*sheets),
           "reviewer_1_vs_intended": summary_probes.agreement(sheets[0], intended),
           "reviewer_2_vs_intended": summary_probes.agreement(sheets[1], intended)}
    (REVIEW / "agreement.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("init", "check", "review-sheets", "agreement"))
    a = ap.parse_args()
    return {"init": lambda: cmd_init() or 0, "check": cmd_check, "review-sheets": cmd_review_sheets,
            "agreement": cmd_agreement}[a.command]()


if __name__ == "__main__":
    sys.exit(main())
