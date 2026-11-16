"""A minimal Anthropic Messages API client with the `client.responses.create(...)` shape that `hearsay.llm`
uses, so a Claude model can be a verifier without changing the callers (no SDK dependency).

Only single-shot text calls are supported (instructions -> system, input -> one user message); tool use
is not. Sampling: temperature only (newer Claude models reject temperature and top_p together).
Retries 429, 5xx and overloaded errors with exponential backoff.
"""

from __future__ import annotations

import time
from types import SimpleNamespace
from typing import Any, Callable

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
RETRY_STATUS = frozenset({429, 500, 502, 503, 504, 529})


class AnthropicError(RuntimeError):
    pass


class _Responses:
    def __init__(self, client: "AnthropicClient") -> None:
        self.client = client

    def create(self, *, model: str, instructions: str, input: Any, temperature: float | None = None,
               top_p: float | None = None, max_output_tokens: int | None = None, tools: Any = None,
               **_: Any) -> SimpleNamespace:
        if tools:
            raise AnthropicError("tool use is not supported by this client")
        body: dict[str, Any] = {"model": model, "max_tokens": max_output_tokens or self.client.max_tokens,
                                "system": instructions, "messages": [{"role": "user", "content": str(input)}]}
        if temperature is not None:
            body["temperature"] = temperature
        elif top_p is not None:
            body["top_p"] = top_p
        data = self.client._post(body)
        text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
        usage = data.get("usage") or {}
        return SimpleNamespace(output_text=text, model=data.get("model"), stop_reason=data.get("stop_reason"),
                               usage=SimpleNamespace(input_tokens=usage.get("input_tokens", 0),
                                                     output_tokens=usage.get("output_tokens", 0)))


class AnthropicClient:
    def __init__(self, api_key: str, *, max_retries: int = 8, timeout: float = 120.0, max_tokens: int = 1024,
                 post: Callable[..., Any] | None = None, sleep: Callable[[float], None] = time.sleep) -> None:
        if not api_key:
            raise AnthropicError("no Anthropic API key")
        self.api_key, self.max_retries, self.timeout, self.max_tokens = api_key, max_retries, timeout, max_tokens
        self._http_post, self._sleep = post, sleep
        self.responses = _Responses(self)

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        post = self._http_post
        if post is None:
            import requests
            post = requests.post
        headers = {"x-api-key": self.api_key, "anthropic-version": API_VERSION, "content-type": "application/json"}
        for attempt in range(self.max_retries + 1):
            try:
                r = post(API_URL, json=body, headers=headers, timeout=self.timeout)
            except Exception as e:                     # network errors: retry like a 5xx
                if attempt == self.max_retries:
                    raise AnthropicError(f"request failed: {type(e).__name__}") from e
                self._sleep(min(60.0, 2 ** attempt))
                continue
            if r.status_code == 200:
                return r.json()
            if r.status_code in RETRY_STATUS and attempt < self.max_retries:
                self._sleep(min(60.0, 2 ** attempt))
                continue
            try:
                err = r.json().get("error", {})
            except ValueError:
                err = {}
            raise AnthropicError(f"HTTP {r.status_code}: {err.get('type')}: {err.get('message')}")
        raise AnthropicError("retries exhausted")
