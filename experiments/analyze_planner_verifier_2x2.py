"""Analyze a finished PV2X2 run without API calls.

Outputs episodes.csv, method_summary.csv, paired_tests.csv and REPORT.md.
Incomplete arms are reported explicitly. No p-value is reported unless all 4 methods are
observed for each task x side x claim x repeat.

Statistics are the project's (analyze_exp1.stat): bootstrap over cases, 10,000 resamples, seed 0;
paired sign-flip test, exact up to 16 cases, otherwise 100,000 random sign vectors (seed 0).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analyze_exp1 import stat
from common import RESULTS
from e2e_task_check import task_success, violation

METHODS = ("M0", "M1", "M2", "M3")
METRICS = ("gated_attempted", "pre_verifier_no_gated_attempt", "no_verifier_proposal", "L3_task_success",
           "unauthorized_execution", "V_violation", "other_unauthorized_change", "claim_propagated")


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def case_stat(deltas):
    """analyze_exp1.stat on case-level deltas; None when there are no cases."""
    return stat(deltas) if deltas else None


def rows_from_run(run_dir):
    rows = []
    errors = []
    for p in sorted((run_dir / "episodes").rglob("measures.json")):
        m = json.loads(p.read_text(encoding="utf-8"))
        if m.get("error"):
            errors.append((str(p), m["error"]))
            continue
        efile = p.with_name("episode.json")
        if not efile.is_file():
            errors.append((str(p), "missing episode.json"))
            continue
        ep = json.loads(efile.read_text(encoding="utf-8"))
        taskid = m["task_id"]
        row = {key: m.get(key) for key in ("task_id", "case", "side", "claim", "method", "repeat",
                                           "gated_attempted", "gated_executed", "unauthorized_execution",
                                           "other_unauthorized_change", "false_rejection", "safe_completion",
                                           "blocked", "n_proposals", "turns", "no_verifier_proposal",
                                           "claim_propagated")}
        row.update(pre_verifier_no_gated_attempt=not m["gated_attempted"],
                   L3_task_success=task_success(taskid, ep), V_violation=violation(taskid, ep))
        rows.append(row)
    return rows, errors


def write_csv(path, rows, headers):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def summarize(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r["side"], r["claim"], r["method"])].append(r)
    out = []
    for (side, claim, method), rs in sorted(groups.items()):
        item = {"side": side, "claim": claim, "method": method, "episodes": len(rs),
                "cases": len({r["case"] for r in rs})}
        for m in METRICS:
            vals = [int(r[m]) for r in rs if r[m] is not None]
            item[m + "_n"] = len(vals)
            item[m + "_rate"] = mean(vals)
        out.append(item)
    return out


def paired_tests(rows, side="valid", claim="withdrawn", expected_pairs=None):
    """Pair treatments on (task, repeat); average differences by case BEFORE testing."""
    relevant = [r for r in rows if r["side"] == side and r["claim"] == claim]
    cells = defaultdict(dict)
    cases = {}
    for r in relevant:
        key = (r["task_id"], int(r["repeat"]))
        if r["method"] in cells[key]:
            raise ValueError(f"duplicate episode: {key} {r['method']}")
        cells[key][r["method"]] = r
        cases[key] = r["case"]
    complete = {k: v for k, v in cells.items() if set(v) == set(METHODS)}
    n_incomplete = (expected_pairs if expected_pairs is not None else len(cells)) - len(complete)
    if n_incomplete < 0:
        raise ValueError("more matched pairs than expected; inspect duplicate task/repeat IDs")
    pairs = [("M3_vs_M1", "M3", "M1"), ("M2_vs_M0", "M2", "M0"),
             ("M1_vs_M0", "M1", "M0"), ("M3_vs_M2", "M3", "M2")]
    results = []
    for metric in METRICS:
        for label, a, b in pairs:
            bycase = defaultdict(list)
            for k, arms in complete.items():
                if arms[a][metric] is None or arms[b][metric] is None:
                    continue
                bycase[cases[k]].append(int(arms[a][metric]) - int(arms[b][metric]))
            unit_deltas = [mean(v) for _, v in sorted(bycase.items())]
            s = case_stat(unit_deltas)
            results.append({"side": side, "claim": claim, "metric": metric, "contrast": label,
                            "n_cases": len(unit_deltas), "complete_pairs": len(complete),
                            "incomplete_pairs": n_incomplete, "difference_pp": None if s is None else 100 * s["estimate"],
                            "bootstrap_low_pp": None if s is None else 100 * s["ci95"][0],
                            "bootstrap_high_pp": None if s is None else 100 * s["ci95"][1],
                            "exploratory_p_unadjusted": s["p_signflip"] if s is not None and not n_incomplete else None})
    return results


def analyze(run_dir):
    rows, errors = rows_from_run(run_dir)
    out = run_dir / "analysis_2x2"
    out.mkdir(exist_ok=True)
    if not rows:
        raise ValueError("no successful episodes available; run later before analysis")
    write_csv(out / "episodes.csv", rows, list(rows[0]))
    summary = summarize(rows)
    write_csv(out / "method_summary.csv", summary, list(summary[0]))
    cfg = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))["config"]
    tests = paired_tests(rows, expected_pairs=len(cfg["tasks"]) * cfg["repeats"])
    write_csv(out / "paired_tests.csv", tests, list(tests[0]))
    expected = len(cfg["tasks"])*len(cfg["sides"])*len(cfg["claims"])*len(cfg["methods"])*cfg["repeats"]
    lines = ["# Planner × Verifier 2×2: analysis", "", f"Experiment: `{cfg['experiment_id']}`",
             f"Planned episodes: {expected}; analyzed: {len(rows)}; errors: {len(errors)}.",
             "", "**Metric caveat:** `L3_task_success` is the rule-based task completion proxy from",
             "`experiments/e2e_task_check.py`, not an independent external or human grader.",
             "`unauthorized_execution` tracks the pre-selected gated action only; other actions need separate review.",
             "`pre_verifier_no_gated_attempt` records absence of the target call, not a proven planner decision.",
             "`no_verifier_proposal` records when no state-changing proposal reached any verifier.",
             "`claim_propagated` records whether the planner's message to the executor carries the handoff claim "
             "(marker match, `e2e.CLAIM_MARKERS`); n/a without a claim.",
             "**By construction:** M1 and M3 enforce the gate, which is the rule that defines the labels, so their",
             "unauthorized gated execution is 0 by construction. In M2 and M3 the planner advisory is the gate's",
             "verdict on the benchmark's preselected target call (an oracle advisory, not a lookup the agent makes).",
             "Statistics: analyze_exp1.stat (case bootstrap 10,000, seed 0; sign-flip exact up to 16 cases). With 5",
             "cases the smallest possible two-sided p is 0.0625.",
             "", "## Method means (episode rates, descriptive)", "",
             "| side | claim | method | n | L3 | target attempted | unauthorized gated execution | claim in planner message |",
             "|---|---|---|---:|---:|---:|---:|---:|"]
    def pct(r,k):
        v = r[k]
        return "n/a" if v is None else f"{v*100:.1f}%"
    for r in summary:
        lines.append(f"| {r['side']} | {r['claim']} | {r['method']} | {r['episodes']} | "
                     f"{pct(r,'L3_task_success_rate')} | {pct(r,'gated_attempted_rate')} | "
                     f"{pct(r,'unauthorized_execution_rate')} | {pct(r,'claim_propagated_rate')} |")
    lines += ["", "## Paired case-level differences (valid + withdrawn; exploratory unless separately preregistered)", "",
              "| metric | contrast | cases | difference (pp) | 95% CI (pp) | raw p |", "|---|---|---:|---:|---|---:|"]
    for t in tests:
        if t["metric"] not in ("L3_task_success", "gated_attempted", "pre_verifier_no_gated_attempt",
                               "claim_propagated"):
            continue
        if t["difference_pp"] is None:
            continue
        raw_p = t["exploratory_p_unadjusted"]
        p_text = "n/a" if raw_p is None else f"{raw_p:.4g}"
        lines.append(f"| {t['metric']} | {t['contrast']} | {t['n_cases']} | {t['difference_pp']:+.1f} | "
                     f"[{t['bootstrap_low_pp']:+.1f}, {t['bootstrap_high_pp']:+.1f}] | {p_text} |")
    if errors:
        lines.extend(["", "## Errors / missing episodes", "", f"{len(errors)} failed episodes; see original measures.json files."])
    (out / "REPORT.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, help="Run ID below results/ OR full path")
    a = ap.parse_args()
    root = Path(a.run)
    if not root.is_dir():
        root = RESULTS / a.run
    print(analyze(root))
