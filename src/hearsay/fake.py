"""A stand-in for the OpenAI client, for dry runs and tests (0 API calls).

It answers the Responses API calls of one scenario:
  coordinator    delegates the scripted delegation (task + claim), then reports
  executor       makes the intended call, then reports
  restatement    the intended call
  verifier       claim_only approves iff the message carries an "Authorization:" claim;
                 with_evidence approves iff the record authorizes the call
"""

from __future__ import annotations

import itertools
import json
from types import SimpleNamespace
from typing import Any

from .parsing import parse_json_object
from .prompts import (COORDINATOR_INSTRUCTIONS, EXECUTOR_INSTRUCTIONS, RESTATE_INSTRUCTIONS,
                      VERIFIER_INSTRUCTIONS)
from .proposal import Proposal
from .records import record_authorizes
from .scenarios import Scenario

_ids = itertools.count()


class _Item(SimpleNamespace):
    def model_dump(self, **_: Any) -> dict[str, Any]:
        return dict(vars(self))


def _message(text: str) -> _Item:
    return _Item(type="message", role="assistant", content=[{"type": "output_text", "text": text}])


def _call(name: str, args: dict[str, Any]) -> _Item:
    return _Item(type="function_call", name=name, arguments=json.dumps(args), call_id=f"call_{next(_ids)}")


def _response(output: list[_Item]) -> SimpleNamespace:
    text = "".join(c["text"] for o in output if o.type == "message" for c in o.content)
    return SimpleNamespace(output=output, output_text=text, model="fake",
                           usage=SimpleNamespace(input_tokens=0, output_tokens=0))


def _tool_results(items: Any) -> list[str]:
    return [i["output"] for i in items if isinstance(i, dict) and i.get("type") == "function_call_output"] \
        if isinstance(items, list) else []


class FakeOpenAI:
    def __init__(self, scenario: Scenario) -> None:
        self.s = scenario
        self.responses = self

    def create(self, *, model: str, instructions: str, input: Any, tools: Any = None, **_: Any) -> SimpleNamespace:
        s, done = self.s, _tool_results(input)
        if instructions == COORDINATOR_INSTRUCTIONS:
            if not done:
                return _response([_call("delegate_to_executor", {"message": s.scripted_delegation})])
            return _response([_message("The executor reported: " + done[-1])])
        if instructions == EXECUTOR_INSTRUCTIONS:
            if not done:
                args = {"resource": s.intended.resource, "scope": s.intended.scope}
                return _response([_call(s.intended.action, args)])
            return _response([_message("Result: " + done[-1])])
        if instructions == RESTATE_INSTRUCTIONS:
            return _response([_message(json.dumps(s.intended.to_dict()))])
        if instructions == VERIFIER_INSTRUCTIONS["claim_only"]:
            approve = "Authorization:" in input
        elif instructions == VERIFIER_INSTRUCTIONS["with_evidence"]:
            line = next(l for l in input.splitlines() if l.startswith("Proposed tool call:"))
            p = Proposal.from_dict(parse_json_object(line.split(":", 1)[1]))
            approve = record_authorizes(p, s.store)
        else:
            raise ValueError("unrecognized instructions")
        return _response([_message(json.dumps({"decision": "approve" if approve else "reject",
                                               "reason": "fake"}))])
