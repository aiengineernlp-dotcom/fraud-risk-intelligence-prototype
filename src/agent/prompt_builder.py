"""
SoC layer      : 4 — LLM Interpreter
Responsibility : Build the two LLM messages of one case from the versioned template (n° 60): the fixed
                 instructions (system) and a delimited data section (user) holding the minimal context
                 only (F04 fields + the untrusted case note, founder decision PR 8 (a))
Never does     : Put case data or the case note in the system message; send a field outside
                 ALLOWED_CONTEXT_FIELDS or a label; round or compute the score; call the LLM; write
                 the audit (the orchestrator, n° 63, records PROMPT_VERSION)
Reference      : Architecture_Projet.md v1.3 — section 1.2, section 5, section 8 (n° 61);
                 Features_Complet.md F03, F04, F05; brief §10.1, §10.3, §12; PASSATION.md §6,
                 decisions PR 6 (a) and PR 8
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from pathlib import Path

from src.agent.domain import EvidenceItem, ScoreResult
from src.agent.llm.base import LLMMessage
from src.data.case_input import CaseInput

# The template version. The orchestrator (PR 10) writes it in the drafting audit event (F03).
PROMPT_VERSION = "investigation_summary_v1"
DEFAULT_TEMPLATE_PATH = Path(__file__).parent / "prompts" / f"{PROMPT_VERSION}.md"

# Fixed markers of the template file.
_VERSION_PREFIX = "prompt_version:"
_SYSTEM_HEADER = "=== SYSTEM ==="
_USER_HEADER = "=== USER ==="
_PLACEHOLDER = "{{CASE_DATA}}"

# Delimiters of the data section, added by the code (not by the template) next to the escaping that
# makes them impossible to close from the data.
DATA_OPEN_TAG = "<case_data>"
DATA_CLOSE_TAG = "</case_data>"

# Facts the LLM must copy unchanged. The names are exactly those of investigation_schema.py
# (n° 50), otherwise the validator would reject every real draft (tested).
COPIED_FIELDS = ("case_id", "risk_level", "model_score", "model_version")

# The only keys of the data section: F04 (case ID, official score and band, verified features,
# approved evidence, model version) + the untrusted case note (founder decision PR 8 (a)).
# The threshold is not in F04, so it is not sent.
ALLOWED_CONTEXT_FIELDS = frozenset({*COPIED_FIELDS, "transaction", "evidence", "case_note_untrusted"})


class PromptTemplateError(ValueError):
    """The template file is missing or does not have the expected shape."""


def load_template(template_path: Path = DEFAULT_TEMPLATE_PATH) -> tuple[str, str]:
    """Read the template and return (system text, user text), split BEFORE any data is inserted.

    Read at each call (small file, no global cache, like decision PR 5 (c)).
    """
    try:
        text = Path(template_path).read_text(encoding="utf-8")
    except OSError as error:
        raise PromptTemplateError(f"Prompt template not readable: {template_path}") from error

    first_line, _, rest = text.partition("\n")
    if first_line.strip() != f"{_VERSION_PREFIX} {PROMPT_VERSION}":
        raise PromptTemplateError(f"Prompt template version is not {PROMPT_VERSION}")
    if rest.count(_SYSTEM_HEADER) != 1 or rest.count(_USER_HEADER) != 1:
        raise PromptTemplateError("Prompt template needs one SYSTEM header and one USER header")

    before_system, _, after_system = rest.partition(_SYSTEM_HEADER)
    system_text, _, user_text = after_system.partition(_USER_HEADER)
    if before_system.strip():
        raise PromptTemplateError("Prompt template has text before the SYSTEM header")
    # The data may only go in the user message, once (Architecture §5: never in the instructions).
    if _PLACEHOLDER in system_text:
        raise PromptTemplateError("The data placeholder must not be in the SYSTEM section")
    if user_text.count(_PLACEHOLDER) != 1:
        raise PromptTemplateError("The USER section needs the data placeholder exactly once")
    return system_text.strip(), user_text.strip()


def build_context(case_input: CaseInput, score: ScoreResult, evidence: Sequence[EvidenceItem]) -> dict:
    """The minimal context, built field by field (never a whole object copied)."""
    if not math.isfinite(score.score):
        raise ValueError("The official score must be a finite number")
    return {
        "case_id": case_input.case_id,
        "risk_level": score.risk_band,
        "model_score": score.score,  # the same float: json writes repr(), never rounded (PR 6 (a))
        "model_version": score.model_version,
        "transaction": case_input.transaction(),  # the 7 verified FEATURE fields only
        "evidence": [{"source_id": item.source_id, "text": item.text} for item in evidence],
        "case_note_untrusted": case_input.case_note,  # None when there is no note
    }


def render_data_section(context: dict) -> str:
    """Serialise the context as JSON between the delimiters, with < and > escaped.

    After escaping, the JSON holds no "<" at all, so no value (note, evidence text, case_id) can write
    </case_data> and close the section. \\u003c and \\u003e are valid JSON escapes: nothing is lost,
    json.loads gives back the original text.
    """
    if set(context) != ALLOWED_CONTEXT_FIELDS:
        raise ValueError(f"Context fields must be exactly {sorted(ALLOWED_CONTEXT_FIELDS)}")
    data = json.dumps(context, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2)
    data = data.replace("<", "\\u003c").replace(">", "\\u003e")
    return f"{DATA_OPEN_TAG}\n{data}\n{DATA_CLOSE_TAG}"


def build_messages(
    case_input: CaseInput,
    score: ScoreResult,
    evidence: Sequence[EvidenceItem],
    *,
    template_path: Path = DEFAULT_TEMPLATE_PATH,
) -> list[LLMMessage]:
    """Return [system: fixed instructions, user: preamble + delimited data section].

    The template is split into SYSTEM and USER first; the data is then put in the USER text by one
    single substitution. The system message never depends on the case.
    """
    system_text, user_text = load_template(template_path)
    data_section = render_data_section(build_context(case_input, score, evidence))
    user_content = user_text.replace(_PLACEHOLDER, data_section, 1)
    return [LLMMessage(role="system", content=system_text), LLMMessage(role="user", content=user_content)]
