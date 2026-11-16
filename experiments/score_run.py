"""Recompute every report of a verifier-only run from its verdicts.jsonl (no API calls).

    python experiments/score_run.py results/A-pilot-v2

Writes scored.jsonl, majority.jsonl, summary.csv, summary_majority.csv and metrics.json
(per_repeat and majority_over_repeats). The verdicts are never changed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import ROOT  # noqa: F401  (puts src on the path)

from hearsay.authbench import evaluate


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", type=Path)
    a = ap.parse_args()
    verdicts = [json.loads(line) for line in (a.run / "verdicts.jsonl").read_text(encoding="utf-8").splitlines()]
    reports = evaluate.write_reports(a.run, verdicts)
    for kind, m in reports.items():
        print(f"== {kind}")
        for method, x in m["methods"].items():
            print(f"{method:27} FAR {x['unauthorized_accepted']}/{x['n_unauthorized']}  FRR {x['valid_rejected']}/"
                  f"{x['n_valid']}  off-intent accepted {x['off_intent_accepted']}/{x['n_off_intent']}  "
                  f"semantic uncertain {x['semantic_uncertain']}")


if __name__ == "__main__":
    main()
