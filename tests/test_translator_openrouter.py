"""Tests for the OpenRouter client (retry/backoff/usage parsing) with a fake session."""

import pytest

from pcleaner.translator.openrouter import (
    OpenRouterClient,
    OpenRouterError,
    ChatResponse,
)


class FakeResponse:
    def __init__(self, status_code, json_data=None, headers=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = headers or {}
        self.text = text

    def json(self):
        return self._json


class FakeSession:
    """Returns queued responses (or raises queued exceptions) on each post()."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def make_success(content="[\"hi\"]", prompt=10, completion=5, cost=0.002, model="m"):
    return FakeResponse(
        200,
        {
            "model": model,
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": prompt, "completion_tokens": completion, "cost": cost},
        },
    )


def make_client(outcomes, **kwargs):
    sleeps = []
    session = FakeSession(outcomes)
    client = OpenRouterClient(
        "key",
        session=session,
        sleep=lambda s: sleeps.append(s),
        **kwargs,
    )
    return client, session, sleeps


def test_requires_api_key():
    with pytest.raises(OpenRouterError):
        OpenRouterClient("")


def test_successful_call_parses_content_and_usage():
    client, session, _ = make_client([make_success(content='["สวัสดี"]')])
    resp = client.chat("model-x", [{"role": "user", "content": "hi"}], temperature=0.5)
    assert isinstance(resp, ChatResponse)
    assert resp.content == '["สวัสดี"]'
    assert resp.usage.prompt_tokens == 10
    assert resp.usage.completion_tokens == 5
    assert resp.usage.cost_usd == 0.002
    assert resp.usage.model == "m"
    # Auth + attribution headers are sent.
    headers = session.calls[0]["headers"]
    assert headers["Authorization"] == "Bearer key"
    assert "HTTP-Referer" in headers and "X-Title" in headers
    assert session.calls[0]["json"]["temperature"] == 0.5


def test_retries_on_429_then_succeeds():
    client, session, sleeps = make_client(
        [FakeResponse(429, headers={"Retry-After": "3"}), make_success()],
        max_retries=4,
    )
    resp = client.chat("m", [{"role": "user", "content": "x"}])
    assert resp.content == '["hi"]'
    assert len(session.calls) == 2
    # Retry-After header is respected for the backoff delay.
    assert sleeps == [3.0]


def test_retries_exhausted_raises():
    client, session, sleeps = make_client(
        [FakeResponse(500), FakeResponse(500), FakeResponse(500)],
        max_retries=2,
    )
    with pytest.raises(OpenRouterError):
        client.chat("m", [{"role": "user", "content": "x"}])
    assert len(session.calls) == 3  # initial + 2 retries
    assert len(sleeps) == 2


def test_network_error_retried_then_raised():
    client, session, sleeps = make_client(
        [ConnectionError("boom"), ConnectionError("boom")],
        max_retries=1,
    )
    with pytest.raises(OpenRouterError):
        client.chat("m", [{"role": "user", "content": "x"}])
    assert len(session.calls) == 2
    assert len(sleeps) == 1


def test_non_retryable_status_raises_immediately():
    client, session, _ = make_client([FakeResponse(400, text="bad request")])
    with pytest.raises(OpenRouterError):
        client.chat("m", [{"role": "user", "content": "x"}])
    assert len(session.calls) == 1


def test_exponential_backoff_without_retry_after():
    client, session, sleeps = make_client(
        [FakeResponse(503), FakeResponse(503), make_success()],
        max_retries=4,
        backoff_base=2.0,
    )
    client.chat("m", [{"role": "user", "content": "x"}])
    # Backoff uses base ** attempt: 2**0, 2**1.
    assert sleeps == [1.0, 2.0]


def test_missing_usage_defaults_to_zero():
    resp_data = FakeResponse(200, {"choices": [{"message": {"content": "[]"}}]})
    client, _, _ = make_client([resp_data])
    resp = client.chat("m", [{"role": "user", "content": "x"}])
    assert resp.usage.prompt_tokens == 0
    assert resp.usage.cost_usd == 0.0
