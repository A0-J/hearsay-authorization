"""Run Hearsay episodes on original AuthorizationBench tasks.

    python experiments/run_authbench.py --task T0010-l-b-h --name smoke_t0010
    python experiments/run_authbench.py --task T0010-l-b-h --dry-run          # fake client, 0 API calls
    python experiments/run_authbench.py --task T0007-a-g-h --condition valid fabricated --dry-run

Without --condition the original task runs as it is (no policy: every call that is not
read-only needs an approval). With --condition the runtime policy and the approval state come
from dataset/tasks/<task_id>/ (policy.json, <condition>.json), the planner receives the
dataset's handoff note, and approvals are judged on the task's reference date. The ground
truth (ground_truth.json) is never read here.

One model for every LLM role (--model, default gpt-4.1): the independent variable
is the evidence a verifier sees, not the model. --planner-model / --executor-model /
--verifier-model exist only for the separate model-comparison experiments.

Every state-changing call is judged by every method in --shadow (identical
proposals); only --enforce decides whether it runs. Results go to
results/authbench/<name>/<task_id>/r<k>/ (episode.json, proposals.jsonl) with
results/authbench/<name>/meta.json.

The benchmark's Oracle User (the principal behind message_user) is an LLM in the
environment; it uses --oracle-model (default: --model) through litellm.
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

from common import RESULTS, openai_client, run_meta  # noqa: E402

from hearsay.authbench import dataset, prompts  # noqa: E402
from hearsay.authbench.approvals import ApprovalRegistry  # noqa: E402
from hearsay.authbench.calls import STATE_CHANGE, effect  # noqa: E402
from hearsay.authbench.locate import PINNED_COMMIT, checkout_commit  # noqa: E402
from hearsay.authbench.runtime import ROLES, RunConfig, WorkspaceRequired, run_episode  # noqa: E402
from hearsay.authbench.task import load_task  # noqa: E402
from hearsay.authbench.verify import METHODS  # noqa: E402


def prompt_hashes() -> dict[str, str]:
    return prompts.fingerprints()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", nargs="+", required=True, help="task ids (or bundle paths)")
    ap.add_argument("--name", default="authbench")
    ap.add_argument("--model", default="gpt-4.1", help="the model of every LLM role")
    for role in ROLES:
        ap.add_argument(f"--{role}-model", help="model-comparison experiments only")
    ap.add_argument("--oracle-model", help="the benchmark's Oracle User (default: --model)")
    ap.add_argument("--delegation", choices=("direct", "planner"), default="direct")
    ap.add_argument("--handoff-note", help="text (or @file) the planner receives with the request")
    ap.add_argument("--enforce", choices=METHODS, default="none")
    ap.add_argument("--shadow", nargs="*", choices=METHODS, default=list(METHODS))
    ap.add_argument("--condition", nargs="+", help="dataset conditions (dataset/tasks/<task_id>/<condition>.json)")
    ap.add_argument("--record", help="approval record JSON for an original task (default: empty, dated to the task)")
    ap.add_argument("--record-lookup", action="store_true", help="give the executor the record lookup tool")
    ap.add_argument("--n-votes", type=int, default=3)
    ap.add_argument("--max-turns", type=int, default=35)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true", help="fake client, 0 API calls")
    a = ap.parse_args()

    if a.condition and (a.record or a.handoff_note):
        ap.error("--condition takes the record and the handoff note from the dataset")
    note = a.handoff_note
    if note and note.startswith("@"):
        note = open(note[1:], encoding="utf-8").read()
    role_models = {r: getattr(a, f"{r}_model") for r in ROLES if getattr(a, f"{r}_model")}

    def run_config(handoff_note):
        return RunConfig(model=a.model, role_models=role_models,
                         delegation="planner" if a.condition else a.delegation, handoff_note=handoff_note,
                         enforce=a.enforce, shadow=tuple(a.shadow), n_votes=a.n_votes,
                         record_lookup=a.record_lookup, max_turns=a.max_turns)

    config = run_config(note)
    record = json.load(open(a.record, encoding="utf-8")) if a.record else None

    out = RESULTS / "authbench" / a.name
    out.mkdir(parents=True, exist_ok=True)
    oracle_model = a.oracle_model or a.model
    client = None
    if not a.dry_run:
        client = openai_client()
        os.environ.setdefault("LITELLM_MODEL", oracle_model)
        os.environ.setdefault("LITELLM_API_KEY", os.environ["OPENAI_API_KEY"])
    meta = run_meta(config=config.to_dict(), oracle_model=None if a.dry_run else os.environ.get("LITELLM_MODEL"),
                    dry_run=a.dry_run, authbench={"pinned": PINNED_COMMIT, "checkout": checkout_commit()},
                    prompt_sha256=prompt_hashes(), tasks=a.task, conditions=a.condition, repeats=a.repeats,
                    record=record)
    (out / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    for task_ref in a.task:
        task = load_task(task_ref)
        for condition in a.condition or ["original"]:
            if condition == "original":
                registry = (ApprovalRegistry.from_dict(record, today=task.today) if record
                            else ApprovalRegistry.empty(task.today))
                episode_config = config
            else:
                registry = dataset.registry(task.task_id, condition)
                episode_config = run_config(dataset.load_inputs(task.task_id)["handoff_note"])
            if registry.today != task.today:
                raise SystemExit(f"{task.task_id}: the record is dated {registry.today}, the task {task.today}")
            if a.dry_run:
                from hearsay.authbench.fake import FakeAuthBenchClient
                state_changing = [t for t in task.allowlist if effect(t) == STATE_CHANGE]
                target = next((t for t in state_changing if registry.policy_level(t) == "required"), state_changing[0])
                client = FakeAuthBenchClient(registry, target)
            for k in range(a.repeats):
                try:
                    ep = run_episode(task, episode_config, client=client, registry=registry,
                                     out_dir=out / task.task_id / condition / f"r{k}")
                except WorkspaceRequired as e:
                    print(f"skip {task.task_id}: {e}")
                    break
                print(f"{task.task_id} {condition} r{k}: {len(ep['proposals'])} proposals, "
                      f"{len(ep['executed_state_changes'])} executed, {len(ep['blocked'])} blocked, "
                      f"unexplained changes {ep['unexplained_state_changes']}")


if __name__ == "__main__":
    main()
