"""Analyse an Experiment 3 run (docs/EXPERIMENT3_E2E_PREREG.md). Committed before any counted episode; tables only.

    python experiments/analyze_e2e.py results/E3-gpt-4.1-run1

Unit = task: an episode measure is averaged over a task's repeats, then over tasks. Tests E3-1..E3-3 are per-task
differences (sign-flip test, bootstrap interval, Holm over the three). Episodes that ended in an error are
reported and left out of the rates.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from analyze_exp2 import holm, stat, write_csv

MEASURES = ("gated_attempted", "gated_executed", "unauthorized_execution", "other_unauthorized_change",
            "false_rejection", "safe_completion", "blocked", "recovery", "claim_propagated")
METHODS = ("none", "claim_only", "aware", "explicit", "gate", "semantic_gate")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run", type=Path)
    a = ap.parse_args()
    run = a.run.resolve()
    eps, errors, usage = [], [], Counter()
    agree = defaultdict(Counter)        # method -> (method allow, gate allow) on gated proposals
    for f in sorted((run / "episodes").rglob("measures.json")):
        m = json.loads(f.read_text(encoding="utf-8"))
        if m.get("error"):
            errors.append(m)
            continue
        eps.append(m)
        ep = json.loads((f.parent / "episode.json").read_text(encoding="utf-8"))
        for role in ("executor", "planner"):
            u = (ep.get(role) or {}).get("usage") or {}
            usage["input_tokens"] += u.get("input_tokens", 0)
            usage["output_tokens"] += u.get("output_tokens", 0)
        for p in ep.get("proposals", []):
            for meth, d in p["decisions"].items():
                for v in ([d] if "usage" in d else []) + (d.get("semantic", {}).get("votes", []) if meth == "semantic_gate" else []):
                    usage["input_tokens"] += (v.get("usage") or {}).get("input_tokens", 0)
                    usage["output_tokens"] += (v.get("usage") or {}).get("output_tokens", 0)
                if p["call"]["tool"] == m["gated_tool"]:
                    agree[meth][(bool(d["allow"]), bool(p["record_verdict"]["allowed"]))] += 1

    def per_task(method, side, claim, measure):
        acc = defaultdict(list)
        for e in eps:
            if e["method"] == method and e["side"] == side and (claim is None or e["claim"] == claim) \
                    and e.get(measure) is not None:
                acc[e["task_id"]].append(float(e[measure]))
        return {t: mean(v) for t, v in acc.items()}

    def diff(m1, m2, side, claim, measure):
        a1, a2 = per_task(m1, side, claim, measure), per_task(m2, side, claim, measure)
        ts = sorted(set(a1) & set(a2))
        return stat([a1[t] - a2[t] for t in ts])

    tests = {"E3-1_unauthorized_execution_invalid_approved_claim_only_minus_aware":
             diff("claim_only", "aware", "invalid", "approved", "unauthorized_execution"),
             "E3-2_safe_completion_valid_withdrawn_explicit_minus_aware":
             diff("explicit", "aware", "valid", "withdrawn", "safe_completion"),
             "E3-3_safe_completion_valid_all_claims_semantic_gate_minus_explicit":
             diff("semantic_gate", "explicit", "valid", None, "safe_completion")}
    hp = holm({k: v["p_signflip"] for k, v in tests.items() if v["p_signflip"] is not None})
    for k in tests:
        tests[k]["p_holm"] = hp.get(k)

    rows = []
    for meth in METHODS:
        for side in ("valid", "invalid"):
            for claim in ("none", "approved", "withdrawn"):
                n = sum(1 for e in eps if e["method"] == meth and e["side"] == side and e["claim"] == claim)
                row = {"method": meth, "side": side, "claim": claim, "episodes": n}
                for ms in MEASURES:
                    pt = per_task(meth, side, claim, ms)
                    row[ms] = round(mean(pt.values()), 4) if pt else None
                rows.append(row)
    out = run / "analysis"
    out.mkdir(exist_ok=True)
    write_csv(out / "rates.csv", rows)
    (out / "tests.json").write_text(json.dumps(tests, indent=2) + "\n", encoding="utf-8")
    (out / "errors.jsonl").write_text("".join(json.dumps(e) + "\n" for e in errors), encoding="utf-8")
    ag = {m: {f"method_{'allow' if x else 'block'}_gate_{'allow' if y else 'deny'}": c for (x, y), c in v.items()}
          for m, v in agree.items()}
    (out / "shadow_agreement.json").write_text(json.dumps(ag, indent=2) + "\n", encoding="utf-8")
    lines = ["# Experiment 3 (E2E): results", "", f"Run `{run.name}`. Pre-registration: "
             "docs/EXPERIMENT3_E2E_PREREG.md (with Amendment 1). Tables only.", "",
             f"Episodes analysed {len(eps)}; episodes with an error {len(errors)} (errors.jsonl). Tokens (planner, "
             f"executor, verifiers; Oracle User not included): {dict(usage)}.", "",
             "## Pre-registered tests (unit = task, Holm over E3-1..E3-3)", "",
             "| test | estimate | 95% CI | p (sign-flip) | p (Holm) |", "|---|---|---|---|---|"]
    lines += [f"| {k} | {s['estimate']:+.4f} | [{s['ci95'][0]:+.4f}, {s['ci95'][1]:+.4f}] | {s['p_signflip']:.4f} | "
              f"{s['p_holm']:.4f} |" if s["estimate"] is not None else f"| {k} | n/a | | | |" for k, s in tests.items()]
    lines += ["", "## Rates (mean over tasks of per-task means)", "",
              "| method | state | claim | episodes | " + " | ".join(MEASURES) + " |",
              "|" + "---|" * (4 + len(MEASURES))]
    lines += [f"| {r['method']} | {r['side']} | {r['claim']} | {r['episodes']} | " +
              " | ".join("" if r[m] is None else f"{r[m]:.3f}" for m in MEASURES) + " |" for r in rows]
    lines += ["", "## Shadow agreement with the gate on gated-tool proposals", "", "```", json.dumps(ag, indent=1), "```"]
    (out / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
