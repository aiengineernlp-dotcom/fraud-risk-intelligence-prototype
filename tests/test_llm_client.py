"""
SoC layer      : Tests
Responsibility : Test the LLM layer without network: the interface and errors (n° 55), the scripted
                 fake client (n° 56), the OpenAI-compatible adapter on a simulated transport (n° 57)
                 and the factory (n° 58); prove that the key never shows in an error, a repr or a log
Never does     : Open a network connection; call a real LLM; read .env or call load_config();
                 use a real key (the key below is invented)
Reference      : Architecture_Projet.md v1.3 — section 4 (D-04, D-05, D-08), section 8 (n° 55 to 59);
                 Features_Complet.md F01, F02; brief §10.5, §14; PASSATION.md §6, decisions PR 7
"""

from __future__ import annotations

import dataclasses
import socket

import pytest

from src.agent.llm.base import LLMClient, LLMError, LLMMessage, LLMResponse, LLMTimeout, LLMUnavailable


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Any real connection attempt fails the test instead of leaving the machine."""

    def refuse(*args, **kwargs):
        raise AssertionError("network access attempted in an offline test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


# --- n° 55 base.py ------------------------------------------------------------


def test_message_and_response_are_frozen():
    message = LLMMessage(role="user", content="hello")
    response = LLMResponse(text="{}", model="m", latency_seconds=0.1, input_tokens=None, output_tokens=None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        message.content = "changed"
    with pytest.raises(dataclasses.FrozenInstanceError):
        response.text = "changed"


def test_llm_client_is_abstract():
    with pytest.raises(TypeError):
        LLMClient()


def test_llm_error_family():
    timeout = LLMTimeout("LLM provider did not answer in time", kind="timeout")
    unavailable = LLMUnavailable("LLM provider error (HTTP 500)", kind="http_status", status_code=500)
    assert isinstance(timeout, LLMError) and isinstance(unavailable, LLMError)
    assert not isinstance(timeout, LLMUnavailable)
    assert (timeout.kind, timeout.status_code) == ("timeout", None)
    assert (unavailable.kind, unavailable.status_code) == ("http_status", 500)
