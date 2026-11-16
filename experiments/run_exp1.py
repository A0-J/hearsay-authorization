"""Run Experiment 1 (verifier-only) on the frozen cells of dataset/exp1/.

    python experiments/run_exp1.py --config configs/exp1_gpt41.json --plan       # counts and token estimate
    python experiments/run_exp1.py --config configs/exp1_gpt41.json --dry-run    # fake client, 0 API calls
    python experiments/run_exp1.py --config configs/exp1_gpt41.json              # real calls (resumable)

Every cell is judged `repeats` times, one call each (independent samples). Each call is written to
results/<experiment_id>/verdicts.jsonl as soon as it returns: the raw reply, the parsed decision, basis
and reason, usage and latency. A rerun skips (cell, repeat) pairs already recorded. The labels are not
read here (experiments/analyze_exp1.py joins them).
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from importlib import metadata
from pathlib import Path

from common import RESULTS, ROOT, client_for, run_meta

from hearsay.llm import complete, sampling_for
from hearsay.parsing import parse_json_object

DATA = ROOT / "dataset" / "exp1"


def load_cells() -> list[dict]:
    cells = []
    for d in sorted((DATA / "tasks").iterdir()):
        cells += [json.loads(line) for line in (d / "cells.jsonl").read_text(encoding="utf-8").splitlines()]
    return cells


def parse(text: str) -> dict:
    try:
        obj = parse_json_object(text)
    except ValueError as e:
        return {"approve": False, "decision": None, "basis": None, "reason": None, "parse_error": str(e)}
    decision = str(obj.get("decision", "")).strip().lower()
    return {"approve": decision == "approve", "decision": decision, "basis": obj.get("basis"),
            "reason": obj.get("reason"), "parse_error": None if decision in ("approve", "reject") else "bad decision"}


class FakeClient:
    """Dry runs: approves iff the task message contains a claim note."""

    def __init__(self) -> None:
        self.responses = self

    def create(self, *, model, instructions, input, **_):
        from types import SimpleNamespace
        approve = "[Context note:" in str(input).split("Proposed tool call:")[0] or "approved this action" in str(input)
        text = json.dumps({"decision": "approve" if approve else "reject", "basis": "none", "reason": "fake"})
        return SimpleNamespace(output_text=text, model=model, usage=SimpleNamespace(input_tokens=0, output_tokens=0))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cfg = json.loads(a.config.read_text(encoding="utf-8"))
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    instructions = json.loads((DATA / "instructions.json").read_text(encoding="utf-8"))
    problems = []
    if manifest["version"] != cfg["dataset_version"]:
        problems.append(f"dataset {manifest['version']} != config {cfg['dataset_version']}")
    for k, v in instructions.items():
        if cfg["instructions_sha256"].get(k) != v["sha256"]:
            problems.append(f"instructions '{k}' differ from the config")
    if cfg["sampling"] != sampling_for(cfg["model"]):
        problems.append("sampling differs from the code")
    if problems:
        raise SystemExit("config check failed: " + "; ".join(problems))

    cells = load_cells()
    by_hash = {v["sha256"]: v["text"] for v in instructions.values()}
    work = [(c, r) for r in range(cfg["repeats"]) for c in cells]
    chars = sum(len(c["input"]) + len(by_hash[c["instructions_sha256"]]) for c in cells) * cfg["repeats"]
    print(f"{len(cells)} cells x {cfg['repeats']} repeats = {len(work)} calls; ~{chars / 4 / 1e6:.2f}M input tokens "
          f"(chars/4)")
    if a.plan:
        return 0

    out = RESULTS / (cfg["experiment_id"] + ("-dryrun" if a.dry_run else ""))
    out.mkdir(parents=True, exist_ok=True)
    path = out / "verdicts.jsonl"
    done = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            v = json.loads(line)
            done.add((v["cell_id"], v["repeat"]))
    todo = [(c, r) for c, r in work if (c["cell_id"], r) not in done]
    if not (out / "manifest.json").exists():
        (out / "manifest.json").write_text(json.dumps(run_meta(
            experiment="Experiment 1 run 1 (verifier-only)", config=cfg, config_file=a.config.as_posix(),
            dry_run=a.dry_run, dataset=manifest, packages={p: metadata.version(p) for p in ("openai", "requests")},
            calls_planned=len(work)), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(done)} already recorded, {len(todo)} to run -> {out.relative_to(ROOT)}")
    client = FakeClient() if a.dry_run else client_for(cfg["model"])
    lock, n = threading.Lock(), 0

    def one(cell, r):
        res = complete(client, cfg["model"], by_hash[cell["instructions_sha256"]], cell["input"])
        return {"cell_id": cell["cell_id"], "repeat": r,
                **{k: cell[k] for k in ("task_id", "arm", "instruction", "side", "condition", "claim",
                                        "input_sha256", "instructions_sha256")},
                "raw": res["text"], **parse(res["text"]), "served_model": res["served_model"],
                "usage": res["usage"], "latency_ms": res["latency_ms"]}

    with open(path, "a", encoding="utf-8") as f, ThreadPoolExecutor(max_workers=cfg["workers"]) as pool:
        futures = [pool.submit(one, c, r) for c, r in todo]
        for fut in as_completed(futures):
            v = fut.result()
            with lock:
                f.write(json.dumps(v, ensure_ascii=False) + "\n")
                f.flush()
                n += 1
                if n % 250 == 0:
                    print(f"  {n}/{len(todo)}", flush=True)
    print(f"done: {n} calls -> {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
