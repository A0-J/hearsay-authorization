"""Archive a finished verifier-only run and record it in the run registry (results/registry.json).

    python experiments/archive_run.py results/A-smoke-v2 --label "smoke" --note "..."

The raw results stay out of git (results/A-*/ is ignored). This writes a zip of the run directory to
archives/<run>.zip (also ignored; copy it to separate storage) and adds to the tracked registry: the
commit and config the run used, prompt fingerprints, model and sampling, the API calls and tokens
counted from the recorded votes, every file's SHA-256 and the archive's SHA-256. Runs are listed
side by side; their results are never pooled.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from common import ROOT

REGISTRY = ROOT / "results" / "registry.json"
ARCHIVES = ROOT / "archives"
PRICE_PER_MTOK = {"gpt-4.1": (2.0, 8.0)}   # USD per million input / output tokens (OpenAI list price, 2026-11)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def usage(verdicts: Path) -> dict:
    """API calls and tokens, counted once per distinct judgement (reused decisions are not new calls)."""
    seen, calls, tin, tout = set(), 0, 0, 0
    for line in verdicts.read_text(encoding="utf-8").splitlines():
        v = json.loads(line)
        if "raw" in v and isinstance(v.get("usage"), dict):     # Experiment 1: one row per call
            calls += 1
            tin += v["usage"].get("input_tokens", 0)
            tout += v["usage"].get("output_tokens", 0)
            continue
        d = v["decision"]
        for block in ([d] if "votes" in d else [d["semantic"]] if "semantic" in d else []):
            key = (v.get("repeat", 0), block.get("input_sha256"))
            if key in seen:
                continue
            seen.add(key)
            for vote in block["votes"]:
                calls += 1
                tin += (vote.get("usage") or {}).get("input_tokens", 0)
                tout += (vote.get("usage") or {}).get("output_tokens", 0)
    return {"api_calls": calls, "input_tokens": tin, "output_tokens": tout}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", type=Path)
    ap.add_argument("--label", required=True, help="what the run is, e.g. 'smoke' or 'Experiment A run 1'")
    ap.add_argument("--note", action="append", default=[], help="an observation to keep with the run")
    a = ap.parse_args()

    run = a.run.resolve()
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    files = [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p)}
             for p in sorted(run.rglob("*")) if p.is_file()]
    ARCHIVES.mkdir(exist_ok=True)
    archive = ARCHIVES / f"{run.name}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(run.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(run.parent).as_posix())
    cfg = manifest["config"]
    use = usage(run / "verdicts.jsonl")
    price = PRICE_PER_MTOK.get(cfg["model"])
    entry = {
        "run_id": run.name, "label": a.label, "experiment": manifest.get("experiment"),
        "started": manifest["time"], "git": manifest["git"], "dry_run": manifest.get("dry_run"),
        "config_file": manifest.get("config_file"), "config": cfg, "dataset": manifest.get("dataset"),
        "authbench_commit": manifest.get("authbench_commit"), "prompts_sha256": manifest.get("prompts_sha256"),
        "packages": manifest.get("packages"), "items": manifest.get("items"),
        "planned_llm_calls": manifest.get("planned_llm_calls"), "usage": use,
        "estimated_cost_usd": round(use["input_tokens"] / 1e6 * price[0] + use["output_tokens"] / 1e6 * price[1], 3)
        if price else None,
        "files": files, "archive": {"path": archive.relative_to(ROOT).as_posix(), "sha256": sha256(archive)},
        "notes": a.note, "pooling": "reported on its own; never pooled with other runs",
    }
    registry = json.loads(REGISTRY.read_text(encoding="utf-8")) if REGISTRY.exists() else {"runs": []}
    registry["runs"] = [r for r in registry["runs"] if r["run_id"] != run.name] + [entry]
    REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{run.name}: {len(files)} files, {use['api_calls']} API calls, archive {archive.name} "
          f"sha256 {entry['archive']['sha256'][:16]}...")


if __name__ == "__main__":
    main()
