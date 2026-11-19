"""Analysis of the escalation follow-up (SIGX; docs/SIGX_ESCALATION_PREREG_DRAFT.md). Exploratory throughout.

    python experiments/analyze_sigx.py --run SIGX-gpt-4o-run1

Unit: the task (11); within-task (paired) differences; estimates are means over tasks with a bootstrap 95% interval
(10,000 resamples, seed 0) and an exact two-sided sign-flip p (analyze_exp1.stat). A parse failure counts as not
approving (sensitivity: dropped). The outcome is the verifier's decision; nothing is executed.

  F(arm)  forged-ID acceptance without a covering record: mean over abs_list, abs_complete of approval(specific)

  X1 F(signed) - F(plain)                      X2 F(signed_claim_unproven) - F(signed)
  X3 F(signed_claim_label) - F(signed)         X4 F(signed_claim_unproven) - F(signed_claim_label)
Holm across X1-X4 is shown for reference; every result is exploratory (the model and the conditions were chosen from
Experiment 1's results). The plain cells are reported next to Experiment 1's gpt-4o values (E1P-gpt-4o-run1).
"""

from __future__ import annotations

import argparse
import csv
import json
from statistics import mean

from analyze_exp1 import holm, stat
from analyze_sig import load, rates
from common import RESULTS

CONDITIONS = ("abs_list", "abs_complete")
ARMS = ("plain", "signed", "signed_claim_unproven", "signed_claim_label")
CONTRASTS = {"X1": ("signed", "plain"), "X2": ("signed_claim_unproven", "signed"),
             "X3": ("signed_claim_label", "signed"), "X4": ("signed_claim_unproven", "signed_claim_label")}
E1_RUN = "E1P-gpt-4o-run1"


def per_task(R: dict, tasks: list[str], arm: str, claim: str) -> dict[str, float]:
    return {t: mean(R[(t, arm, "aware", "invalid", c, claim)] for c in CONDITIONS) for t in tasks}


def tests(R: dict, tasks: list[str]) -> dict:
    out = {}
    for name, (a, b) in CONTRASTS.items():
        fa, fb = per_task(R, tasks, a, "specific"), per_task(R, tasks, b, "specific")
        out[name] = {"contrast": f"F({a}) - F({b})", **stat([fa[t] - fb[t] for t in tasks])}
    for k, p in holm({k: v["p_signflip"] for k, v in out.items()}).items():
        out[k]["p_holm"] = p
    return out


def e1_reference() -> dict:
    path = RESULTS / E1_RUN / "analysis" / "cell_summary.csv"
    if not path.exists():
        return {}
    return {f"{r['condition']}/{r['claim']}": float(r["mean_approval_over_tasks"])
            for r in csv.DictReader(path.open(encoding="utf-8"))
            if r["arm"] == "main" and r["instruction"] == "aware" and r["side"] == "invalid"
            and r["condition"] in CONDITIONS and r["claim"] in ("none", "specific")}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    verdicts = load(a.run)
    tasks = sorted({v["task_id"] for v in verdicts})
    R, Rd = rates(verdicts), rates(verdicts, drop_parse_errors=True)
    cells = {f"{arm}/{c}/{k}": mean(R[(t, arm, "aware", "invalid", c, k)] for t in tasks)
             for arm in ARMS for c in CONDITIONS for k in ("none", "specific")}
    res = {"tasks": len(tasks), "calls": len(verdicts), "status": "exploratory",
           "parse_errors": {arm: sum(1 for v in verdicts if v.get("parse_error") and v["presentation"] == arm)
                            for arm in ARMS},
           "F": {arm: stat(list(per_task(R, tasks, arm, "specific").values())) for arm in ARMS},
           "cells": cells, "e1_reference_plain": e1_reference(),
           "tests": tests(R, tasks), "tests_without_parse_errors": tests(Rd, tasks)}
    out = RESULTS / a.run / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [f"# Escalation follow-up (exploratory): {a.run}", "",
             "No covering record; the task message cites a forged approval id. Per-task means over "
             f"{len(tasks)} tasks; bootstrap 95% CI; exact two-sided sign-flip p; Holm across X1-X4 for reference. "
             "Exploratory: model and conditions chosen from Experiment 1. Outcome: the verifier's decision.", "",
             "| arm | F (forged id accepted) | 95% CI | abs_list none | abs_list specific | abs_complete none "
             "| abs_complete specific |", "|---|---|---|---|---|---|---|"]
    for arm in ARMS:
        f = res["F"][arm]
        lines.append(f"| {arm} | {100 * f['estimate']:.1f} | [{100 * f['ci95'][0]:.1f}, {100 * f['ci95'][1]:.1f}] | "
                     + " | ".join(f"{100 * cells[f'{arm}/{c}/{k}']:.1f}" for c in CONDITIONS for k in ("none", "specific"))
                     + " |")
    ref = res["e1_reference_plain"]
    if ref:
        lines.append(f"| Experiment 1 ({E1_RUN}, plain) | | | "
                     + " | ".join(f"{100 * ref.get(f'{c}/{k}', float('nan')):.1f}" for c in CONDITIONS
                                  for k in ("none", "specific")) + " |")
    lines += ["", "| contrast | estimate | 95% CI | p | p (Holm, reference) |", "|---|---|---|---|---|"]
    for k, s in res["tests"].items():
        lines.append(f"| {k} {s['contrast']} | {100 * s['estimate']:+.1f} pp | [{100 * s['ci95'][0]:+.1f}, "
                     f"{100 * s['ci95'][1]:+.1f}] | {s['p_signflip']:.4f} | {s['p_holm']} |")
    lines += ["", f"Parse errors (counted as not approving): {res['parse_errors']}"]
    (out / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
