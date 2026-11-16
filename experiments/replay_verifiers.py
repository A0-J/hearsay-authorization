"""Re-judge saved proposals with any verification method, without re-running the agents.

    python experiments/replay_verifiers.py results/authbench/pilot --methods llm_claim_only llm_with_evidence

Each proposal in <dir>/**/proposals.jsonl carries everything a verifier saw (the
call, the task message, the approval record), so every method and model is
compared on identical proposals. Writes <dir>/replay_<model>.jsonl.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import openai_client, run_meta

from hearsay.authbench.approvals import ApprovalRegistry
from hearsay.authbench.calls import ToolCall
from hearsay.authbench.verify import METHODS, NEEDS_CLIENT, judge


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results", type=Path)
    ap.add_argument("--methods", nargs="+", choices=METHODS, default=list(METHODS))
    ap.add_argument("--model", default="gpt-4.1")
    ap.add_argument("--n-votes", type=int, default=3)
    a = ap.parse_args()

    client = openai_client() if set(a.methods) & NEEDS_CLIENT else None
    out = a.results / f"replay_{a.model}.jsonl"
    n = 0
    with open(out, "w", encoding="utf-8") as f:
        f.write(json.dumps({"meta": run_meta(methods=a.methods, model=a.model, n_votes=a.n_votes)}) + "\n")
        for path in sorted(a.results.rglob("proposals.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                p = json.loads(line)
                call, registry = ToolCall(**p["call"]), ApprovalRegistry.from_dict(p["registry"])
                for m in a.methods:
                    d = judge(m, call, p["delegation"], registry, client=client, model=a.model, n_votes=a.n_votes,
                              request=p.get("request"))
                    f.write(json.dumps({"source": path.relative_to(a.results).as_posix(),
                                        "proposal_index": p["proposal_index"], "task_id": p["task_id"],
                                        "record_verdict": p["record_verdict"], "decision": d},
                                       ensure_ascii=False) + "\n")
                    n += 1
    print(f"{n} judgements -> {out}")


if __name__ == "__main__":
    main()
