"""
SoC layer      : 4 — LLM Interpreter
Responsibility : The replaceable LLM interface: the message and response shapes, the abstract
                 LLMClient with its single method complete(), and the two named errors
                 (LLMTimeout, LLMUnavailable) every client raises
Never does     : Call a provider; read .env or a key; retry (retry.py, n° 62, does); parse or judge
                 the reply (the validator, n° 51, does); compute a score, a band or a validity
Reference      : Architecture_Projet.md v1.3 — section 4 (D-03, D-04, D-08), section 6, section 8
                 (n° 55); Features_Complet.md F01; brief §10.5; PASSATION.md §6, decisions PR 7
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

# Only two roles: the instructions (system) and the case material (user). Keeping them apart is what
# lets prompt_builder.py (n° 60) never put a case note in the instructions (Architecture §5).
Role = Literal["system", "user"]

# Fixed error codes. They are written in the code, never copied from a provider message, so an error
# can never carry a key that a provider echoed back. retry.py (n° 62) decides on them.
ErrorKind = Literal[
    "timeout",          # the provider did not answer within the delay
    "connection",       # the provider could not be reached
    "rate_limited",     # HTTP 429
    "auth",             # HTTP 401 / 403: a new attempt cannot help
    "http_status",      # any other HTTP error status
    "empty_response",   # an answer without text
    "bad_response",     # any other provider-side failure
]


@dataclass(frozen=True)
class LLMMessage:
    """One message sent to the LLM."""

    role: Role
    content: str


@dataclass(frozen=True)
class LLMResponse:
    """The raw reply of one call, with what the report needs (brief §10.5: cost and latency)."""

    text: str                    # raw reply, never parsed here (the validator does)
    model: str
    latency_seconds: float
    input_tokens: int | None     # None when the provider does not report usage
    output_tokens: int | None


class LLMError(Exception):
    """Base of the LLM errors. The message is a fixed text written in the code, never a provider text."""

    def __init__(self, message: str, kind: ErrorKind, status_code: int | None = None) -> None:
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code


class LLMTimeout(LLMError):
    """The provider did not answer within the delay given to the client."""


class LLMUnavailable(LLMError):
    """The provider could not give a usable answer (connection, HTTP error, empty reply...)."""


class LLMClient(ABC):
    """What the orchestrator knows about any LLM. Changing provider = another class behind this one."""

    @abstractmethod
    def complete(self, messages: Sequence[LLMMessage]) -> LLMResponse:
        """Send the messages once and return the reply.

        One single attempt: no retry here (retry.py does). The delay is fixed when the client is built.
        Raises LLMTimeout or LLMUnavailable; never returns an empty text.
        """
