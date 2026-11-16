"""The verification-method ablation (docs/ABLATION_PREREG.md) on Experiment 1's cells. Committed before any
ablation data; tables only.

    python experiments/analyze_ablation.py --e1 results/E1-gpt-4.1-run1 --claim-only results/AB-claim-only-gpt-4.1-run1 \
        --semantic results/AB-semantic-gpt-4.1-run1 --out results/ablation-gpt-4.1

Methods, each judged on the same Experiment 1 main-arm cells (11 tasks x 52 cells x 3 repeats per instruction):
  claim_only      LLM; the task message and the policy, no evidence (dataset ablation_claim_only)
  aware           LLM; Experiment 1's evidence-aware run
  explicit        LLM; Experiment 1's evidence-explicit run
  gate            the provenance gate (labels' gate_allowed): the labels' own definition, a reference by construction
  semantic_gate   LLM semantic check (3 votes, approve only on an "aligned" majority) AND the gate
Repeat r of a cell uses repeat r of claim_only and votes 3r..3r+2 of semantic. Methods that do not read the
instruction (claim_only, gate, semantic_gate) are counted once per cell (the evidence-aware copy).
Unit = task; statistics as in analyze_exp2.py; Holm over A1-A3.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from analyze_exp2 import holm, stat, write_csv
from common import ROOT

POSITIVE = ("unverified", "bare", "verified", "specific")
METHODS = ("claim_only", "aware", "explicit", "gate", "semantic_gate")


def verdicts(run: Path) -> tuple[dict, list[dict]]:
    m = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    return m, [json.loads(x) for x in (run / "verdicts.jsonl").read_text(encoding="utf-8").splitlines()]


def claim_only_key(cell: dict) -> str:
    target = "control" if cell["side"] == "control" else "call"
    if cell["claim"] == "specific":
        return f"{target}/specific_{'0419' if cell['condition'] == 'combined' else '0417'}"
    return f"{target}/{cell['claim']}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--e1", type=Path, required=True)
    ap.add_argument("--claim-only", type=Path, required=True)
    ap.add_argument("--semantic", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    m1, e1 = verdicts(a.e1)
    _, co = verdicts(a.claim_only)
    _, se = verdicts(a.semantic)
    data = ROOT / "dataset" / m1["config"].get("dataset_dir", "exp1")
    cells, labels = {}, {}
    for d in sorted((data / "tasks").iterdir()):
        for x in (d / "cells.jsonl").read_text(encoding="utf-8").splitlines():
            c = json.loads(x)
            if c["arm"] == "main":
                c.pop("input")
                cells[c["cell_id"]] = c
        for x in (d / "labels.jsonl").read_text(encoding="utf-8").splitlines():
            lab = json.loads(x)
            labels[lab["cell_id"]] = lab

    e1_dec = {(v["cell_id"], v["repeat"]): v["approve"] for v in e1 if v["cell_id"] in cells}
    co_dec = {(v["task_id"], v["cell_id"].split("/claim_only/")[1], v["repeat"]): v["approve"] for v in co}
    votes = defaultdict(dict)
    for v in se:
        votes[(v["task_id"], v["cell_id"].rsplit("/", 1)[1])][v["repeat"]] = v.get("decision")
    repeats = sorted({r for _, r in e1_dec})

    rows = []          # one per (method, cell, repeat)
    for cid, c in cells.items():
        gate = labels[cid]["gate_allowed"]
        target = "control" if c["side"] == "control" else "call"
        for r in repeats:
            dec = {}
            if c["instruction"] in ("aware", "explicit"):
                dec[c["instruction"]] = e1_dec.get((cid, r))
            if c["instruction"] == "aware":
                dec["claim_only"] = co_dec.get((c["task_id"], claim_only_key(c), r))
                dec["gate"] = gate
                vs = [votes[(c["task_id"], target)].get(i) for i in range(3 * r, 3 * r + 3)]
                dec["semantic_gate"] = (None if any(x is None for x in vs)
                                        else gate and Counter(vs)["aligned"] >= 2)
            for meth, ok in dec.items():
                if ok is not None:
                    rows.append({"method": meth, "task_id": c["task_id"], "side": c["side"],
                                 "condition": c["condition"], "claim": c["claim"], "repeat": r, "approve": bool(ok)})

    def per_task(meth, side, claims=None):
        acc = defaultdict(list)
        for x in rows:
            if x["method"] == meth and x["side"] == side and (claims is None or x["claim"] in claims):
                acc[x["task_id"]].append(x["approve"])
        return {t: mean(v) for t, v in acc.items()}

    def diff(m_a, m_b, side, claims, reject=False):
        pa, pb = per_task(m_a, side, claims), per_task(m_b, side, claims)
        ts = sorted(set(pa) & set(pb))
        sgn = -1 if reject else 1
        return stat([sgn * (pa[t] - pb[t]) for t in ts])

    def fr_both(meth):
        acc = defaultdict(list)
        for x in rows:
            if x["method"] == meth and x["side"] in ("valid", "control"):
                acc[x["task_id"]].append(not x["approve"])
        return {t: mean(v) for t, v in acc.items()}

    sg, ex = fr_both("semantic_gate"), fr_both("explicit")
    tests = {
        "A1_unauthorized_approval_positive_claims_claim_only_minus_aware": diff("claim_only", "aware", "invalid", POSITIVE),
        "A2_false_rejection_negative_claim_aware_minus_explicit": diff("aware", "explicit", "valid", ("negative",),
                                                                       reject=True),
        "A3_false_rejection_valid_and_control_semantic_gate_minus_explicit": stat(
            [sg[t] - ex[t] for t in sorted(set(sg) & set(ex))]),
    }
    hp = holm({k: v["p_signflip"] for k, v in tests.items()})
    for k in tests:
        tests[k]["p_holm"] = hp[k]

    table = []
    for meth in METHODS:
        for side, measure in (("invalid", "unauthorized_approval"), ("valid", "false_rejection"),
                              ("control", "false_rejection")):
            claims = sorted({x["claim"] for x in rows if x["side"] == side})
            for claim in ["(all)"] + claims:
                pt = per_task(meth, side, None if claim == "(all)" else (claim,))
                if not pt:
                    continue
                vals = [v if side == "invalid" else 1 - v for v in pt.values()]
                s = stat(vals)
                table.append({"method": meth, "side": side, "measure": measure, "claim": claim,
                              "rate_mean_over_tasks": s["estimate"], "ci95_low": s["ci95"][0],
                              "ci95_high": s["ci95"][1], "n_tasks": s["n_tasks"],
                              "note": "reference by construction (defines the labels)" if meth == "gate" else ""})
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "method_table.csv", table)
    (out / "tests.json").write_text(json.dumps(tests, indent=2) + "\n", encoding="utf-8")
    missing = {m: sum(1 for x in rows if x["method"] == m) for m in METHODS}
    lines = ["# Verification-method ablation: results", "",
             f"E1 run `{a.e1.name}`, claim-only run `{a.claim_only.name}`, semantic run `{a.semantic.name}`. "
             "Pre-registration: docs/ABLATION_PREREG.md. Tables only.", "",
             f"Decisions per method: {missing}.", "", "## Pre-registered comparisons (unit = task, Holm over A1-A3)",
             "", "| test | estimate | 95% CI | p (sign-flip) | p (Holm) |", "|---|---|---|---|---|"]
    lines += [f"| {k} | {s['estimate']:+.4f} | [{s['ci95'][0]:+.4f}, {s['ci95'][1]:+.4f}] | {s['p_signflip']:.4f} | "
              f"{s['p_holm']:.4f} |" for k, s in tests.items()]
    lines += ["", "## Rates per method (mean over tasks; the gate is the labels' definition)", "",
              "| method | side | measure | claim | rate | 95% CI |", "|---|---|---|---|---|---|"]
    lines += [f"| {r['method']} | {r['side']} | {r['measure']} | {r['claim']} | {r['rate_mean_over_tasks']:.3f} | "
              f"[{r['ci95_low']:.3f}, {r['ci95_high']:.3f}] |" for r in table]
    sem = Counter(v.get("decision") for v in se)
    lines += ["", f"Semantic votes: {dict(sem)}; claim-only parse errors: {sum(1 for v in co if v.get('parse_error'))}.", ""]
    (out / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
