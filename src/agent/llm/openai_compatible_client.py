"""
SoC layer      : 4 — LLM Interpreter
Responsibility : The single adapter to any provider or local server speaking the OpenAI-compatible
                 protocol (D-04): one chat completion per call, within the delay received from the
                 factory, provider failures turned into LLMTimeout / LLMUnavailable with a fixed message
Never does     : Read .env or the environment (the factory gives the settings); retry (max_retries=0,
                 retry.py, n° 62, decides); copy a provider error text or chain a provider exception
                 (either may contain the key); log the key, the messages, the reply or the base URL;
                 parse or judge the reply; set model parameters (temperature... : Q-22, none for now)
Reference      : Architecture_Projet.md v1.3 — section 4 (D-04, D-08), section 6, section 8 (n° 57);
                 Features_Complet.md F01; brief §10.5, §14 ("Secrets are not written to logs");
                 PASSATION.md §6, decisions PR 7
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence

import openai

from src.agent.llm.base import (
    ErrorKind,
    LLMClient,
    LLMError,
    LLMMessage,
    LLMResponse,
    LLMTimeout,
    LLMUnavailable,
)
from src.config import LLMSettings

log = logging.getLogger(__name__)

# Fixed messages, written here. A provider message is never copied: a provider can echo the key
# back (checked on openai 3.45.0: a 401 says "Incorrect API key provided: <the key>").
_FIXED_MESSAGES: dict[ErrorKind, str] = {
    "timeout": "LLM provider did not answer in time",
    "connection": "LLM provider could not be reached",
    "rate_limited": "LLM provider refused the call: rate limit reached",
    "auth": "LLM provider refused the credentials",
    "http_status": "LLM provider returned an error status",
    "empty_response": "LLM provider returned an empty answer",
    "bad_response": "LLM provider returned an unusable answer",
}


class OpenAICompatibleClient(LLMClient):
    """One OpenAI-compatible endpoint. Built once by the factory; the key never leaves the SDK object."""

    def __init__(self, settings: LLMSettings, timeout_seconds: float, http_client=None) -> None:
        # Names only in these messages, never values.
        missing = [name for name, ok in (
            ("LLM_BASE_URL", settings.base_url),
            ("LLM_MODEL", settings.model),
            ("LLM_API_KEY", settings.api_key.is_set()),
        ) if not ok]
        if missing:
            raise ValueError(f"OpenAI-compatible client needs: {', '.join(missing)}")
        if not timeout_seconds > 0:
            raise ValueError("timeout_seconds must be > 0")

        self._model = settings.model
        self._secret = settings.api_key  # kept as Secret (masked repr) for redact() only
        self._timeout_seconds = float(timeout_seconds)
        # The only reveal() of the project: the key goes straight to the SDK, nowhere else.
        # max_retries=0: one single attempt, new attempts belong to retry.py (founder decision PR 7 (a)).
        # http_client: a simulated transport in the tests; None = the SDK default.
        self._client = openai.OpenAI(
            api_key=settings.api_key.reveal(),
            base_url=settings.base_url,
            timeout=self._timeout_seconds,
            max_retries=0,
            http_client=http_client,
        )

    @property
    def timeout_seconds(self) -> float:
        return self._timeout_seconds

    def complete(self, messages: Sequence[LLMMessage]) -> LLMResponse:
        start = time.monotonic()
        # Founder decision PR 7 (1): inside the except blocks we only keep the error kind and the
        # status code; the LLMError is raised AFTER the try statement, so neither __cause__ nor
        # __context__ points to the SDK exception (whose text may contain the key).
        failed_kind: ErrorKind | None = None
        status_code: int | None = None
        completion = None
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": message.role, "content": message.content} for message in messages],
            )
        # Order matters: APITimeoutError is a subclass of APIConnectionError, and the status errors
        # are subclasses of APIStatusError.
        except openai.APITimeoutError:
            failed_kind = "timeout"
        except openai.APIConnectionError:
            failed_kind = "connection"
        except openai.RateLimitError as error:
            failed_kind, status_code = "rate_limited", error.status_code
        except (openai.AuthenticationError, openai.PermissionDeniedError) as error:
            failed_kind, status_code = "auth", error.status_code
        except openai.APIStatusError as error:
            failed_kind, status_code = "http_status", error.status_code
        except openai.OpenAIError:
            failed_kind = "bad_response"
        latency = time.monotonic() - start

        if failed_kind is None:
            text, input_tokens, output_tokens = _read_completion(completion)
            if not text:
                failed_kind = "empty_response"
        if failed_kind is not None:
            raise self._error(failed_kind, status_code, latency)

        log.info(
            "LLM call ok: model=%s latency=%.3fs input_tokens=%s output_tokens=%s",
            self._model, latency, input_tokens, output_tokens,
        )
        return LLMResponse(
            text=self._secret.redact(text),  # in case a server echoes the key in its answer
            model=self._model,
            latency_seconds=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    def _error(self, kind: ErrorKind, status_code: int | None, latency: float) -> LLMError:
        """Build the named error from fixed parts only (kind, status code), and log one line."""
        message = _FIXED_MESSAGES[kind]
        if status_code is not None:
            message = f"{message} (HTTP {status_code})"
        log.warning("LLM call failed: model=%s kind=%s latency=%.3fs", self._model, kind, latency)
        error_class = LLMTimeout if kind == "timeout" else LLMUnavailable
        # redact() as a last safety net: the message is already a fixed text.
        return error_class(self._secret.redact(message), kind=kind, status_code=status_code)

    def __repr__(self) -> str:
        # No key, and no base URL either (a URL can hold credentials, user:password@host).
        return f"OpenAICompatibleClient(model='{self._model}')"

    __str__ = __repr__


def _read_completion(completion) -> tuple[str, int | None, int | None]:
    """Return (text, input tokens, output tokens); an empty text when the answer has none."""
    choices = getattr(completion, "choices", None) or []
    if not choices:
        return "", None, None
    message = getattr(choices[0], "message", None)
    text = (getattr(message, "content", None) or "").strip()
    usage = getattr(completion, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", None)
    output_tokens = getattr(usage, "completion_tokens", None)
    return text, input_tokens, output_tokens
