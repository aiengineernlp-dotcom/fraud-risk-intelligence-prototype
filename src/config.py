"""
SoC layer      : Transverse
Responsibility : Load `.env` and `configs/settings.yaml` into one typed, read-only object
Never does     : Business logic; print or log a secret; hold the decision threshold or band bounds
                 (single source: model_metadata.json, D-12 / I20)
Reference      : Architecture_Projet.md v1.1 — section 4 (D-04, D-08, D-12), section 8 (n° 07)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SETTINGS_PATH = REPO_ROOT / "configs" / "settings.yaml"
DEFAULT_ENV_PATH = REPO_ROOT / ".env"

ALLOWED_PROVIDERS = ("fake", "openai_compatible")
DEFAULT_PROVIDER = "fake"  # offline, no cost: safe when LLM_PROVIDER is empty


class ConfigError(Exception):
    """Raised when the configuration is missing or invalid. Never contains a secret value."""


class Secret:
    """Wraps a secret so that print(), str() and repr() never show it."""

    def __init__(self, value: str) -> None:
        self._value = value

    def reveal(self) -> str:
        """Return the real value. Call it only where the value is sent to its provider."""
        return self._value

    def is_set(self) -> bool:
        return bool(self._value)

    def redact(self, text: str) -> str:
        """Return `text` with every occurrence of this secret replaced by ********.

        Lets logging hide the key without ever reading it (reveal() stays in the LLM client only).
        """
        if not self._value:
            return text
        return text.replace(self._value, "********")

    def __repr__(self) -> str:
        return "Secret('********')" if self._value else "Secret('')"

    __str__ = __repr__


@dataclass(frozen=True)
class RetrySettings:
    max_retries: int
    timeout_seconds: float


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    base_url: str
    model: str
    api_key: Secret


@dataclass(frozen=True)
class Paths:
    raw_data_dir: Path
    runtime_db: Path
    demo_cases: Path
    evidence_store: Path
    model_pipeline: Path
    mlp_state: Path
    model_metadata: Path
    metrics_dir: Path
    figures_dir: Path
    prohibited_terms: Path


@dataclass(frozen=True)
class AppConfig:
    tool_retries: RetrySettings
    llm_retries: RetrySettings
    near_threshold_margin: float | None  # None until fixed at J3 (I08)
    paths: Paths
    llm: LLMSettings


def load_config(
    settings_path: Path = DEFAULT_SETTINGS_PATH,
    env_path: Path = DEFAULT_ENV_PATH,
) -> AppConfig:
    """Read settings.yaml and .env, check them, and return one read-only AppConfig."""
    settings = _read_yaml(settings_path)
    # Variables already set in the shell win over .env (override=False).
    load_dotenv(env_path, override=False)
    return AppConfig(
        tool_retries=_retry(settings, "tools", "max_retries"),
        llm_retries=_retry(settings, "llm", "max_retries_after_rejection"),
        near_threshold_margin=_margin(settings),
        paths=_paths(settings),
        llm=_llm_from_environment(),
    )


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigError(f"Settings file not found: {path}")
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)  # safe_load: never builds arbitrary Python objects
    if not isinstance(data, dict):
        raise ConfigError(f"Settings file is empty or not a mapping: {path}")
    return data


def _section(data: dict[str, Any], *keys: str) -> Any:
    node: Any = data
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            raise ConfigError(f"Missing setting: {'.'.join(keys)}")
        node = node[key]
    return node


def _retry(settings: dict[str, Any], caller: str, retries_key: str) -> RetrySettings:
    retries = _section(settings, "retries", caller, retries_key)
    timeout = _section(settings, "retries", caller, "timeout_seconds")
    if not isinstance(retries, int) or isinstance(retries, bool) or retries < 0:
        raise ConfigError(f"retries.{caller}.{retries_key} must be an integer >= 0")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise ConfigError(f"retries.{caller}.timeout_seconds must be a number > 0")
    return RetrySettings(max_retries=retries, timeout_seconds=float(timeout))


def _margin(settings: dict[str, Any]) -> float | None:
    margin = _section(settings, "routing", "near_threshold_margin")
    if margin is None:
        return None
    if not isinstance(margin, (int, float)) or isinstance(margin, bool) or not 0 <= margin <= 1:
        raise ConfigError("routing.near_threshold_margin must be empty or a number between 0 and 1")
    return float(margin)


def _paths(settings: dict[str, Any]) -> Paths:
    raw = _section(settings, "paths")
    if not isinstance(raw, dict):
        raise ConfigError("paths must be a mapping")
    values = {}
    for name in Paths.__dataclass_fields__:
        if name not in raw or not raw[name]:
            raise ConfigError(f"Missing setting: paths.{name}")
        values[name] = REPO_ROOT / str(raw[name])
    return Paths(**values)


def _llm_from_environment() -> LLMSettings:
    provider = os.getenv("LLM_PROVIDER", "").strip() or DEFAULT_PROVIDER
    if provider not in ALLOWED_PROVIDERS:
        raise ConfigError(f"LLM_PROVIDER must be one of {ALLOWED_PROVIDERS}, got '{provider}'")
    llm = LLMSettings(
        provider=provider,
        base_url=os.getenv("LLM_BASE_URL", "").strip(),
        model=os.getenv("LLM_MODEL", "").strip(),
        api_key=Secret(os.getenv("LLM_API_KEY", "").strip()),
    )
    if provider == "openai_compatible":
        missing = [name for name, ok in (
            ("LLM_BASE_URL", llm.base_url),
            ("LLM_MODEL", llm.model),
            ("LLM_API_KEY", llm.api_key.is_set()),
        ) if not ok]
        if missing:
            # Names only, never values.
            raise ConfigError(f"LLM_PROVIDER=openai_compatible needs: {', '.join(missing)} in .env")
    return llm