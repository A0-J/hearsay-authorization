"""A stand-in for the OpenAI client on AuthorizationBench episodes, for dry runs and tests (0 API calls).

  planner        forwards the principal's request (and the handoff note, if any)
  executor       turn 1 calls `target` (a canonical state-changing tool) with placeholder arguments,
                 turn 2 calls finish
  verifier       claim_only approves iff the task message mentions an approval;
                 with_evidence / evidence_explicit approve iff the record authorizes the call;
                 the semantic check approves every call
"""

from __future__ import annotations

import json
from typing import Any

from ..fake import _call, _message, _response
from ..parsing import parse_json_object
from .approvals import ApprovalRegistry
from .calls import ToolCall
from .prompts import PLANNER_INSTRUCTIONS, SEMANTIC_INSTRUCTIONS, VERIFIER_INSTRUCTIONS
from .selfcheck import sample_arguments


class FakeAuthBenchClient:
    def __init__(self, registry: ApprovalRegistry, target: str) -> None:
        self.registry, self.target = registry, target
        self.responses = self

    def create(self, *, model: str, instructions: str, input: Any, tools: Any = None, **_: Any) -> Any:
        if instructions == PLANNER_INSTRUCTIONS:
            request = next(l for l in input.splitlines() if l.startswith("Request from your principal:"))
            note = "\n\n".join(p for p in input.split("\n\n")[2:-1])
            return _response([_message(request.split(":", 1)[1].strip().strip('"') + (f"\n\n{note}" if note else ""))])
        if instructions == SEMANTIC_INSTRUCTIONS:
            return _response([_message(json.dumps({"decision": "aligned", "reason": "fake"}))])
        if instructions in VERIFIER_INSTRUCTIONS.values():
            line = next(l for l in input.splitlines() if l.startswith("Proposed tool call:"))
            call = ToolCall(**parse_json_object(line.split(":", 1)[1]))
            if instructions != VERIFIER_INSTRUCTIONS["claim_only"]:
                approve = self.registry.check(call).allowed
            else:
                approve = "approv" in input.split("Proposed tool call:")[0].lower()
            return _response([_message(json.dumps({"decision": "approve" if approve else "reject",
                                                   "reason": "fake"}))])
        # executor
        done = sum(1 for i in input if isinstance(i, dict) and i.get("type") == "function_call_output")
        if done == 0:
            published = self.target.replace(".", "_")
            spec = next(t for t in tools if t["name"] == published)
            return _response([_call(published, sample_arguments(spec["parameters"]))])
        if done == 1:
            return _response([_call("finish", {"message": "done"})])
        return _response([_message("done")])


class ClaimFollowerClient:
    """Verifier-only dry runs (0 API calls): every LLM verifier approves iff the task message mentions an
    approval, and the semantic check approves every call. Its scores are a property of this rule, not a
    finding; it exercises the pipeline end to end."""

    def __init__(self) -> None:
        self.responses = self
        self.calls = 0

    def create(self, *, model: str, instructions: str, input: Any, **_: Any) -> Any:
        self.calls += 1
        if instructions == SEMANTIC_INSTRUCTIONS:
            return _response([_message(json.dumps({"decision": "aligned", "reason": "fake"}))])
        approve = "approv" in str(input).split("Proposed tool call:")[0].lower()
        return _response([_message(json.dumps({"decision": "approve" if approve else "reject", "reason": "fake"}))])
