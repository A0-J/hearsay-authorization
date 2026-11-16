"""A tool-using agent on the OpenAI Responses API: call the model, run the tools it calls, repeat.

Every model output item and every tool call with its result is kept, so the
trajectory can be inspected afterwards.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable

from .llm import sampling_for, usage_of

ToolHandler = Callable[[str, dict[str, Any]], dict[str, Any]]


@dataclass
class AgentRun:
    final_text: str = ""
    stop: str = ""                                   # "final" (the model answered) or "max_turns"
    turns: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    usage: Counter = field(default_factory=Counter)
    served_model: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"final_text": self.final_text, "stop": self.stop, "turns": self.turns,
                "tool_calls": self.tool_calls, "usage": dict(self.usage), "served_model": self.served_model}


def _dump(item: Any) -> dict[str, Any]:
    if hasattr(item, "model_dump"):
        return item.model_dump(exclude_none=True)
    return dict(item) if isinstance(item, dict) else {"repr": repr(item)}


def run_agent(client: Any, *, model: str, instructions: str, user_input: str, tools: list[dict[str, Any]],
              handle: ToolHandler, max_turns: int = 8,
              after_turn: Callable[[int], bool] | None = None) -> AgentRun:
    """`after_turn(turn)` runs after each turn's tool calls; returning True ends the run (e.g. a finish tool)."""
    run = AgentRun()
    items: list[Any] = [{"role": "user", "content": user_input}]
    for turn in range(max_turns):
        start = time.monotonic()
        r = client.responses.create(model=model, instructions=instructions, input=items, tools=tools,
                                    **sampling_for(model))
        run.usage += usage_of(r)
        run.served_model = getattr(r, "model", None)
        run.turns.append({"turn": turn, "latency_ms": round((time.monotonic() - start) * 1000.0, 1),
                          "output": [_dump(o) for o in r.output]})
        calls = [o for o in r.output if getattr(o, "type", None) == "function_call"]
        items += r.output
        if not calls:
            run.final_text, run.stop = r.output_text or "", "final"
            return run
        for c in calls:
            try:
                args = json.loads(c.arguments or "{}")
                result = handle(c.name, args)
            except json.JSONDecodeError:
                args, result = {"raw": c.arguments}, {"error": "arguments are not valid JSON"}
            run.tool_calls.append({"turn": turn, "tool": c.name, "args": args, "result": result})
            items.append({"type": "function_call_output", "call_id": c.call_id, "output": json.dumps(result)})
        if after_turn is not None and after_turn(turn):
            run.stop = "stopped"
            return run
    run.stop = "max_turns"
    return run
