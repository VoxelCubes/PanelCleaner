"""
OpenRouter HTTP client for LLM-based translation.

A thin wrapper over the OpenRouter chat-completions API built on ``requests``. It
handles authentication, attribution headers, retry with exponential backoff on rate
limits / server errors, and surfaces token usage and cost for accounting.

The ``requests`` session and the sleep function are injectable so the client can be
unit-tested without real network calls or real delays.
"""

import time
from typing import Any, Callable

from attrs import frozen
from loguru import logger

API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Attribution headers recommended by OpenRouter.
DEFAULT_REFERER = "https://github.com/VoxelCubes/PanelCleaner"
DEFAULT_TITLE = "Panel Cleaner"


class OpenRouterError(Exception):
    """Raised when a translation request ultimately fails."""


@frozen
class ChatUsage:
    """Token usage and cost reported by the API for one request."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    model: str = ""


@frozen
class ChatResponse:
    """The assistant message content plus usage for one chat completion."""

    content: str
    usage: ChatUsage


# Status codes worth retrying: rate limiting and transient server errors.
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class OpenRouterClient:
    """A minimal OpenRouter chat-completions client with retry/backoff."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = API_URL,
        referer: str = DEFAULT_REFERER,
        title: str = DEFAULT_TITLE,
        session: Any = None,
        timeout: float = 60.0,
        max_retries: int = 4,
        backoff_base: float = 2.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not api_key:
            raise OpenRouterError(
                "No OpenRouter API key provided. Set OPENROUTER_API_KEY or configure it "
                "in the [OpenRouter] section of the config."
            )
        self.api_key = api_key
        self.base_url = base_url
        self.referer = referer
        self.title = title
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self._sleep = sleep
        if session is None:
            import requests

            session = requests.Session()
        self.session = session

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.referer,
            "X-Title": self.title,
        }

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
    ) -> ChatResponse:
        """
        Perform a chat completion, retrying on rate limits and transient errors.

        :param model: The OpenRouter model identifier.
        :param messages: The chat messages (list of {"role", "content"}).
        :param temperature: The sampling temperature.
        :return: The assistant content and usage.
        :raises OpenRouterError: If the request fails after exhausting retries.
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            # Ask OpenRouter to include cost accounting in the usage object.
            "usage": {"include": True},
        }

        last_error: str = ""
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.post(
                    self.base_url,
                    headers=self._headers(),
                    json=payload,
                    timeout=self.timeout,
                )
            except Exception as e:  # network-level error (ConnectionError, Timeout, ...)
                last_error = f"network error: {e}"
                if attempt < self.max_retries:
                    self._backoff(attempt, None)
                    continue
                raise OpenRouterError(
                    f"OpenRouter request failed after {self.max_retries + 1} attempts: {last_error}"
                ) from e

            status = response.status_code
            if status == 200:
                return self._parse_response(response, model)

            if status in RETRYABLE_STATUS and attempt < self.max_retries:
                retry_after = self._retry_after_seconds(response)
                logger.warning(
                    f"OpenRouter returned {status}, retrying "
                    f"(attempt {attempt + 1}/{self.max_retries})."
                )
                self._backoff(attempt, retry_after)
                continue

            # Non-retryable, or out of retries.
            body = self._safe_body(response)
            raise OpenRouterError(f"OpenRouter request failed with status {status}: {body}")

        raise OpenRouterError("OpenRouter request failed: retries exhausted.")

    def _backoff(self, attempt: int, retry_after: float | None) -> None:
        delay = retry_after if retry_after is not None else self.backoff_base**attempt
        self._sleep(delay)

    @staticmethod
    def _retry_after_seconds(response: Any) -> float | None:
        value = response.headers.get("Retry-After") if hasattr(response, "headers") else None
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_body(response: Any) -> str:
        try:
            return response.text[:500]
        except Exception:
            return "<no body>"

    @staticmethod
    def _parse_response(response: Any, model: str) -> ChatResponse:
        try:
            data = response.json()
        except Exception as e:
            raise OpenRouterError(f"Failed to decode OpenRouter response as JSON: {e}") from e

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise OpenRouterError(f"Unexpected OpenRouter response shape: {data}") from e

        usage_data = data.get("usage") or {}
        usage = ChatUsage(
            prompt_tokens=int(usage_data.get("prompt_tokens", 0) or 0),
            completion_tokens=int(usage_data.get("completion_tokens", 0) or 0),
            cost_usd=float(usage_data.get("cost", 0.0) or 0.0),
            model=data.get("model", model),
        )
        return ChatResponse(content=content, usage=usage)
