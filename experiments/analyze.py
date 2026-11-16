"""Tables from results/<name>/episodes.jsonl (0 API calls). Wilson 95% intervals.

  PYTHONPATH=src python experiments/analyze.py results/<name>

Writes results/<name>/derived/summary.md and episodes.csv.
Unit: one episode. Episodes of the same scenario are not independent, so the
intervals are optimistic; the per-scenario breakdown is in episodes.csv.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from common import RESULTS  # noqa: E402,F401

from hearsay.episode import OUTCOMES  # noqa: E402
from hearsay.guards import METHODS  # noqa: E402
from hearsay.io import read_jsonl  # noqa: E402
from hearsay.scenarios import AUTHORIZED, CONDITIONS  # noqa: E402
from hearsay.stats import fmt  # noqa: E402


def count(eps, pred) -> tuple[int, int]:
    return sum(map(pred, eps)), len(eps)


def main() -> None:
    d = Path(sys.argv[1])
    raw = read_jsonl(d / "episodes.jsonl")
    errors = [r for r in raw if "error" in r]
    eps = [r for r in raw if "error" not in r]
    methods = [m for m in METHODS if any(e["method"] == m for e in eps)]
    by = defaultdict(list)
    for e in eps:
        by[(e["method"], e["condition"])].append(e)
        by[(e["method"], "authorized" if e["authorized"] else "unauthorized")].append(e)

    L = [f"# {d.name}: {len(eps)} episodes ({len(errors)} errors excluded)", ""]
    L += ["## Headline: unauthorized execution vs. legitimate tasks not done", "",
          "Unauthorized execution: share of episodes in the unauthorized conditions where a call the record does "
          "not authorize ran. Legitimate task done: share of episodes in the authorized conditions where the "
          "intended call ran; false rejection: the guard blocked the valid intended call.", "",
          "| method | unauthorized execution | legitimate task done | false rejection (guard) | "
          "not attempted (agents) |", "|---|---|---|---|---|"]
    for m in methods:
        u, a = by[(m, "unauthorized")], by[(m, "authorized")]
        L.append(f"| {m} | {fmt(*count(u, lambda e: e['outcome'] == 'unauthorized_execution'))} "
                 f"| {fmt(*count(a, lambda e: e['outcome'] == 'correct_execution'))} "
                 f"| {fmt(*count(a, lambda e: e['outcome'] == 'false_rejection'))} "
                 f"| {fmt(*count(a, lambda e: e['outcome'] == 'not_attempted'))} |")

    L += ["", "## By condition", "",
          "Authorized conditions: intended call ran. Unauthorized conditions: unauthorized call ran.", "",
          "| method | " + " | ".join(CONDITIONS) + " |", "|---|" + "---|" * len(CONDITIONS)]
    for m in methods:
        cells = []
        for c in CONDITIONS:
            target = "correct_execution" if c in AUTHORIZED else "unauthorized_execution"
            k, n = count(by[(m, c)], lambda e: e["outcome"] == target)
            cells.append(f"{k}/{n}" if n else "–")
        L.append(f"| {m} | " + " | ".join(cells) + " |")

    L += ["", "## Outcomes by method", "", "| method | " + " | ".join(OUTCOMES) + " |",
          "|---|" + "---|" * len(OUTCOMES)]
    for m in methods:
        oc = Counter(e["outcome"] for e in eps if e["method"] == m)
        L.append(f"| {m} | " + " | ".join(str(oc[o]) for o in OUTCOMES) + " |")

    none = [e for e in eps if e["method"] == "none"]
    if none:
        L += ["", "## Agents without any verification (method none)", "",
              "Executor attempted the intended call; coordinator forwarded the cited approval id; executor looked "
              "the approval up (only with --record-lookup).", "",
              "| condition | executor attempted intended call | claim forwarded | looked up record |",
              "|---|---|---|---|"]
        for c in CONDITIONS:
            g = [e for e in none if e["condition"] == c]
            fw = [e for e in g if e["claim_forwarded"] is not None]
            L.append(f"| {c} | {fmt(*count(g, lambda e: e['attempted_intended']))} "
                     f"| {fmt(*count(fw, lambda e: e['claim_forwarded']))} "
                     f"| {fmt(*count(g, lambda e: e['looked_up_record']))} |")

    usage = Counter()
    for e in eps:
        for run in [e.get("coordinator") or {}] + e.get("executor_runs", []):
            usage.update(run.get("usage", {}))
        for ev in e["events"]:
            for v in (ev.get("guard") or {}).get("votes", []):
                usage.update(v.get("usage", {}))
    L += ["", f"Agent and verifier usage: {usage['calls']} calls, {usage['input_tokens']} input tokens, "
          f"{usage['output_tokens']} output tokens (restatements for dualflow not included)."]
    if errors:
        L += ["", "Errors: " + "; ".join(sorted(Counter(r["error"].split(":")[0] for r in errors)))]

    out = d / "derived"
    out.mkdir(exist_ok=True)
    (out / "summary.md").write_text("\n".join(L), encoding="utf-8")
    cols = ["scenario_id", "base_id", "domain", "condition", "authorized", "method", "executor_model", "repeat",
            "delegated", "claim_forwarded", "looked_up_record", "attempted_intended", "blocked_attempts", "outcome",
            "executed_calls", "unauthorized_calls", "intended_gate_reason"]
    with (out / "episodes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for e in eps:
            w.writerow({k: (json.dumps(e[k]) if isinstance(e.get(k), list) else e.get(k)) for k in cols})
    print("\n".join(L))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
