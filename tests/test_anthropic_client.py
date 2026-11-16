"""The Claude adapter, against a fake HTTP endpoint (no API calls)."""

from types import SimpleNamespace

import pytest

from hearsay.anthropic_client import AnthropicClient, AnthropicError
from hearsay.llm import complete, sampling_for


class FakePost:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []

    def __call__(self, url, json, headers, timeout):
        self.calls.append({"url": url, "json": json, "headers": headers})
        status, body = self.replies.pop(0)
        return SimpleNamespace(status_code=status, json=lambda: body)


OK = (200, {"model": "claude-sonnet-5-5", "stop_reason": "end_turn",
            "content": [{"type": "text", "text": '{"decision": "reject", "reason": "r"}'}],
            "usage": {"input_tokens": 120, "output_tokens": 9}})


def test_request_shape_and_response_parsing():
    post = FakePost([OK])
    out = complete(AnthropicClient("k", post=post), "claude-sonnet-5-5", "SYSTEM", "USER INPUT")
    body = post.calls[0]["json"]
    assert body["system"] == "SYSTEM" and body["messages"] == [{"role": "user", "content": "USER INPUT"}]
    assert body["temperature"] == 1.0 and "top_p" not in body and body["max_tokens"] == 1024
    assert post.calls[0]["headers"]["x-api-key"] == "k" and post.calls[0]["headers"]["anthropic-version"]
    assert out["text"] == '{"decision": "reject", "reason": "r"}' and out["served_model"] == "claude-sonnet-5-5"
    assert out["usage"] == {"input_tokens": 120, "output_tokens": 9, "calls": 1}


def test_retries_overloaded_then_fails_on_client_errors():
    post = FakePost([(529, {"error": {"type": "overloaded_error"}}), (429, {}), OK])
    client = AnthropicClient("k", post=post, sleep=lambda s: None)
    assert client.responses.create(model="m", instructions="s", input="i").output_text
    assert len(post.calls) == 3
    bad = AnthropicClient("k", post=FakePost([(401, {"error": {"type": "authentication_error", "message": "no"}})]),
                          sleep=lambda s: None)
    with pytest.raises(AnthropicError, match="401"):
        bad.responses.create(model="m", instructions="s", input="i")


def test_sampling_is_temperature_only_for_claude():
    assert sampling_for("claude-sonnet-5-5") == {"temperature": 1.0}
    assert sampling_for("gpt-4.1") == {"temperature": 1.0, "top_p": 1.0}
