"""Generalization tasks (docs/GENERALIZATION_PREREG.md): the AuthorizationBench review and constructions of groups
1-5 (gen_tasks_g1..g5, each reviewed under the frozen rule before any generalization call), combined.

REVIEW rows: (case, domain, task_id, stage, decision, reason). GROUP tells whether a selected task is a new domain
of an Experiment 1 case ("e1_case_new_domain") or a new case ("new_case"); results are reported per group.
"""

from __future__ import annotations

from . import gen_tasks_g1, gen_tasks_g2, gen_tasks_g3, gen_tasks_g4, gen_tasks_g5
from .exp1 import E1Task
from .exp1_tasks import SELECTED as E1_SELECTED

_MODULES = (gen_tasks_g1, gen_tasks_g2, gen_tasks_g3, gen_tasks_g4, gen_tasks_g5)
REVIEW = sorted((row for k, m in enumerate(_MODULES, 1) for row in getattr(m, f"REVIEW_G{k}")),
                key=lambda r: (r[0], r[1], r[2]))
SELECTED = [r[2] for r in REVIEW if r[4] == "selected"]
E1_CASES = {f"S{t[1:5]}" for t in E1_SELECTED}


def group(t: E1Task) -> str:
    return "e1_case_new_domain" if t.case in E1_CASES else "new_case"


def build_tasks() -> list[E1Task]:
    tasks = [t for k, m in enumerate(_MODULES, 1) for t in getattr(m, f"build_g{k}")()]
    assert sorted(t.task_id for t in tasks) == sorted(SELECTED), "every selected task is built, and only those"
    return sorted(tasks, key=lambda t: t.task_id)
