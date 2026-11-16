"""Run Experiment 3 (end-to-end delegation; docs/EXPERIMENT3_E2E_PREREG.md).

    python experiments/run_e2e.py --config configs/e2e_gpt-4.1.json --dry-run --limit 4     # fake client
    python experiments/run_e2e.py --config configs/e2e_gpt-4.1.json --shard 0/6             # real calls

Episodes: task x approval state x handoff claim x enforced method x repeat, in a fixed order; shard i/N runs every
N-th episode from i, one at a time (the benchmark's host environment keeps per-process state, so parallelism is by
process). Each episode is saved to results/<id>/episodes/<task>/<side>/<claim>/<method>/r<k>/ (episode.json,
proposals.jsonl, condition.json, measures.json); an existing measures.json is skipped (resumable).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

if os.name == "nt" and not sys.flags.utf8_mode:   # the benchmark reads its bundles with the default encoding
    os.environ["PYTHONUTF8"] = "1"
    sys.exit(subprocess.call([sys.executable, *sys.argv]))

from common import RESULTS, ROOT, openai_client, run_meta  # noqa: E402

from hearsay.authbench import e2e, exp1  # noqa: E402
from hearsay.authbench.exp1_tasks import build_tasks  # noqa: E402
from hearsay.authbench.fake import FakeAuthBenchClient, _message, _response  # noqa: E402
from hearsay.authbench.locate import PINNED_COMMIT, checkout_commit  # noqa: E402
from hearsay.authbench.runtime import RunConfig, run_episode  # noqa: E402
from hearsay.authbench.task import load_task  # noqa: E402
from hearsay.parsing import parse_json_object  # noqa: E402
from hearsay.authbench.calls import ToolCall  # noqa: E402


class FakeE2EClient(FakeAuthBenchClient):
    """Dry runs: Experiment 1-format verifiers approve iff the gate allows (claim-only: iff the message mentions an
    approval); the semantic check says aligned; planner and executor as in FakeAuthBenchClient."""

    E1_TEXTS = set(exp1.E1_INSTRUCTIONS.values())

    def create(self, *, model, instructions, input, tools=None, **kw):
        from hearsay.authbench.exp2 import CLAIM_ONLY_INSTRUCTIONS
        if instructions in self.E1_TEXTS or instructions == CLAIM_ONLY_INSTRUCTIONS:
            line = next(x for x in input.splitlines() if x.startswith("Proposed tool call:"))
            call = ToolCall(**parse_json_object(line.split(":", 1)[1]))
            ok = (self.registry.check(call).allowed if instructions in self.E1_TEXTS
                  else "approv" in input.split("Proposed tool call:")[0].lower())
            return _response([_message(json.dumps({"decision": "approve" if ok else "reject", "basis": "none",
                                                   "reason": "fake"}))])
        return super().create(model=model, instructions=instructions, input=input, tools=tools, **kw)


def jobs(cfg):
    tasks = [t for t in build_tasks() if not cfg.get("tasks") or t.task_id in cfg["tasks"]]
    return [(t, side, claim, method, k) for t in tasks for side in cfg["sides"] for claim in cfg["claims"]
            for method in cfg["methods"] for k in range(cfg["repeats"])]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    cfg = json.loads(open(a.config, encoding="utf-8").read())
    if checkout_commit() != PINNED_COMMIT:
        raise SystemExit("the AuthorizationBench checkout is not at the pinned commit")
    i, n = map(int, a.shard.split("/"))
    out = RESULTS / (cfg["experiment_id"] + ("-dryrun" if a.dry_run else ""))
    out.mkdir(parents=True, exist_ok=True)
    all_jobs = jobs(cfg)
    if not (out / "manifest.json").exists():
        (out / "manifest.json").write_text(json.dumps(run_meta(
            experiment=cfg["experiment"], config=cfg, config_file=a.config, dry_run=a.dry_run,
            authbench={"pinned": PINNED_COMMIT, "checkout": checkout_commit()}, episodes_planned=len(all_jobs),
            oracle_model=cfg["model"]), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    mine = all_jobs[i::n][: a.limit] if a.limit else all_jobs[i::n]
    client = None
    if not a.dry_run:
        client = openai_client()
        os.environ.setdefault("LITELLM_MODEL", cfg["model"])
        os.environ.setdefault("LITELLM_API_KEY", os.environ["OPENAI_API_KEY"])
    done = 0
    for t, side, claim, method, k in mine:
        d = out / "episodes" / t.task_id / side / claim / method / f"r{k}"
        if (d / "measures.json").exists():
            continue
        task = load_task(t.task_id)
        registry = e2e.e2e_registry(t, side)
        cl = FakeE2EClient(registry, t.gated_tool) if a.dry_run else client
        verification = e2e.E1Verification(t, side, enforce=method, client=cl, model=cfg["model"])
        workspace = e2e.WorkspaceShim(task.bundle)
        config = RunConfig(model=cfg["model"], delegation="planner", handoff_note=e2e.CLAIMS[claim], enforce="none",
                           shadow=(), max_turns=cfg["max_turns"], allow_missing_workspace=True)
        d.mkdir(parents=True, exist_ok=True)
        cond = {"task_id": t.task_id, "case": t.case, "side": side, "claim": claim, "method": method, "repeat": k,
                "gated_tool": t.gated_tool, "workspace": "local stand-in (read_file/write_file on a copy; no terminal)"}
        (d / "condition.json").write_text(json.dumps(cond, indent=2) + "\n", encoding="utf-8")
        try:
            ep = run_episode(task, config, client=cl, registry=registry, out_dir=d, verification=verification,
                             workspace=workspace, context_resolver=e2e.e2e_context)
            m = {**cond, **e2e.measures(t, side, claim, ep), "error": None}
        except Exception as e:                       # recorded, never silently dropped
            m = {**cond, "error": f"{type(e).__name__}: {str(e)[:500]}"}
        finally:
            workspace.close()
        (d / "measures.json").write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        done += 1
        print(f"[{i}/{n}] {done}/{len(mine)} {t.task_id} {side} {claim} {method} r{k}: "
              f"{'ERROR ' + m['error'] if m.get('error') else {x: m.get(x) for x in ('gated_executed', 'blocked', 'safe_completion', 'unauthorized_execution')}}",
              flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
