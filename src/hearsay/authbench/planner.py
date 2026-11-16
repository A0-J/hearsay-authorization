"""The planner agent: reads the principal's request (and any handoff note carrying an inherited claim) and writes
the task message the executor works from. It has no tools."""

from __future__ import annotations

from typing import Any

from ..llm import complete, sampling_for
from .prompts import PLANNER_INSTRUCTIONS, planner_input
from .task import AuthBenchTask


def plan(client: Any, model: str, task: AuthBenchTask, handoff_note: str | None = None) -> dict[str, Any]:
    call = complete(client, model, PLANNER_INSTRUCTIONS, planner_input(task, handoff_note))
    return {"message": call["text"].strip(), "handoff_note": handoff_note, "sampling": sampling_for(model), **call}
