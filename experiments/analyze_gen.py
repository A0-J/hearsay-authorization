"""Case-level analysis of a generalization run (docs/GENERALIZATION_PREREG.md, primary G1 and G2). Committed before
any generalization call; tables only. (The full Experiment 1 analysis of the same run is analyze_exp1.py.)

    python experiments/analyze_gen.py results/G1-gpt-4.1-run1

G1: the negative claim's effect on valid evidence under evidence-aware (Experiment 1's H5 contrast: per task, the
mean over the 4 valid conditions of approval(negative) - approval(none)). G2: positive claims on invalid evidence
under evidence-aware (H1: per task, the mean over the 8 invalid conditions of mean(approval(positive claims)) -
approval(none)). The unit of independence is the case: a case's value is the mean of its tasks' values. Holm over
G1 and G2. The same quantities over tasks, and per reporting group, are secondary.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

from analyze_exp2 import holm, stat
from common import ROOT

VALID = ("direct", "derived", "scope", "combined")
INVALID = ("abs_list", "abs_complete", "direct_revoked", "direct_expired", "derived_revoked", "derived_expired",
           "scope", "combined")
POS = ("unverified", "bare", "verified", "specific")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", type=Path)
    a = ap.parse_args()
    run = a.run.resolve()
    cfg = json.loads((run / "manifest.json").read_text(encoding="utf-8"))["config"]
    man = json.loads((ROOT / "dataset" / cfg["dataset_dir"] / "manifest.json").read_text(encoding="utf-8"))
    case_of, group_of = man["case_of_task"], man["group_of_task"]
    acc = defaultdict(list)
    for x in (run / "verdicts.jsonl").read_text(encoding="utf-8").splitlines():
        v = json.loads(x)
        if v["arm"] == "main" and v["instruction"] == "aware":
            acc[(v["task_id"], v["side"], v["condition"], v["claim"])].append(v["approve"])
    r = {k: mean(x) for k, x in acc.items()}
    tasks = sorted(case_of)

    def g1(t):
        return mean(r[(t, "valid", c, "negative")] - r[(t, "valid", c, "none")] for c in VALID)

    def g2(t):
        return mean(mean(r[(t, "invalid", c, k)] for k in POS) - r[(t, "invalid", c, "none")] for c in INVALID)

    def by_case(fn, subset):
        cases = defaultdict(list)
        for t in subset:
            cases[case_of[t]].append(fn(t))
        return [mean(v) for _, v in sorted(cases.items())]

    out = {"primary_case_level": {"G1_negative_claim_valid_aware": stat(by_case(g1, tasks)),
                                  "G2_positive_claims_invalid_aware": stat(by_case(g2, tasks))}}
    hp = holm({k: v["p_signflip"] for k, v in out["primary_case_level"].items()})
    for k in hp:
        out["primary_case_level"][k]["p_holm"] = hp[k]
    out["task_level"] = {"G1": stat([g1(t) for t in tasks]), "G2": stat([g2(t) for t in tasks])}
    out["by_group_case_level"] = {}
    for grp in sorted(set(group_of.values())):
        sub = [t for t in tasks if group_of[t] == grp]
        out["by_group_case_level"][grp] = {"n_tasks": len(sub), "G1": stat(by_case(g1, sub)),
                                           "G2": stat(by_case(g2, sub))}
    out["per_task"] = {t: {"case": case_of[t], "group": group_of[t], "G1": round(g1(t), 4), "G2": round(g2(t), 4)}
                       for t in tasks}
    dest = run / "analysis"
    dest.mkdir(exist_ok=True)
    (dest / "generalization_tests.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    lines = [f"# Generalization (case level): `{run.name}`", "", "Pre-registration: docs/GENERALIZATION_PREREG.md. "
             f"{len(tasks)} tasks in {len(set(case_of.values()))} cases. Tables only.", "",
             "| level | test | estimate | 95% CI | p (sign-flip) | p (Holm) | n |", "|---|---|---|---|---|---|---|"]
    for k, s in out["primary_case_level"].items():
        lines.append(f"| case | {k} | {s['estimate']:+.4f} | [{s['ci95'][0]:+.4f}, {s['ci95'][1]:+.4f}] | "
                     f"{s['p_signflip']:.4f} | {s['p_holm']:.4f} | {s['n_tasks']} cases |")
    for k, s in out["task_level"].items():
        lines.append(f"| task | {k} | {s['estimate']:+.4f} | [{s['ci95'][0]:+.4f}, {s['ci95'][1]:+.4f}] | "
                     f"{s['p_signflip']:.4f} | | {s['n_tasks']} tasks |")
    for grp, d in out["by_group_case_level"].items():
        for k in ("G1", "G2"):
            s = d[k]
            lines.append(f"| case, {grp} | {k} | {s['estimate']:+.4f} | [{s['ci95'][0]:+.4f}, {s['ci95'][1]:+.4f}] | "
                         f"{s['p_signflip']:.4f} | | {s['n_tasks']} cases |")
    (dest / "GENERALIZATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"-> {dest}")


if __name__ == "__main__":
    main()
