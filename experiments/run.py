"""Run episodes: scenarios x verification methods x executor models x repeats, with real tool-using agents.

  PYTHONPATH=src python experiments/run.py --dry-run                          # fake client, 0 API calls
  PYTHONPATH=src python experiments/run.py --name smoke --bases finance_vendor_payment \
      --conditions valid_claim fabricated --methods none provenance_gate        # a few real episodes
  PYTHONPATH=src python experiments/run.py --name main --repeats 3 --workers 8   # 64 scenarios x 5 methods x 3

Output: results/<name>/episodes.jsonl (one record per episode: every model output, tool call, guard decision)
        results/<name>/meta.json
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor

from common import (COORDINATOR_MODEL, EXECUTOR_MODEL, N_RESTATE, N_VERIFY, RESTATE_MODEL, RESULTS,  # noqa: E402
                    VERIFIER_MODEL, openai_client, run_meta)

from hearsay.episode import run_episode  # noqa: E402
from hearsay.guards import METHODS, IntentCache  # noqa: E402
from hearsay.io import append_jsonl  # noqa: E402
from hearsay.scenarios import BASES, CONDITIONS, scenarios  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default=None, help="results subdirectory (default: dry_run / run)")
    ap.add_argument("--methods", nargs="+", default=list(METHODS), choices=METHODS)
    ap.add_argument("--conditions", nargs="+", default=list(CONDITIONS), choices=CONDITIONS)
    ap.add_argument("--bases", nargs="+", default=[b.base_id for b in BASES], choices=[b.base_id for b in BASES])
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--executors", nargs="+", default=[EXECUTOR_MODEL], help="executor agent model(s)")
    ap.add_argument("--coordinator", default=COORDINATOR_MODEL)
    ap.add_argument("--verifier", default=VERIFIER_MODEL)
    ap.add_argument("--restater", default=RESTATE_MODEL)
    ap.add_argument("--n-verify", type=int, default=N_VERIFY)
    ap.add_argument("--n-restate", type=int, default=N_RESTATE)
    ap.add_argument("--delegation", choices=("agent", "scripted"), default="agent",
                    help="agent: the coordinator agent writes the delegation; scripted: fixed task + claim text")
    ap.add_argument("--record-lookup", action="store_true",
                    help="give the executor a lookup_approval tool on the approval system")
    ap.add_argument("--max-turns", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true", help="fake client, no API calls")
    ap.add_argument("--resume", action="store_true", help="skip episodes already recorded without error")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()

    bases = {b.base_id: b for b in BASES}
    scen = scenarios(tuple(bases[b] for b in args.bases), tuple(args.conditions))
    out = RESULTS / (args.name or ("dry_run" if args.dry_run else "run"))
    out.mkdir(parents=True, exist_ok=True)
    path = out / "episodes.jsonl"

    def key(r) -> tuple:
        return (r["scenario_id"], r["method"], r["executor_model"], r["repeat"])

    done = set()
    if args.resume and path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if "error" not in r:
                done.add(key(r))
    jobs = [(s, m, e, k) for s in scen for m in args.methods for e in args.executors for k in range(args.repeats)
            if (s.scenario_id, m, e, k) not in done]
    (out / "meta.json").write_text(json.dumps(run_meta(args=vars(args), n_scenarios=len(scen), n_jobs=len(jobs)),
                                              indent=2), encoding="utf-8")
    print(f"{len(scen)} scenarios x {len(args.methods)} methods x {len(args.executors)} executor(s) x "
          f"{args.repeats} repeat(s): {len(jobs)} episodes to run -> {path}")

    if args.dry_run:
        from hearsay.fake import FakeOpenAI
        client_for = FakeOpenAI
    else:
        shared = openai_client()   # thread-safe; shared by all workers
        client_for = lambda s: shared  # noqa: E731
    intents = IntentCache(client_for, args.restater, args.n_restate) if "dualflow" in args.methods else None
    lock = threading.Lock()
    count = {"done": 0, "err": 0}

    def one(s, method: str, executor: str, rep: int) -> None:
        base = {"scenario_id": s.scenario_id, "method": method, "executor_model": executor, "repeat": rep}
        try:
            ep = run_episode(s, method, client=client_for(s), coordinator_model=args.coordinator,
                             executor_model=executor, verifier_model=args.verifier, n_verify=args.n_verify,
                             intents=intents, delegation=args.delegation, record_lookup=args.record_lookup,
                             max_turns=args.max_turns)
            rec = {**ep, **base}
        except Exception as e:   # keep going; --resume runs it again
            rec = {**base, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()}
        with lock:   # record first, then print
            append_jsonl(path, rec)
            count["done"] += 1
            count["err"] += "error" in rec
            status = rec.get("error") or (f"{rec['outcome']:22s} delegated={rec['delegated']} "
                                          f"claim_forwarded={rec['claim_forwarded']}")
            print(f"  [{count['done']}/{len(jobs)}] {s.scenario_id:45s} {method:17s} #{rep} {status}",
                  flush=True, file=sys.stderr if "error" in rec else sys.stdout)

    if args.workers <= 1:
        for job in jobs:
            one(*job)
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for f in [pool.submit(one, *job) for job in jobs]:
                f.result()
    print(f"done; {count['err']} errors")


if __name__ == "__main__":
    main()
