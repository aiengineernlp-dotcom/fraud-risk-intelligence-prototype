"""
SoC layer      : 3 — Logic Engine
Responsibility : Name the errors every tool raises, in two families the caller can tell apart:
                 a bad input (never retried) and an unavailable resource (retried, then FAILED)
Never does     : Retry, wait or decide a state (retry.py n° 62 and the orchestrator n° 63 do);
                 put a secret, a case note or audit details in a message
Reference      : Architecture_Projet.md v1.3 — section 1.2, section 8 (n° 44 to 47), D-07, D-08;
                 PASSATION.md §6, decisions PR 5 (a), (b), (e) — file added at PR 5 (founder GO)
"""

from __future__ import annotations


class ToolError(Exception):
    """Base of every tool error. The original error is kept as __cause__ (raise ... from)."""


class ToolInputError(ToolError):
    """The input is invalid: a new attempt would fail the same way, so it is never retried."""


class DuplicateSubmissionError(ToolInputError):
    """The case already exists (D-07): it is not created twice.

    A subclass of ToolInputError (never retried); the orchestrator can catch it on its own
    and carry on with the existing case instead of failing it.
    """

    def __init__(self, case_id: str) -> None:
        self.case_id = case_id
        super().__init__(f"Case already submitted: {case_id}")


class ToolUnavailableError(ToolError):
    """A resource failed (broken store, locked database, unusable model).

    Not the caller's fault: retry.py may try again, then the case goes to FAILED (D-08).
    """
