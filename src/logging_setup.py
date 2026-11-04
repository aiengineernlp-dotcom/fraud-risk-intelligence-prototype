"""
SoC layer      : Transverse
Responsibility : Configure technical logging to the terminal and hide every secret before a line is written
Never does     : Write audit events (write_audit_event.py, layer 3, does); read a secret value
               (it calls Secret.redact, never reveal); write log files
Reference      : Architecture_Projet.md v1.1 — section 8 (n° 08); brief §12 and §14 ("Secrets are not written to logs")
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterable

from src.config import AppConfig, Secret

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_HANDLER_NAME = "capstone-terminal"


class RedactingFormatter(logging.Formatter):
    """Formats a log line, traceback included, then replaces every known secret by ********."""

    def __init__(self, secrets: Iterable[Secret], fmt: str = LOG_FORMAT) -> None:
        super().__init__(fmt)
        self._secrets = tuple(secret for secret in secrets if secret.is_set())

    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)  # the full line: message, arguments and traceback
        for secret in self._secrets:
            text = secret.redact(text)
        return text


def setup_logging(config: AppConfig, level: int = logging.INFO) -> logging.Logger:
    """Attach one redacting terminal handler to the root logger. Safe to call more than once."""
    root = logging.getLogger()
    for handler in list(root.handlers):
        if handler.get_name() == _HANDLER_NAME:
            root.removeHandler(handler)  # no duplicate lines when called twice
    handler = logging.StreamHandler(sys.stderr)
    handler.set_name(_HANDLER_NAME)
    handler.setFormatter(RedactingFormatter([config.llm.api_key]))
    root.addHandler(handler)
    # INFO by default: some HTTP libraries print request details only at DEBUG.
    root.setLevel(level)
    return root