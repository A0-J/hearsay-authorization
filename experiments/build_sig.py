"""Build the signed-state (SIG) datasets from the pinned AuthorizationBench checkout. No API calls.

    python experiments/build_sig.py                                  # dataset/sig/ and dataset/sig_obs1/
    python experiments/build_sig.py --obs2 SIG-obs1-gpt-4.1-run1     # dataset/sig_obs2/ from stage 1 replies

dataset/sig/       presentation {plain, signed, signed_claim_unproven} x instruction {aware (16 cells/task), explicit (12)}
                   + signed_claim_label x aware (16): 100 cells/task
dataset/sig_obs1/  Observer stage 1: the task message of each aware, plain cell without the positive note (12/task)
dataset/sig_obs2/  Observer stage 2: one verifier cell per stage 1 reply (run with repeats = 1)

The build refuses to write if a plain cell differs from the frozen Experiment 1 cell, if deleting the added lines
of a signed cell does not give the plain input, if a signature does not verify, or if a gate verdict differs from
the cell's side. See docs/SIGNED_STATE_PREREG.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

if os.name == "nt" and not sys.flags.utf8_mode:   # the benchmark reads its bundles with the default encoding
    os.environ["PYTHONUTF8"] = "1"
    sys.exit(subprocess.call([sys.executable, *sys.argv]))

from common import RESULTS, ROOT  # noqa: E402

from hearsay.authbench import exp1, sigstate  # noqa: E402
from hearsay.authbench.exp1_tasks import build_tasks  # noqa: E402
from hearsay.authbench.locate import PINNED_COMMIT, checkout_commit  # noqa: E402

APPROVE_REJECT = ["approve", "reject"]
ADDED_PREFIXES = ("  signature: ", "  revocation: ")
HEADER_LINES = (sigstate.SOURCE_LINE, sigstate.CHECK_LINE, *sigstate.CLAIM_LINES.values())


def jsonl(rows) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def strip_added(text: str) -> str:
    return "\n".join(x for x in text.split("\n") if x not in HEADER_LINES and not x.startswith(ADDED_PREFIXES))


def frozen_e1() -> dict[str, str]:
    out = {}
    for d in sorted((ROOT / "dataset" / "exp1" / "tasks").iterdir()):
        for line in (d / "cells.jsonl").read_text(encoding="utf-8").splitlines():
            c = json.loads(line)
            out[c["cell_id"]] = c["input_sha256"]
    return out


def check(tasks) -> None:
    e1 = frozen_e1()
    for t in tasks:
        for c in sigstate.cells(t):
            lab = sigstate.label(t, c)
            if lab["gate_allowed"] != (c["side"] == "valid"):
                raise SystemExit(f"gate verdict differs from the side: {c['cell_id']}")
            plain = sigstate.sig_input(t, c["side"], c["condition"], c["claim"], "plain")
            if exp1.sha(plain) != e1[c["e1_cell_id"]]:
                raise SystemExit(f"plain input differs from the frozen Experiment 1 cell: {c['e1_cell_id']}")
            if c["presentation"] == "plain" and c["input"] != plain:
                raise SystemExit(f"plain cell is not Experiment 1's input: {c['cell_id']}")
            if c["presentation"] != "plain" and strip_added(c["input"]) != plain:
                raise SystemExit(f"signed cell is not the plain input plus added lines: {c['cell_id']}")


def write(name: str, version: str, tasks_cells: dict, labels: dict, instructions: dict, extra: dict) -> None:
    out = ROOT / "dataset" / name
    if out.exists():
        shutil.rmtree(out)
    for task_id, cells in tasks_cells.items():
        d = out / "tasks" / task_id
        d.mkdir(parents=True)
        (d / "cells.jsonl").write_text(jsonl(cells), encoding="utf-8")
        (d / "labels.jsonl").write_text(jsonl(labels[task_id]), encoding="utf-8")
    (out / "instructions.json").write_text(exp1.dumps(
        {k: {"text": v, "sha256": exp1.sha(v), "decisions": dec} for k, (v, dec) in instructions.items()}),
        encoding="utf-8")
    h = hashlib.sha256()
    for p in sorted((out / "tasks").rglob("*")):
        if p.is_file():
            h.update(p.relative_to(out).as_posix().encode() + b"\0" + p.read_bytes())
    n = sum(len(c) for c in tasks_cells.values())
    manifest = {"dataset": f"hearsay-{name}", "version": version, "prereg": "docs/SIGNED_STATE_PREREG.md",
                "task_set": "e1", "authbench_commit": PINNED_COMMIT, "tasks": list(tasks_cells), "cells": n,
                "cells_per_task": n // max(1, len(tasks_cells)), "tasks_sha256": h.hexdigest(),
                "spec_sha256": {m: exp1.sha((ROOT / "src" / "hearsay" / "authbench" / m).read_text(encoding="utf-8"))
                                for m in ("exp1.py", "sigstate.py")},
                "experiment1_dataset": "dataset/exp1/ is separate and unchanged", **extra}
    (out / "manifest.json").write_text(exp1.dumps(manifest), encoding="utf-8")
    print(f"{name}: {len(tasks_cells)} tasks, {n} cells")


def build_main(tasks) -> None:
    check(tasks)
    keys = {r: sigstate.key_id(r) for r in sorted({t.approver.role for t in tasks} | {t.unauthorized.role for t in tasks})}
    cells = {t.task_id: [{**c} for c in sigstate.cells(t)] for t in tasks}
    labels = {t.task_id: [sigstate.label(t, c) for c in cells[t.task_id]] for t in tasks}
    write("sig", sigstate.SIG_VERSION, cells, labels,
          {k: (exp1.E1_INSTRUCTIONS[k], APPROVE_REJECT) for k in exp1.INSTRUCTIONS},
          {"test_key_ids": keys, "test_keys": "seed = SHA-256('hearsay SIG test key <role>'); for testing only"})
    obs = {t.task_id: sigstate.observer_cells(t) for t in tasks}
    obs_labels = {t.task_id: [sigstate.label(t, c) for c in obs[t.task_id]] for t in tasks}
    write("sig_obs1", sigstate.OBS_VERSION, obs, obs_labels,
          {"observer": (sigstate.OBSERVER_INSTRUCTIONS, sigstate.OBSERVER_DECISIONS)}, {"stage": 1})


def build_obs2(tasks, run_id: str) -> None:
    by_task = {t.task_id: t for t in tasks}
    stage1 = {}
    for d in sorted((ROOT / "dataset" / "sig_obs1" / "tasks").iterdir()):
        for line in (d / "cells.jsonl").read_text(encoding="utf-8").splitlines():
            c = json.loads(line)
            stage1[c["cell_id"]] = c
    run = RESULTS / run_id
    cfg = json.loads((run / "manifest.json").read_text(encoding="utf-8"))["config"]
    verdicts = [json.loads(x) for x in (run / "verdicts.jsonl").read_text(encoding="utf-8").splitlines()]
    seen = {(v["cell_id"], v["repeat"]) for v in verdicts}
    missing = [(c, r) for c in stage1 for r in range(cfg["repeats"]) if (c, r) not in seen]
    if missing:
        raise SystemExit(f"stage 1 is incomplete: {len(missing)} replies missing")
    cells, labels = {}, {}
    for v in sorted(verdicts, key=lambda v: (v["cell_id"], v["repeat"])):
        s1 = stage1[v["cell_id"]]
        t = by_task[s1["task_id"]]
        original = exp1.delegation(t, s1["claim"], s1["condition"])
        message, why = sigstate.observer_message(v["raw"], original)
        text = sigstate.observer_stage2_input(t, s1["side"], s1["condition"], s1["claim"], message)
        c = {"cell_id": f"{v['cell_id']}/r{v['repeat']}", "task_id": t.task_id, "arm": "observer",
             "presentation": "plain", "instruction": "aware", "side": s1["side"], "condition": s1["condition"],
             "claim": s1["claim"], "obs1_cell_id": v["cell_id"], "obs1_repeat": v["repeat"], "observer_outcome": why,
             "message_changed": message != original,
             "instructions_sha256": exp1.sha(exp1.E1_INSTRUCTIONS["aware"]), "input": text,
             "input_sha256": exp1.sha(text)}
        cells.setdefault(t.task_id, []).append(c)
        labels.setdefault(t.task_id, []).append(sigstate.label(t, c))
    name = "sig_obs2_dryrun" if run_id.endswith("-dryrun") else "sig_obs2"   # a dry run never writes the real one
    write(name, sigstate.OBS_VERSION, cells, labels, {"aware": (exp1.E1_INSTRUCTIONS["aware"], APPROVE_REJECT)},
          {"stage": 2, "stage1_run": run_id})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--obs2", metavar="STAGE1_RUN_ID")
    a = ap.parse_args()
    if checkout_commit() != PINNED_COMMIT:
        raise SystemExit("the AuthorizationBench checkout is not at the pinned commit")
    tasks = build_tasks()
    if a.obs2:
        build_obs2(tasks, a.obs2)
    else:
        build_main(tasks)


if __name__ == "__main__":
    main()
