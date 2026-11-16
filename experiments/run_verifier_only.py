"""Experiment A (verifier-only) from a config file: the dataset's probe calls, every method, every condition.

    python experiments/run_verifier_only.py --config configs/experiment_a.json --plan      # count LLM calls
    python experiments/run_verifier_only.py --config configs/experiment_a.json --dry-run   # fake client, 0 API calls
    python experiments/run_verifier_only.py --config configs/experiment_a.json             # real verifiers

The config pins the dataset version, the methods, the model, its sampling, the number of votes and the
prompt fingerprints; the run refuses to start if the code's prompts or sampling differ from it.
Writes results/<experiment_id>/ (<experiment_id>-dryrun for dry runs):

  manifest.json      the config, versions (git, dataset hash, AuthorizationBench commit, packages), prompts
  verdicts.jsonl     one line per item x method: item, method, decision with every vote and its input hash
  scored.jsonl       the decisions joined with the labels (A, I, final_allow); majority.jsonl: the
                     majority over repeats (the k-vote decision), with summary_majority.csv
  summary.csv        counts per method x condition x delegation (and "all")
  metrics.json       per method: the rates and the dependence on the inherited claim

Agent runs (experiment B) are separate (experiments/run_authbench.py); their results are never pooled
with these.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from importlib import metadata
from pathlib import Path

from common import RESULTS, ROOT, openai_client, run_meta

from hearsay.authbench import dataset, evaluate, prompts, verifier_only
from hearsay.authbench.calls import ToolCall
from hearsay.authbench.fake import ClaimFollowerClient
from hearsay.authbench.locate import PINNED_COMMIT
from hearsay.authbench.paired import DATASET_VERSION
from hearsay.authbench.verify import LLM_KIND, METHODS, SEMANTIC, input_sha256
from hearsay.llm import sampling_for

PACKAGES = ("openai", "jsonschema")


def dataset_sha256(root: Path = dataset.DATASET_DIR) -> str:
    h = hashlib.sha256()
    for p in sorted((root / "tasks").rglob("*.json")):
        h.update(p.relative_to(root).as_posix().encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


def check_config(cfg: dict) -> None:
    problems = []
    if cfg["dataset"]["version"] != DATASET_VERSION:
        problems.append(f"dataset version {cfg['dataset']['version']} != {DATASET_VERSION}")
    if set(cfg["methods"]) - set(METHODS):
        problems.append(f"unknown methods {set(cfg['methods']) - set(METHODS)}")
    if cfg["sampling"] != sampling_for(cfg["model"]):
        problems.append(f"sampling {cfg['sampling']} != the code's {sampling_for(cfg['model'])}")
    current = prompts.fingerprints()
    changed = sorted(k for k in set(current) | set(cfg["prompts_sha256"]) if current.get(k) != cfg["prompts_sha256"].get(k))
    if changed:
        problems.append(f"prompts differ from the config: {changed} (update the config deliberately)")
    if problems:
        raise SystemExit("config check failed: " + "; ".join(problems))


def planned_llm_calls(work: list[dict], methods: list[str], n_votes: int, reuse: bool, repeats: int) -> dict[str, int]:
    """LLM calls per method: distinct inputs per repeat (or every item without reuse) x votes x repeats."""
    seen: dict[str, set] = {m: set() for m in methods}
    total = {m: 0 for m in methods}
    for it in work:
        inputs = dataset.load_inputs(it["task_id"])
        probe = next(p for p in inputs["probes"] if p["probe_id"] == it["probe_id"])
        call, registry = ToolCall(**probe["call"]), dataset.registry(it["task_id"], it["condition"])
        for m in methods:
            if m in LLM_KIND:
                kind = LLM_KIND[m]
                key = input_sha256(prompts.VERIFIER_INSTRUCTIONS[kind],
                                   prompts.verifier_input(call, inputs["delegations"][it["delegation"]], registry, kind))
            elif m == SEMANTIC:
                key = input_sha256(prompts.SEMANTIC_INSTRUCTIONS,
                                   prompts.semantic_input(call, inputs["request"], inputs["trusted_context"]))
            else:
                continue
            total[m] += 1
            seen[m].add(key)
    return {m: (len(seen[m]) if reuse else total[m]) * n_votes * repeats for m in methods if total[m]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true", help="fake client (claim follower), 0 API calls")
    ap.add_argument("--plan", action="store_true", help="print the number of items and LLM calls, run nothing")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()

    cfg = json.loads(a.config.read_text(encoding="utf-8"))
    check_config(cfg)
    work = verifier_only.items(tasks=cfg["tasks"], conditions=cfg["conditions"], delegations=cfg["delegations"])
    repeats, workers = cfg.get("repeats", 1), cfg.get("workers", 1)
    calls = planned_llm_calls(work, cfg["methods"], cfg["n_votes"], cfg["reuse_identical_inputs"], repeats)
    print(f"{len(work)} items x {len(cfg['methods'])} methods x {repeats} repeats; LLM calls {sum(calls.values())} "
          f"{calls}")
    if a.plan:
        return

    out = RESULTS / (cfg["experiment_id"] + ("-dryrun" if a.dry_run else ""))
    if out.exists() and any(out.iterdir()) and not (a.overwrite or a.dry_run):
        raise SystemExit(f"{out} exists; pass --overwrite to replace it")
    out.mkdir(parents=True, exist_ok=True)
    client = ClaimFollowerClient() if a.dry_run else openai_client()
    manifest = run_meta(experiment="A: verifier-only", config=cfg, config_file=a.config.as_posix(), dry_run=a.dry_run,
                        dataset={"path": "dataset", "version": DATASET_VERSION, "sha256": dataset_sha256()},
                        authbench_commit=PINNED_COMMIT, prompts_sha256=prompts.fingerprints(),
                        packages={p: metadata.version(p) for p in PACKAGES},
                        items=len(work), planned_llm_calls=calls)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    verdicts = []
    with open(out / "verdicts.jsonl", "w", encoding="utf-8") as f:
        for i, v in enumerate(verifier_only.run(work, tuple(cfg["methods"]), client=client, model=cfg["model"],
                                                n_votes=cfg["n_votes"], repeats=repeats, workers=workers,
                                                reuse=cfg["reuse_identical_inputs"])):
            v = {"verdict_id": f"{cfg['experiment_id']}:{i:05d}", **v}
            verdicts.append(v)
            f.write(json.dumps(v, ensure_ascii=False, default=str) + "\n")

    m = evaluate.write_reports(out, verdicts)["per_repeat"]   # ground truth is joined only here
    for method, x in m["methods"].items():
        print(f"{method:27} FAR {x['unauthorized_accepted']}/{x['n_unauthorized']}  "
              f"FRR {x['valid_rejected']}/{x['n_valid']}  off-intent accepted "
              f"{x['off_intent_accepted']}/{x['n_off_intent']}  semantic uncertain {x['semantic_uncertain']}  "
              f"claim dependence {x['claim_dependence']['changed']}/{x['claim_dependence']['pairs']}")
    effect = m["analysis"]["claim_effect"].get("llm_with_evidence", {}).get("unauthorized")
    if effect:
        t = effect["tasks"]
        print(f"Delta_claim (evidence-aware FAR, claim - no claim): {effect['difference']} over {effect['items']} items; "
              f"per task {t['per_task']}; 95% CI over {t['n_tasks']} tasks {t['ci95']}")
    print(f"-> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
