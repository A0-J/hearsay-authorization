"""Independent 2x2 planner x verifier intervention on the E3 AuthorizationBench tasks.

No API calls for --validate-only. --dry-run uses a deterministic fake client but
still needs the pinned AuthorizationBench sandbox to execute host episodes.
Real API calls require config approved_for_run=true AND --execute.

Apply this overlay to the original repository; do not import the old run_e2e
runner as its six-method shadow evaluations are intentionally disabled here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

if os.name == "nt" and not sys.flags.utf8_mode:
    os.environ["PYTHONUTF8"] = "1"
    sys.exit(subprocess.call([sys.executable, *sys.argv]))

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common import RESULTS, fatal_api_error, openai_client, run_meta, write_paused
from hearsay.authbench import e2e, exp1
from hearsay.authbench.exp1_tasks import SELECTED, build_tasks
from hearsay.authbench.fake import _message, _response
from run_e2e import FakeE2EClient
from hearsay.authbench.locate import PINNED_COMMIT, checkout_commit
from hearsay.authbench.planner_guard import GuardedPlanner, GUARD_INSTRUCTIONS
from hearsay.authbench.prompts import PLANNER_INSTRUCTIONS
from hearsay.authbench.runtime import RunConfig, run_episode
from hearsay.authbench.task import load_task

# M0 = baseline aware; M1 = verified gate; M2 = trusted planner advisory;
# M3 = both trusted planner advisory and execution gate.
METHODS = {
    "M0": {"planner_guard": False, "verifier": "aware"},
    "M1": {"planner_guard": False, "verifier": "gate"},
    "M2": {"planner_guard": True, "verifier": "aware"},
    "M3": {"planner_guard": True, "verifier": "gate"},
}
REQUIRED = {"experiment_id", "model", "tasks", "sides", "claims", "methods", "repeats", "max_turns"}


def check_config(c: dict) -> None:
    missing = REQUIRED - set(c)
    if missing:
        raise ValueError(f"config missing: {sorted(missing)}")
    if not c["experiment_id"] or not c["model"]:
        raise ValueError("experiment_id and model must not be empty")
    if any(x not in SELECTED for x in c["tasks"]) or not c["tasks"]:
        raise ValueError("tasks must be a nonempty subset of E3 selected tasks")
    if len(set(c["tasks"])) != len(c["tasks"]):
        raise ValueError("duplicate task ids")
    for k, allowed in (("sides", e2e.SIDES), ("claims", e2e.CLAIMS), ("methods", METHODS)):
        if not c[k] or len(set(c[k])) != len(c[k]) or any(x not in allowed for x in c[k]):
            raise ValueError(f"invalid {k}")
    if not (isinstance(c["repeats"], int) and c["repeats"] > 0):
        raise ValueError("repeats must be positive int")
    if not (isinstance(c["max_turns"], int) and c["max_turns"] > 0):
        raise ValueError("max_turns must be positive int")
    if not c["experiment_id"].startswith("PV2X2-") or "/" in c["experiment_id"] or ".." in c["experiment_id"]:
        raise ValueError("experiment_id must begin PV2X2- and contain no path separators")


def planned(c: dict) -> list[tuple[str, str, str, str, int]]:
    return [(tid, side, claim, method, k) for tid in c["tasks"] for side in c["sides"]
            for claim in c["claims"] for method in c["methods"] for k in range(c["repeats"])]


class Fake2x2Client(FakeE2EClient):
    """Pipeline fake; NOT an empirical effect simulator."""
    def create(self, *, model, instructions, input, tools=None, **kw):
        if instructions.startswith(PLANNER_INSTRUCTIONS) and GUARD_INSTRUCTIONS in instructions:
            # Simulated planner reads the trusted advisory, but executor fake always attempts the target.
            status = "AUTHORIZED" if "Authorization status: AUTHORIZED" in instructions else "NOT_AUTHORIZED"
            request = next(x for x in input.splitlines() if x.startswith("Request from your principal:"))
            return _response([_message(request.split(":", 1)[1].strip() if status == "AUTHORIZED" else
                                       "Request approval for this protected action before proceeding.")])
        return super().create(model=model, instructions=instructions, input=input, tools=tools, **kw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True)
    parser.add_argument("--validate-only", action="store_true", help="No benchmark or API needed")
    parser.add_argument("--dry-run", action="store_true", help="Fake client; benchmark host required")
    parser.add_argument("--execute", action="store_true", help="Explicit opt-in to live API calls")
    parser.add_argument("--shard", default="0/1")
    parser.add_argument("--limit", type=int, default=None)
    a = parser.parse_args()
    c = json.loads(Path(a.config).read_text(encoding="utf-8"))
    check_config(c)
    jobs = planned(c)
    i, n = map(int, a.shard.split("/"))
    if n <= 0 or not 0 <= i < n:
        raise SystemExit("shard must be i/n with 0 <= i < n")
    config_sha = hashlib.sha256(Path(a.config).read_bytes()).hexdigest()
    if a.validate_only:
        print(json.dumps({"experiment_id": c["experiment_id"], "episodes": len(jobs),
                          "per_method": len(jobs) // len(c["methods"]), "config_sha256": config_sha,
                          "design": METHODS, "api_calls": 0}, indent=2))
        return 0
    if not a.dry_run and (not a.execute or c.get("approved_for_run") is not True):
        raise SystemExit("Live run blocked: set approved_for_run=true in config AND pass --execute")
    if a.dry_run and a.execute:
        raise SystemExit("Choose --dry-run OR --execute, not both")
    if checkout_commit() != PINNED_COMMIT:
        raise SystemExit("AuthorizationBench checkout absent or not at pinned commit")
    task_map = {t.task_id: t for t in build_tasks()}
    out = RESULTS / (c["experiment_id"] + ("-dryrun" if a.dry_run else ""))
    out.mkdir(parents=True, exist_ok=True)
    metadata = {"experiment": c.get("experiment", "planner_verifier_2x2"), "config": c,
                "config_sha256": config_sha, "authbench_commit": checkout_commit(),
                "episodes_planned": len(jobs), "method_factors": METHODS,
                "warning": "planner advisory is for preselected target call, not arbitrary downstream calls",
                "planner_advisory": "oracle: ApprovalRegistry.check on the benchmark's preselected target call, "
                                    "the same rule that defines the labels; not a lookup the agent makes",
                "by_construction": "M1/M3 enforce the gate, so their unauthorized gated execution is 0 by construction"}
    manifest_file = out / "manifest.json"
    if manifest_file.exists():
        old = json.loads(manifest_file.read_text(encoding="utf-8"))
        if old.get("config_sha256") != config_sha:
            raise SystemExit("config changed for an existing run; use a NEW experiment_id")
    else:
        manifest_file.write_text(json.dumps(run_meta(**metadata), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    selected = jobs[i::n]
    if a.limit is not None:
        selected = selected[: a.limit]
    client = None if a.dry_run else openai_client()
    if not a.dry_run:
        os.environ.setdefault("LITELLM_MODEL", c["model"])
        os.environ.setdefault("LITELLM_API_KEY", os.environ["OPENAI_API_KEY"])
    done = 0
    pause = out / f"PAUSED-shard{i}of{n}.json"
    pause.unlink(missing_ok=True)
    for task_id, side, claim, method, k in selected:
        folder = out / "episodes" / task_id / side / claim / method / f"r{k}"
        measure_file = folder / "measures.json"
        if measure_file.exists() and not json.loads(measure_file.read_text(encoding="utf-8")).get("error"):
            continue
        if (out / "STOP").exists():
            write_paused(out, reason="STOP", done=done, total=len(selected),
                         resume=f"python experiments/run_planner_verifier_2x2.py --config {a.config} --shard {a.shard}")
            (out / "PAUSED.json").replace(pause)
            return 3
        t = task_map[task_id]
        task = load_task(task_id)
        reg = e2e.e2e_registry(t, side)
        cl = Fake2x2Client(reg, t.gated_tool) if a.dry_run else client
        factors = METHODS[method]
        verifier = e2e.E1Verification(t, side, enforce=factors["verifier"], client=cl,
                                      model=c["model"], shadow=False)
        guarded = GuardedPlanner(reg, t.call) if factors["planner_guard"] else None
        rc = RunConfig(model=c["model"], delegation="planner", handoff_note=e2e.CLAIMS[claim],
                       enforce="none", shadow=(), max_turns=c["max_turns"],
                       allow_missing_workspace=True)
        folder.mkdir(parents=True, exist_ok=True)
        condition = {"task_id": task_id, "case": t.case, "side": side, "claim": claim,
                     "method": method, "repeat": k, "planner_guard": factors["planner_guard"],
                     "verifier_method": factors["verifier"], "gated_tool": t.gated_tool,
                     "benchmark_target_call": t.call.to_dict()}
        (folder / "condition.json").write_text(json.dumps(condition, indent=2) + "\n", encoding="utf-8")
        workspace = e2e.WorkspaceShim(task.bundle)
        try:
            episode = run_episode(task, rc, client=cl, registry=reg, out_dir=folder,
                                  verification=verifier, workspace=workspace,
                                  context_resolver=e2e.e2e_context, planner_override=guarded)
            measure = {**condition, **e2e.measures(t, side, claim, episode),
                       "no_verifier_proposal": len(episode["proposals"]) == 0, "error": None}
        except Exception as exc:
            reason = fatal_api_error(exc)
            if reason is not None:
                write_paused(out, reason=reason, done=done, total=len(selected),
                             resume=f"python experiments/run_planner_verifier_2x2.py --config {a.config} --shard {a.shard}")
                (out / "PAUSED.json").replace(pause)
                print(f"PAUSED: {reason}", flush=True)
                return 3
            measure = {**condition, "error": f"{type(exc).__name__}: {str(exc)[:500]}"}
        finally:
            workspace.close()
        measure_file.write_text(json.dumps(measure, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        done += 1
        print(f"[{i}/{n}] {task_id} {side} {claim} {method} r{k}: "
              f"{'ERROR: ' + measure['error'] if measure.get('error') else ('gated_attempted=' + str(measure.get('gated_attempted')))}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
