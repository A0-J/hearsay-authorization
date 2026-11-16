"""LLM calls through the OpenAI Responses API shape (OpenAI, or Claude via hearsay.anthropic_client):
sampling settings, single-shot completions and usage accounting."""

from __future__ import annotations

import time
from collections import Counter
from typing import Any

DEFAULT_SAMPLING_MODELS = frozenset({"gpt-5.5", "gpt-6.1-sol"})   # reject temperature/top_p
# Reasoning models (OpenAI o-series and GPT-5/6) and Claude models whose API removed sampling parameters
# (Opus 5 / 5.5, Fable): their sampling is the provider's default, so nothing is sent.
_NO_SAMPLING_PREFIXES = ("o1", "o3", "o4", "gpt-5", "gpt-6", "claude-opus-5", "claude-fable", "claude-mythos")


def sampling_for(model: str) -> dict[str, float]:
    if model in DEFAULT_SAMPLING_MODELS or model.startswith(_NO_SAMPLING_PREFIXES):
        return {}
    if model.startswith("claude-"):              # Claude: temperature only (temperature and top_p together are rejected)
        return {"temperature": 1.0}
    return {"temperature": 1.0, "top_p": 1.0}


def usage_of(response: Any) -> Counter:
    usage = getattr(response, "usage", None)
    return Counter({"input_tokens": getattr(usage, "input_tokens", 0) or 0,
                    "output_tokens": getattr(usage, "output_tokens", 0) or 0, "calls": 1})


def complete(client: Any, model: str, instructions: str, input_text: str, **request: Any) -> dict[str, Any]:
    """One call without tools; returns the text and the call's metadata. `request` holds per-run request
    options from the config (e.g. Claude's `thinking`, `max_output_tokens`), sent unchanged."""
    start = time.monotonic()
    r = client.responses.create(model=model, instructions=instructions, input=input_text, **sampling_for(model),
                                **request)
    stop = getattr(r, "stop_reason", None) or getattr(r, "status", None)
    return {"text": r.output_text, "requested_model": model, "served_model": getattr(r, "model", None),
            "stop_reason": stop, "latency_ms": round((time.monotonic() - start) * 1000.0, 1),
            "usage": dict(usage_of(r))}
