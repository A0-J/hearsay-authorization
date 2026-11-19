"""Build the escalation follow-up (SIGX) dataset, dataset/sigx/. No API calls. docs/SIGX_ESCALATION_PREREG_DRAFT.md.

    python experiments/build_sigx.py

The build refuses to write if a plain cell differs from the frozen Experiment 1 cell, if deleting the added lines of
a signed cell does not give the plain input, if the gate would allow a cell, or if a record has the forged id.
The signed-state datasets (dataset/sig/, dataset/sig_obs1/) are not touched.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys

if os.name == "nt" and not sys.flags.utf8_mode:   # the benchmark reads its bundles with the default encoding
    os.environ["PYTHONUTF8"] = "1"
    sys.exit(subprocess.call([sys.executable, *sys.argv]))

from build_sig import APPROVE_REJECT, frozen_e1, jsonl, strip_added  # noqa: E402
from common import ROOT  # noqa: E402

from hearsay.authbench import exp1, sigstate, sigx  # noqa: E402
from hearsay.authbench.exp1_tasks import build_tasks  # noqa: E402
from hearsay.authbench.locate import PINNED_COMMIT, checkout_commit  # noqa: E402

PREREG = "docs/SIGX_ESCALATION_PREREG_DRAFT.md"


def check(tasks) -> None:
    e1 = frozen_e1()
    for t in tasks:
        for condition in sigx.CONDITIONS:
            if not sigx.forged_id_absent(t, condition):
                raise SystemExit(f"a record has the forged id: {t.task_id}/{condition}")
        for c in sigx.cells(t):
            if sigx.label(t, c)["gate_allowed"]:
                raise SystemExit(f"the gate would allow: {c['cell_id']}")
            plain = sigstate.sig_input(t, "invalid", c["condition"], c["claim"], "plain")
            if exp1.sha(plain) != e1[c["e1_cell_id"]]:
                raise SystemExit(f"plain input differs from the frozen Experiment 1 cell: {c['e1_cell_id']}")
            if (c["input"] != plain) if c["presentation"] == "plain" else (strip_added(c["input"]) != plain):
                raise SystemExit(f"cell is not the plain input plus added lines: {c['cell_id']}")


def main() -> None:
    if checkout_commit() != PINNED_COMMIT:
        raise SystemExit("the AuthorizationBench checkout is not at the pinned commit")
    tasks = build_tasks()
    check(tasks)
    out = ROOT / "dataset" / "sigx"
    if out.exists():
        shutil.rmtree(out)
    for t in tasks:
        d = out / "tasks" / t.task_id
        d.mkdir(parents=True)
        cells = sigx.cells(t)
        (d / "cells.jsonl").write_text(jsonl(cells), encoding="utf-8")
        (d / "labels.jsonl").write_text(jsonl(sigx.label(t, c) for c in cells), encoding="utf-8")
    text = exp1.E1_INSTRUCTIONS[sigx.INSTRUCTION]
    (out / "instructions.json").write_text(exp1.dumps(
        {sigx.INSTRUCTION: {"text": text, "sha256": exp1.sha(text), "decisions": APPROVE_REJECT}}), encoding="utf-8")
    h = hashlib.sha256()
    for p in sorted((out / "tasks").rglob("*")):
        if p.is_file():
            h.update(p.relative_to(out).as_posix().encode() + b"\0" + p.read_bytes())
    n = sum(len(sigx.cells(t)) for t in tasks)
    src = ROOT / "src" / "hearsay" / "authbench"
    manifest = {"dataset": "hearsay-sigx", "version": sigx.SIGX_VERSION, "prereg": PREREG, "task_set": "e1",
                "authbench_commit": PINNED_COMMIT, "tasks": [t.task_id for t in tasks], "cells": n,
                "cells_per_task": n // len(tasks), "tasks_sha256": h.hexdigest(),
                "spec_sha256": {m: exp1.sha((src / m).read_text(encoding="utf-8"))
                                for m in ("exp1.py", "sigstate.py", "sigx.py")},
                "signed_state_dataset": "dataset/sig/ is separate and unchanged",
                "test_key_ids": {r: sigstate.key_id(r) for r in sorted(
                    {a.issuer for t in tasks for c in sigx.CONDITIONS for a in exp1.registry(t, "invalid", c).approvals})},
                "test_keys": "seed = SHA-256('hearsay SIG test key <role>'); for testing only"}
    (out / "manifest.json").write_text(exp1.dumps(manifest), encoding="utf-8")
    print(f"sigx: {len(tasks)} tasks, {n} cells")


if __name__ == "__main__":
    main()
