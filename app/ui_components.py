"""
SoC layer      : 5 — UI
Responsibility : Shared display pieces of the Streamlit pages: the prototype banner (J02), the
                 cached application resources (one load per process, I72 D3, I74 P6), the fixed
                 error and failure messages (J07, I72 D4), the band / validator badges and the
                 labels of the reviewer decisions
Never does     : Import the orchestrator (the loading function is received as a parameter, I74 P6)
                 or any src module; compute a score, a band, a priority or a validity; show
                 str(error) or a trace; render data as Markdown or HTML (data -> st.text only)
Reference      : Architecture_Projet.md v1.5 — section 1.2, section 5, section 8 (n° 66);
                 Features_Complet.md J02, J04, J07; brief §13 elements 3, 9, 12; decisions I72, I73,
                 I74 and Q-41 (one message for AppStartupError)
"""

from __future__ import annotations

from typing import Any, Callable

import streamlit as st

# Where the pages keep the selected case ID between pages (an ID only, never data).
CASE_KEY = "selected_case_id"

# J02: visible on every page.
BANNER_TEXT = (
    "Educational prototype — synthetic data only (PaySim), no real customer. "
    "The score and the summary prove nothing: a human reviewer makes every decision."
)

# I72 D4: one fixed, readable message per known error, looked up by CLASS NAME (this file never
# imports the orchestrator). The text of the error itself is never shown: it may carry a value.
ERROR_MESSAGES = {
    "AppStartupError": (  # Q-41: one message for both causes (model or configuration)
        "The application cannot start: the scoring model or the configuration is missing or "
        "unusable. Run python -m src.train, then check configs/settings.yaml and .env."
    ),
    "ToolInputError": (
        "The input was refused (unknown case ID, invalid value or comment not accepted). "
        "Nothing was changed: check it and try again."
    ),
    "ToolUnavailableError": (
        "A tool or the local database is unavailable right now. Nothing was changed: "
        "please try again."
    ),
    "ReviewAlreadyRecordedError": (
        "This case already has another decision, or it is no longer in human review. "
        "Nothing was changed; the refused attempt is recorded in the audit trail."
    ),
    "MissingPriorityError": (
        "A case in human review has no valid priority, so the review queue cannot be sorted. "
        "See the audit trail."
    ),
    "AuditUnavailableError": (
        "The audit trail could not be written, so the workflow stopped (no step without a trace). "
        "Please try again."
    ),
}
GENERAL_ERROR_MESSAGE = "An unexpected error occurred. No technical detail is shown on screen."

# J07 "validation failure" (brief §11.6): the case is VALIDATION_REJECTED.
VALIDATION_FAILURE_MESSAGE = (
    "Validation failure: the AI draft did not pass the independent validator within the bounded "
    "retries. No summary is shown as trusted: review the structured data only."
)

# J07 "tool failure": a FAILED case, by the step written in the audit (get_failure_cause).
FAILURE_MESSAGES = {
    "score": "Tool failure: the scoring tool did not answer within its bounded retries. "
             "The case is FAILED; no score is shown.",
    "evidence": "Tool failure: the evidence store did not answer within its bounded retries. "
                "The case is FAILED.",
    "draft": "Tool failure: the language model did not produce a draft within its bounded retries "
             "(timeout, refusal or unavailable). The case is FAILED.",
    "routing": "Tool failure: the review routing could not be applied. The case is FAILED.",
}
GENERAL_FAILURE_MESSAGE = "The case is FAILED. The cause is recorded in the audit trail."

# Badges: fixed texts; the value is only a key, never inserted in the Markdown.
BAND_BADGES = {"low": "Risk band: **LOW**", "medium": "Risk band: **MEDIUM**",
               "high": "Risk band: **HIGH**"}
VALIDATOR_BADGES = {"passed": "Validator: **PASSED**", "failed": "Validator: **FAILED**",
                    "not_run": "Validator: **not run** (the case stopped before validation)"}
UNKNOWN_BADGE = "**unknown**"

# Brief §13 element 10, keyed by the value of the CaseState.
DECISION_LABELS = {"CLOSED": "Approve and close", "ESCALATED": "Escalate",
                   "NEEDS_MORE_INFORMATION": "Need more information"}


def show_banner() -> None:
    st.warning(BANNER_TEXT)


@st.cache_resource(show_spinner=False)
def _cached_app(_load: Callable[[], Any]) -> Any:
    """Called once per process. The leading underscore: Streamlit does not hash the function, so
    there is one cached value. An exception is not cached: the next run tries again."""
    return _load()


def get_app(load: Callable[[], Any]) -> Any:
    """The application resources, loaded once by `load` (orchestrator.load_app, I72 D3)."""
    return _cached_app(load)


def error_message(error: BaseException) -> str:
    """The fixed message of an error: its class, or a parent class, in the table; else general."""
    for cls in type(error).__mro__:
        if cls.__name__ in ERROR_MESSAGES:
            return ERROR_MESSAGES[cls.__name__]
    return GENERAL_ERROR_MESSAGE


def show_error(error: BaseException) -> None:
    """Show the fixed message only: never str(error), never a trace (J07, I72 D4)."""
    st.error(error_message(error))


def get_app_or_stop(load: Callable[[], Any]) -> Any:
    """The resources, or (model / configuration missing…) a fixed message then st.stop(): the page
    goes no further, no database is opened (Q-19 (4))."""
    try:
        return get_app(load)
    except Exception as error:  # st.stop() raises a BaseException: never caught here
        show_error(error)
        st.stop()


def failure_message(cause: dict[str, str] | None) -> str:
    """Readable message of a FAILED case, from {step, cause} of the audit (I72 D4)."""
    if cause is None:
        return GENERAL_FAILURE_MESSAGE
    return FAILURE_MESSAGES.get(cause.get("step", ""), GENERAL_FAILURE_MESSAGE)


def show_band(band: str) -> None:
    st.markdown(BAND_BADGES.get(band, "Risk band: " + UNKNOWN_BADGE))


def show_validator_status(status: str) -> None:
    st.markdown(VALIDATOR_BADGES.get(status, "Validator: " + UNKNOWN_BADGE))


def decision_label(decision: Any) -> str:
    """Label of a reviewer decision (a CaseState); unknown -> its value as it is."""
    value = getattr(decision, "value", decision)
    return DECISION_LABELS.get(value, str(value))
