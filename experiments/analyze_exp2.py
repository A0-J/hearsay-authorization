"""Analyse an Experiment 2 run (docs/EXPERIMENT2_PREREG.md) or a DEFER-arm run (docs/EXPERIMENT2_DEFER_PREREG.md).
Committed before any Experiment 2 data; tables only, no interpretation.

    python experiments/analyze_exp2.py results/E2-gpt-4.1-run1
    python experiments/analyze_exp2.py results/E2-claude-sonnet-5-5-nothink-run1 --compare results/E2-claude-sonnet-5-5-run1
    python experiments/analyze_exp2.py results/E2D-gpt-4.1-run1          # DEFER arm (dataset exp2_defer*)

Unit = task. A cell's rate is the mean over its repeats; a pooled quantity is the unweighted mean of its cells'
rates within a task; a contrast is a per-task difference, its estimate the mean over tasks, its 95% interval a
bootstrap over tasks (10,000 resamples, seed 0), its p-value a sign-flip permutation test over tasks (exact for up to
16 tasks, otherwise 100,000 random sign vectors, seed 0). Holm within the primary family {P1, P2} and within the
secondary family {S1..S6}. An unparseable reply counts as not approving and is reported.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from common import ROOT

CLAIM_WORDS = ("supervisor", "upstream", "planning agent", "context note", "claim", "report")   # pre-registered


def stat(values: list[float], n_boot: int = 10000, seed: int = 0) -> dict:
    n = len(values)
    if n == 0:
        return {"estimate": None, "ci95": [None, None], "p_signflip": None, "n_tasks": 0, "per_task": []}
    est = mean(values)
    rng = random.Random(seed)
    boots = sorted(mean(rng.choices(values, k=n)) for _ in range(n_boot))
    obs = abs(est) - 1e-12
    if all(abs(v) < 1e-12 for v in values):
        p = 1.0
    elif n <= 16:
        p = sum(1 for s in itertools.product((1, -1), repeat=n)
                if abs(sum(a * v for a, v in zip(s, values)) / n) >= obs) / 2 ** n
    else:
        rs = random.Random(seed)
        hits = sum(1 for _ in range(100000)
                   if abs(sum(v if rs.random() < 0.5 else -v for v in values) / n) >= obs)
        p = (hits + 1) / 100001
    return {"estimate": round(est, 4), "ci95": [round(boots[int(0.025 * n_boot)], 4),
                                                round(boots[int(0.975 * n_boot) - 1], 4)],
            "p_signflip": round(p, 5), "n_tasks": n, "per_task": [round(v, 4) for v in values]}


def holm(ps: dict[str, float]) -> dict[str, float]:
    order = sorted(ps, key=ps.get)
    out, running = {}, 0.0
    for i, k in enumerate(order):
        running = max(running, min(1.0, ps[k] * (len(order) - i)))
        out[k] = round(running, 5)
    return out


def load(run: Path):
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    data = ROOT / "dataset" / manifest["config"].get("dataset_dir", "exp1")
    verdicts = [json.loads(x) for x in (run / "verdicts.jsonl").read_text(encoding="utf-8").splitlines()]
    labels, cells = {}, {}
    for d in sorted((data / "tasks").iterdir()):
        for x in (d / "labels.jsonl").read_text(encoding="utf-8").splitlines():
            lab = json.loads(x)
            labels[lab["cell_id"]] = lab
        for x in (d / "cells.jsonl").read_text(encoding="utf-8").splitlines():
            c = json.loads(x)
            c.pop("input", None)
            cells[c["cell_id"]] = c
    return manifest, verdicts, labels, cells


def cell_rates(verdicts, key="approve"):
    acc = defaultdict(list)
    for v in verdicts:
        acc[v["cell_id"]].append(v[key] if key == "approve" else v.get("decision") == key)
    return {k: mean(x) for k, x in acc.items()}


class Cells:
    """Pooled rates per task over the cells that match a filter."""

    def __init__(self, cells, rates):
        self.cells, self.rates = cells, rates
        self.tasks = sorted({c["task_id"] for c in cells.values()})

    def r(self, task, **f) -> float | None:
        xs = [self.rates[k] for k, c in self.cells.items()
              if c["task_id"] == task and k in self.rates and all(c.get(a) == b for a, b in f.items())]
        return mean(xs) if xs else None

    def contrast(self, fn) -> dict:
        vals = [fn(t) for t in self.tasks]
        return stat([v for v in vals if v is not None])


def exp2_tests(C: Cells) -> dict:
    B = dict(block="B", instruction="aware", policy="base")

    def p1(t):
        diffs = [C.r(t, block="A", instruction="aware", side="valid", condition=k, claim="negative")
                 - C.r(t, block="A", instruction="aware", side="valid", condition=k, claim="none")
                 for k in ("direct", "derived", "scope", "combined")]
        return mean(diffs)

    def vw(t, **f):                       # valid side, withdrawal claim
        return C.r(t, side="valid", claim="withdrawn", **f)

    tests = {
        "P1_negative_claim_valid_blockA_aware": C.contrast(p1),
        "P2_before_minus_after_valid_withdrawn_base_aware": C.contrast(
            lambda t: vw(t, timing="before", **B) - vw(t, timing="after", **B)),
    }
    sec = {
        "S1_asymmetry_withdrawal_drop_minus_approval_rise_unspecified": C.contrast(
            lambda t: (C.r(t, side="valid", claim="none", **B) - vw(t, timing="unspecified", **B))
            - (C.r(t, side="invalid", claim="approved", timing="unspecified", **B)
               - C.r(t, side="invalid", claim="none", **B))),
        "S2_before_minus_unspecified": C.contrast(
            lambda t: vw(t, timing="before", **B) - vw(t, timing="unspecified", **B)),
        "S3_supervisor_minus_upstream_agent": C.contrast(
            lambda t: vw(t, source="supervisor", **B) - vw(t, source="upstream_agent", **B)),
        "S4_record_authority_minus_base_unspecified": C.contrast(
            lambda t: vw(t, block="B", instruction="aware", policy="record_authority", timing="unspecified")
            - vw(t, timing="unspecified", **B)),
        "S5_explicit_minus_aware_unspecified": C.contrast(
            lambda t: vw(t, block="B", instruction="explicit", policy="base", timing="unspecified")
            - vw(t, timing="unspecified", **B)),
        "S6_record_authority_before_minus_after": C.contrast(
            lambda t: vw(t, block="B", instruction="aware", policy="record_authority", timing="before")
            - vw(t, block="B", instruction="aware", policy="record_authority", timing="after")),
    }
    hp = holm({k: v["p_signflip"] for k, v in tests.items()})
    hs = holm({k: v["p_signflip"] for k, v in sec.items()})
    for k in tests:
        tests[k]["p_holm"] = hp[k]
    for k in sec:
        sec[k]["p_holm"] = hs[k]
    return {"primary": tests, "secondary": sec}


def summary_rows(C: Cells, labels, fields):
    """Mean over tasks of each cell type's approval rate (cell type = the fields, task left out)."""
    groups = defaultdict(lambda: defaultdict(list))
    for k, c in C.cells.items():
        if k in C.rates:
            groups[tuple(c.get(f) for f in fields)][c["task_id"]].append(C.rates[k])
    rows = []
    for g, per in sorted(groups.items(), key=lambda x: [str(v) for v in x[0]]):
        vals = [mean(v) for v in per.values()]
        norm = {labels[k]["normative"] for k, c in C.cells.items() if tuple(c.get(f) for f in fields) == g}
        rows.append({**dict(zip(fields, g)), "approval_mean_over_tasks": round(mean(vals), 4), "n_tasks": len(vals),
                     "normative": "/".join(sorted(str(n) for n in norm))})
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", type=Path)
    ap.add_argument("--compare", type=Path, help="another run on the same dataset (e.g. the other thinking setting)")
    a = ap.parse_args()
    run = a.run.resolve()
    manifest, verdicts, labels, cells = load(run)
    out = run / "analysis"
    out.mkdir(exist_ok=True)
    defer = manifest["config"].get("dataset_dir", "").startswith("exp2_defer")
    served = Counter(v.get("served_model") for v in verdicts)
    parse_errors = sum(1 for v in verdicts if v.get("parse_error"))
    stops = Counter(str(v.get("stop_reason")) for v in verdicts)
    use = {"calls": len(verdicts), "input_tokens": sum(v["usage"].get("input_tokens", 0) for v in verdicts),
           "output_tokens": sum(v["usage"].get("output_tokens", 0) for v in verdicts),
           "parse_errors": parse_errors, "served_models": dict(served), "stop_reasons": dict(stops)}
    (out / "usage.json").write_text(json.dumps(use, indent=2) + "\n", encoding="utf-8")

    # errors against the normative decision, where one exists
    errors = []
    for v in verdicts:
        norm = labels[v["cell_id"]].get("normative")
        if norm is not None and v.get("decision") != norm:
            c = cells[v["cell_id"]]
            errors.append({"cell_id": v["cell_id"], "repeat": v["repeat"], "normative": norm,
                           "decision": v.get("decision"), "basis": v.get("basis"), "reason": v.get("reason"),
                           "parse_error": v.get("parse_error"), "cites_claim": any(
                               w in str(v.get("reason", "")).lower() for w in CLAIM_WORDS),
                           **{f: c.get(f) for f in ("block", "instruction", "policy", "side", "condition", "claim",
                                                    "timing", "source")}})
    (out / "errors.jsonl").write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in errors),
                                      encoding="utf-8")
    fields = ("block", "instruction", "policy", "side", "condition", "claim", "timing", "source")
    lines = [f"# {'DEFER arm' if defer else 'Experiment 2'}: results", "",
             f"Run: `{run.name}`. Pre-registration: {manifest.get('dataset', {}).get('prereg')}. Tables only.", "",
             f"Calls {use['calls']}; input tokens {use['input_tokens']}; output tokens {use['output_tokens']}; "
             f"parse errors {parse_errors}; served models {dict(served)}; stop reasons {dict(stops)}.", "",
             f"Tasks (n = {len({c['task_id'] for c in cells.values()})}). Decisions that differ from a normative "
             f"label: {len(errors)} (errors.jsonl).", ""]
    if defer:
        rows = []
        for dec in ("approve", "reject", "defer"):
            C = Cells(cells, cell_rates(verdicts, dec))
            for r in summary_rows(C, labels, ("instruction", "condition", "claim")):
                rows.append({"decision": dec, **r})
        write_csv(out / "decision_rates.csv", rows)
        lines += ["## Decision rates (mean over tasks)", "", "| instruction | evidence state | claim | normative | "
                  "approve | reject | defer |", "|---|---|---|---|---|---|---|"]
        key = defaultdict(dict)
        for r in rows:
            key[(r["instruction"], r["condition"], r["claim"], r["normative"])][r["decision"]] = r[
                "approval_mean_over_tasks"]
        for (i, s, c, n), d in key.items():
            lines.append(f"| {i} | {s} | {c} | {n} | {d.get('approve', 0):.3f} | {d.get('reject', 0):.3f} | "
                         f"{d.get('defer', 0):.3f} |")
        (out / "tests.json").write_text("{}\n", encoding="utf-8")
    else:
        C = Cells(cells, cell_rates(verdicts))
        tests = exp2_tests(C)
        (out / "tests.json").write_text(json.dumps(tests, indent=2) + "\n", encoding="utf-8")
        rows = summary_rows(C, labels, fields)
        write_csv(out / "cell_summary.csv", rows)
        lines += ["## Pre-registered tests (unit = task)", "", "| family | test | estimate | 95% CI | p (sign-flip) | "
                  "p (Holm) |", "|---|---|---|---|---|---|"]
        for fam in ("primary", "secondary"):
            for k, s in tests[fam].items():
                lines.append(f"| {fam} | {k} | {s['estimate']:+.4f} | [{s['ci95'][0]:+.4f}, {s['ci95'][1]:+.4f}] | "
                             f"{s['p_signflip']:.4f} | {s['p_holm']:.4f} |")
        lines += ["", "## Approval rate by cell type (mean over tasks)", "",
                  "| " + " | ".join(fields) + " | normative | approval |", "|" + "---|" * (len(fields) + 2)]
        lines += ["| " + " | ".join(str(r[f]) for f in fields) + f" | {r['normative']} | "
                  f"{r['approval_mean_over_tasks']:.3f} |" for r in rows]
        if a.compare:
            m2, v2, l2, c2 = load(a.compare.resolve())
            C2 = Cells(c2, cell_rates(v2))
            t2 = exp2_tests(C2)
            cmp = {}
            for k in ("P1_negative_claim_valid_blockA_aware", "P2_before_minus_after_valid_withdrawn_base_aware"):
                x, y = tests["primary"][k]["per_task"], t2["primary"][k]["per_task"]
                cmp[k] = stat([b - a_ for a_, b in zip(x, y)]) if len(x) == len(y) else None
            (out / f"compare_{a.compare.name}.json").write_text(json.dumps(cmp, indent=2) + "\n", encoding="utf-8")
            lines += ["", f"## Comparison with `{a.compare.name}` (per-task contrast there minus here)", ""]
            lines += [f"- {k}: {v['estimate']:+.4f} [{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}], p {v['p_signflip']}"
                      for k, v in cmp.items() if v]
    cites = [v for v in verdicts if cells[v["cell_id"]].get("claim") not in ("none", None)]
    lines += ["", f"Replies under a claim whose reason contains a claim word {CLAIM_WORDS}: "
              f"{sum(1 for v in cites if any(w in str(v.get('reason', '')).lower() for w in CLAIM_WORDS))}"
              f" of {len(cites)}.", ""]
    (out / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"-> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
