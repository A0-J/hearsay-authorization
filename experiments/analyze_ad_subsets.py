"""AgentDojo generalization: the primary analysis and the sensitivity analyses fixed in Amendment 3 item 4
(docs/GENERALIZATION_PREREG.md), computed from the per-task values that analyze_gen.py (Experiment 1 cells) and
analyze_exp2.py (Experiment 2 cells) already wrote. No API calls.

    python experiments/analyze_ad_subsets.py results/AD1-gpt-4.1-run1 results/AD2E-gpt-4.1-run1

One AgentDojo user task = one case. Sets:
    all20      every selected task (the rule before the audit; reported for transparency)
    primary    without Abank00 (19 cases); Holm over G1 and G2 (Experiment 1 cells), and over P1 and P2
    S-a        primary, with tasks of identical calls merged into one unit (Aslack02/11/16, Aslack09/10): 16 units
    S-b        primary without Abank06 and Atravel00 (17 cases)
    Abank00    reported alone
Writes <run>/analysis/AGENTDOJO_SUBSETS.md and agentdojo_subsets.json for each run given.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

from analyze_exp2 import holm, stat

MERGE = [("Aslack02", "Aslack11", "Aslack16"), ("Aslack09", "Aslack10")]
SETS = {"all20": dict(drop=(), merge=False), "primary": dict(drop=("Abank00",), merge=False),
        "S-a": dict(drop=("Abank00",), merge=True), "S-b": dict(drop=("Abank00", "Abank06", "Atravel00"), merge=False)}


def units(per_task: dict[str, float], drop, merge) -> list[float]:
    vals = {t: v for t, v in per_task.items() if t not in drop}
    if merge:
        for grp in MERGE:
            present = [t for t in grp if t in vals]
            if present:
                m = mean(vals.pop(t) for t in present)
                vals["+".join(present)] = m
    return [vals[k] for k in sorted(vals)]


def main() -> None:
    for run in map(lambda p: Path(p).resolve(), sys.argv[1:]):
        a = run / "analysis"
        if (a / "generalization_tests.json").exists():
            g = json.loads((a / "generalization_tests.json").read_text(encoding="utf-8"))["per_task"]
            tests = {"G1": {t: v["G1"] for t, v in g.items()}, "G2": {t: v["G2"] for t, v in g.items()}}
        else:
            tj = json.loads((a / "tests.json").read_text(encoding="utf-8"))
            tasks = sorted(json.loads((run / "manifest.json").read_text(encoding="utf-8"))["dataset"]["tasks"])
            tests = {}
            for fam in ("primary", "secondary"):
                for k, v in tj[fam].items():
                    assert len(v["per_task"]) == len(tasks), "per-task values follow the sorted task list"
                    tests[k] = dict(zip(tasks, v["per_task"]))
        out = {}
        for sname, s in SETS.items():
            out[sname] = {k: stat(units(pt, s["drop"], s["merge"])) for k, pt in tests.items()}
            prim = [k for k in out[sname] if k in ("G1", "G2") or k.startswith(("P1_", "P2_"))]
            hp = holm({k: out[sname][k]["p_signflip"] for k in prim if out[sname][k]["p_signflip"] is not None})
            for k, p in hp.items():
                out[sname][k]["p_holm_primary_pair"] = p
        out["Abank00_alone"] = {k: pt.get("Abank00") for k, pt in tests.items()}
        (a / "agentdojo_subsets.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        md = [f"# AgentDojo: primary and sensitivity analyses (`{run.name}`)", "",
              "Amendment 3 item 4 of docs/GENERALIZATION_PREREG.md. Unit = case (one AgentDojo user task). Holm over "
              "the primary pair (G1, G2 or P1, P2) within each set.", "",
              "| set | test | estimate | 95% CI | p (sign-flip) | p (Holm, primary pair) | units |", "|---|---|---|---|---|---|---|"]
        for sname in SETS:
            for k, v in out[sname].items():
                ph = v.get("p_holm_primary_pair")
                md.append(f"| {sname} | {k} | {v['estimate']:+.4f} | [{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}] | "
                          f"{v['p_signflip']} | {'' if ph is None else ph} | {v['n_tasks']} |")
        md += ["", "Abank00 alone: " + ", ".join(f"{k} {v:+.4f}" for k, v in out["Abank00_alone"].items()
                                                 if v is not None)]
        (a / "AGENTDOJO_SUBSETS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print("\n".join(md))


if __name__ == "__main__":
    main()
