"""Generalization, second source (docs/GENERALIZATION_PREREG.md, Amendments 1-2): the AgentDojo v1 reviews and
constructions (banking + travel, slack + workspace), combined. One AgentDojo user task = one case; reporting group
"agentdojo". REVIEW rows: (case, suite, task_id, stage, decision, reason)."""

from __future__ import annotations

from . import ad_tasks_bank_travel as bt
from . import ad_tasks_slack_work as sw
from .exp1 import E1Task

REVIEW = list(bt.REVIEW_BT) + list(sw.REVIEW_SW)
SELECTED = [r[2] for r in REVIEW if r[4] == "selected"]
AD_ID = {**bt.AD_ID, **sw.AD_ID}


def group(t: E1Task) -> str:
    return "agentdojo"


def build_tasks() -> list[E1Task]:
    tasks = bt.build_bt() + sw.build_sw()
    assert sorted(t.task_id for t in tasks) == sorted(SELECTED), "every selected task is built, and only those"
    return sorted(tasks, key=lambda t: t.task_id)
