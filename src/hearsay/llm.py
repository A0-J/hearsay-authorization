"""LLM calls through the OpenAI Responses API shape (OpenAI, or Claude via hearsay.anthropic_client):
sampling settings, single-shot completions and usage accounting."""

from __future__ import annotations

import time
from collections import Counter
from typing import Any

DEFAULT_SAMPLING_MODELS = frozenset({"gpt-5.5", "gpt-6.1-sol"})   # reject temperature/top_p


def sampling_for(model: str) -> dict[str, float]:
    if model in DEFAULT_SAMPLING_MODELS:
        return {}
    if model.startswith("claude-"):              # Claude: temperature only (temperature and top_p together are rejected)
        return {"temperature": 1.0}
    return {"temperature": 1.0, "top_p": 1.0}


def usage_of(response: Any) -> Counter:
    usage = getattr(response, "usage", None)
    return Counter({"input_tokens": getattr(usage, "input_tokens", 0) or 0,
                    "output_tokens": getattr(usage, "output_tokens", 0) or 0, "calls": 1})


def complete(client: Any, model: str, instructions: str, input_text: str) -> dict[str, Any]:
    """One call without tools; returns the text and the call's metadata."""
    start = time.monotonic()
    r = client.responses.create(model=model, instructions=instructions, input=input_text, **sampling_for(model))
    return {"text": r.output_text, "requested_model": model, "served_model": getattr(r, "model", None),
            "latency_ms": round((time.monotonic() - start) * 1000.0, 1), "usage": dict(usage_of(r))}
