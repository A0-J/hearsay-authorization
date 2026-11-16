"""Experiment A: verifier-only. No agent runs; the dataset's probe calls go to every verification method.

An item is task x probe x delegation x condition:
  delegation   `claim` (the request and the planner's handoff note with the authority claim) or
               `no_claim` (the request alone): the inherited claim is the only difference
  condition    the approval state (sigma); the policy (pi) is the same in every condition
Every method judges every item, in each of `repeats` independent repeats. Within a repeat,
identical LLM inputs are judged once and reused (a claim-only verifier's input does not change
with the approval state, the semantic check's not with the delegation either); across repeats
nothing is reused, so the repeats are independent samples of the same inputs. Each verdict
records its repeat, its input hash and whether it was reused.

The design is repeated measures: 11 probe calls from 5 tasks, not 132 independent cases. The
analysis treats the task as the unit for confidence intervals (evaluate.py).

Ground truth is not read here; evaluate.py joins it afterwards.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Iterator

from . import dataset
from .calls import ToolCall
from .paired import CONDITIONS, DELEGATION_VARIANTS
from .verify import DecisionCache, compute_request, judge, llm_request


def items(*, tasks: list[str] | None = None, conditions=CONDITIONS, delegations=DELEGATION_VARIANTS,
          root=dataset.DATASET_DIR) -> list[dict[str, str]]:
    out = []
    for task_id in tasks or dataset.task_ids(root):
        for probe in dataset.load_inputs(task_id, root)["probes"]:
            for d in delegations:
                for c in conditions:
                    out.append({"item_id": f"{task_id}/{probe['probe_id']}/{d}/{c}", "task_id": task_id,
                                "probe_id": probe["probe_id"], "delegation": d, "condition": c})
    return out


def _resolved(work: list[dict[str, str]], root) -> Iterator[tuple[dict, ToolCall, Any, dict]]:
    inputs: dict[str, dict] = {}
    for it in work:
        task_inputs = inputs.setdefault(it["task_id"], dataset.load_inputs(it["task_id"], root))
        probe = next(p for p in task_inputs["probes"] if p["probe_id"] == it["probe_id"])
        yield it, ToolCall(**probe["call"]), dataset.registry(it["task_id"], it["condition"], root), task_inputs


def llm_jobs(work: list[dict[str, str]], methods: tuple[str, ...], *, model: str, n_votes: int,
             root=dataset.DATASET_DIR) -> dict[tuple, tuple[str, str]]:
    """The distinct LLM judgements one repeat needs: cache key -> (instructions, input text)."""
    jobs: dict[tuple, tuple[str, str]] = {}
    for it, call, registry, task_inputs in _resolved(work, root):
        for m in methods:
            req = llm_request(m, call, task_inputs["delegations"][it["delegation"]], registry, model=model,
                              n_votes=n_votes, request=task_inputs["request"],
                              trusted_context=task_inputs["trusted_context"])
            if req:
                jobs.setdefault(req[0], (req[1], req[2]))
    return jobs


def run(work: list[dict[str, str]], methods: tuple[str, ...], *, client: Any, model: str, n_votes: int,
        repeats: int = 1, reuse: bool = True, workers: int = 1,
        root=dataset.DATASET_DIR) -> Iterator[dict[str, Any]]:
    for r in range(repeats):
        cache = DecisionCache() if reuse else None
        if cache is not None and workers > 1:          # judge this repeat's distinct inputs in parallel
            jobs = llm_jobs(work, methods, model=model, n_votes=n_votes, root=root)
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {key: pool.submit(compute_request, client, model, key, ins, text, n_votes)
                           for key, (ins, text) in jobs.items()}
                for key, future in futures.items():
                    cache.store[key] = {**future.result(), "input_sha256": key[-1]}
        for it, call, registry, task_inputs in _resolved(work, root):
            for m in methods:
                d = judge(m, call, task_inputs["delegations"][it["delegation"]], registry, client=client,
                          model=model, n_votes=n_votes, request=task_inputs["request"],
                          trusted_context=task_inputs["trusted_context"], cache=cache)
                yield {**it, "repeat": r, "method": m, "allow": d["allow"], "decision": d}
