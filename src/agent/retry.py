"""
SoC layer      : 4 — LLM Interpreter + orchestrator
Responsibility : The single place for bounded retries and maximum delays (D-08): call a tool or the
                 LLM at most 1 + max_retries times, measure each attempt, count a too-slow attempt
                 as a timeout, hand one record per attempt to the caller's audit function, and say
                 why the attempts ran out (timeout, failed, rejected)
Never does     : Loop without a limit; wait or sleep between attempts; cut a call (no thread, no
                 signal: the delay is measured, decision PR 9 (c)); retry a bad input
                 (ToolInputError) or an auth error (kind="auth"); judge a draft itself (the caller's
                 `check` calls the validator); write to the database (the audit function does);
                 copy an error text into a record (a provider text may carry a key, PASSATION §5)
Reference      : Architecture_Projet.md v1.3 — section 3 (Flux 2a, 2b), section 4 (D-07, D-08),
                 section 5, section 8 (n° 62); Features_Complet.md G09, H06; brief §11.3, §11.6,
                 §12.1; PASSATION.md §6, decisions PR 5 (a), PR 7 (4), PR 9 (a)-(d)
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, TypeVar

from src.agent.llm.base import LLMError
from src.agent.tools.errors import ToolInputError, ToolUnavailableError
from src.config import RetrySettings

T = TypeVar("T")

# The four `result` values of an audit event (Architecture §10.2).
RESULT_OK = "ok"
RESULT_FAILED = "failed"
RESULT_TIMEOUT = "timeout"
RESULT_REJECTED = "rejected"

# Error code written for an attempt that was too slow but did not raise (decision PR 9 (c)).
ERROR_TOO_SLOW = "too_slow"


@dataclass(frozen=True)
class AttemptRecord:
    """What happened in one attempt. The caller turns it into one audit event."""

    step: str                    # e.g. "score", "evidence", "draft"
    attempt: int                 # 1, 2, 3...
    max_attempts: int            # 1 + max_retries
    result: str                  # ok / failed / timeout / rejected
    duration_seconds: float      # measured, never cut (decision PR 9 (c))
    timeout_seconds: float       # the maximum delay, from settings.yaml
    error: str | None            # fixed code (class name or "llm:<kind>"), never the error text
    reasons: tuple[str, ...]     # the validator's reasons when result is "rejected"

    def details(self) -> dict[str, Any]:
        """JSON-ready details for AuditEvent.details (no secret: only fixed codes and numbers)."""
        return {
            "step": self.step,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "duration_seconds": self.duration_seconds,
            "timeout_seconds": self.timeout_seconds,
            "error": self.error,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class RetryOutcome:
    """The end of the attempts. `value` is None when they ran out: nothing is shown as trusted."""

    ok: bool
    value: Any | None
    attempts: int
    cause: str | None            # timeout / failed / rejected when ok is False
    last_reasons: tuple[str, ...]


def _check_settings(settings: RetrySettings) -> None:
    # config.py already checks settings.yaml; this guards an object built by hand.
    retries, timeout = settings.max_retries, settings.timeout_seconds
    if not isinstance(retries, int) or isinstance(retries, bool) or retries < 0:
        raise ValueError("max_retries must be an integer >= 0")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not timeout > 0 \
            or not math.isfinite(timeout):
        raise ValueError("timeout_seconds must be a finite number > 0")


def _error_code(error: Exception) -> str:
    """A fixed code for the audit: never str(error), which may carry a key echoed by a provider."""
    if isinstance(error, LLMError):
        return f"llm:{error.kind}"
    return type(error).__name__


def _is_never_retried(error: Exception) -> bool:
    """A bad input, or an auth error: a new attempt would fail the same way (decision PR 7 (4))."""
    if isinstance(error, ToolInputError):
        return True
    return isinstance(error, LLMError) and error.kind == "auth"


def _result_of_error(error: Exception) -> str:
    if isinstance(error, LLMError) and error.kind == "timeout":
        return RESULT_TIMEOUT
    return RESULT_FAILED


def run_with_retries(
    step: str,
    call: Callable[[], T],
    *,
    settings: RetrySettings,
    audit: Callable[[AttemptRecord], None],
    check: Callable[[T], Sequence[str]] | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> RetryOutcome:
    """Call `call()` at most 1 + settings.max_retries times and return how it ended.

    For each attempt, in this order:
    - ToolInputError, or an LLMError with kind "auth": audited as "failed", then the ORIGINAL error
      is raised again (never retried; the orchestrator decides, decision PR 9);
    - ToolUnavailableError or any other LLMError: "failed" or "timeout", retried;
    - a value that came later than timeout_seconds: "timeout", the value is dropped, retried;
    - `check(value)` returns reasons: "rejected", retried (H06); `check` calls the validator;
    - otherwise: "ok", the value is returned.
    Any other exception is a bug: it is not caught and goes up at once.
    If the audit function raises, its error goes up too: the workflow never goes on without a trace.
    """
    _check_settings(settings)
    max_attempts = 1 + settings.max_retries
    timeout = float(settings.timeout_seconds)
    cause: str | None = None
    last_reasons: tuple[str, ...] = ()

    for attempt in range(1, max_attempts + 1):
        start = clock()
        error: Exception | None = None
        value = None
        try:
            value = call()
        except (ToolUnavailableError, ToolInputError, LLMError) as caught:
            error = caught
        duration = clock() - start

        def record(result: str, code: str | None, reasons: tuple[str, ...] = ()) -> None:
            audit(AttemptRecord(step, attempt, max_attempts, result, duration, timeout, code, reasons))

        if error is not None:
            result = _result_of_error(error)
            record(result, _error_code(error))
            if _is_never_retried(error):
                # Re-raised outside the except block on purpose: same rule as the LLM client (§5).
                raise error
            cause, last_reasons = result, ()
            continue

        # Measured, not cut (decision PR 9 (c)): a late answer counts as a timeout.
        if duration > timeout:
            record(RESULT_TIMEOUT, ERROR_TOO_SLOW)
            cause, last_reasons = RESULT_TIMEOUT, ()
            continue

        reasons = tuple(check(value)) if check is not None else ()
        if reasons:
            record(RESULT_REJECTED, None, reasons)
            cause, last_reasons = RESULT_REJECTED, reasons
            continue

        record(RESULT_OK, None)
        return RetryOutcome(ok=True, value=value, attempts=attempt, cause=None, last_reasons=())

    # All attempts used: no value is returned, so no rejected draft can be shown as trusted.
    return RetryOutcome(ok=False, value=None, attempts=max_attempts, cause=cause,
                        last_reasons=last_reasons)
