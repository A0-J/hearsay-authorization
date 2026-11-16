"""JSON extraction from model output."""

from __future__ import annotations

import json
import re

_FENCE_RE = re.compile(r"^```[a-zA-Z]*\n?|```$", re.MULTILINE)
_DECODER = json.JSONDecoder()


def parse_json_object(text: str) -> dict:
    """The first complete JSON object in `text` (markdown fences removed)."""
    text = _FENCE_RE.sub("", text.strip()).strip()
    start = text.find("{")
    while start != -1:
        try:
            obj, _ = _DECODER.raw_decode(text, start)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
        start = text.find("{", start + 1)
    raise ValueError(f"No JSON object found in model output: {text[:200]!r}")
