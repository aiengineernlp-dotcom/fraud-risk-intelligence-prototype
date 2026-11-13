"""
SoC layer      : 4 — LLM Interpreter
Responsibility : Choose the LLM client from the configuration already loaded (LLM_PROVIDER, D-04) and
                 give it its settings and its delay (retries.llm.timeout_seconds of settings.yaml)
Never does     : Read .env or the environment itself (src/config.py, load_config, does); call the LLM;
                 retry; hold a delay or any other decision value of its own
Reference      : Architecture_Projet.md v1.3 — section 4 (D-04, D-05, D-08), section 6, section 8
                 (n° 58); Features_Complet.md F01, F02; PASSATION.md §6, decisions PR 7
"""

from __future__ import annotations

from src.agent.llm.base import LLMClient
from src.agent.llm.fake_client import DraftFacts, FakeLLMClient
from src.agent.llm.openai_compatible_client import OpenAICompatibleClient
from src.config import AppConfig


def create_llm_client(
    config: AppConfig,
    *,
    fake_scenario: str = "valid",
    fake_facts: DraftFacts | None = None,
) -> LLMClient:
    """Return the client named by config.llm.provider.

    fake              -> FakeLLMClient(fake_scenario, fake_facts); the facts are required, because the
                         fake copies the official values of the case into its draft.
    openai_compatible -> OpenAICompatibleClient with the delay of settings.yaml (one attempt per call).
    """
    provider = config.llm.provider
    if provider == "fake":
        if fake_facts is None:
            raise ValueError("The fake LLM client needs the official facts of the case (fake_facts)")
        return FakeLLMClient(fake_scenario, fake_facts)
    if provider == "openai_compatible":
        return OpenAICompatibleClient(config.llm, timeout_seconds=config.llm_retries.timeout_seconds)
    # load_config() already refuses other values; kept so that a hand-built config cannot slip through.
    raise ValueError(f"Unknown LLM provider '{provider}'")
