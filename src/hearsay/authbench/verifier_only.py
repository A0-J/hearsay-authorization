"""Experiment A: verifier-only. No agent runs; the dataset's probe calls go to every verification method.

An item is task x probe x delegation x condition:
  delegation   `claim` (the request and the planner's handoff note with the authority claim) or
               `no_claim` (the request alone): the inherited claim is the only difference
  condition    the approval state (sigma); the policy (pi) is the same in every condition
Every method judges every item. Identical LLM inputs are judged once and reused (a claim-only
verifier's input does not change with the approval state, the semantic check's not with the
delegation either); each verdict records the input hash and whether it was reused. The items are
therefore not independent observations: the analysis reports the distinct inputs per method.

Ground truth is not read here; evaluate.py joins it afterwards.
"""

from __future__ import annotations

from typing import Any, Iterator

from . import dataset
from .calls import ToolCall
from .paired import CONDITIONS, DELEGATION_VARIANTS
from .verify import judge


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


def run(work: list[dict[str, str]], methods: tuple[str, ...], *, client: Any, model: str, n_votes: int,
        reuse: bool = True, root=dataset.DATASET_DIR) -> Iterator[dict[str, Any]]:
    cache: dict | None = {} if reuse else None
    inputs: dict[str, dict] = {}
    for it in work:
        task_inputs = inputs.setdefault(it["task_id"], dataset.load_inputs(it["task_id"], root))
        probe = next(p for p in task_inputs["probes"] if p["probe_id"] == it["probe_id"])
        call, registry = ToolCall(**probe["call"]), dataset.registry(it["task_id"], it["condition"], root)
        for m in methods:
            d = judge(m, call, task_inputs["delegations"][it["delegation"]], registry, client=client, model=model,
                      n_votes=n_votes, request=task_inputs["request"],
                      trusted_context=task_inputs["trusted_context"], cache=cache)
            yield {**it, "method": m, "allow": d["allow"], "decision": d}
