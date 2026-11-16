"""Understanding the user's need -> NSZU package ids.   OWNER: Діма (issue "D1").

The model only CHOOSES ids from data/packages.csv. It never answers the user, never gives medical
advice, and its output is never trusted without validation. Any problem -> needs_picker=True (fail closed).

Contract for match() (tests/test_match.py is the spec):
  1. text stripped; empty -> MatchResult((), emergency=False, needs_picker=True, reason="empty"), LLM NOT called.
  2. emergency = is_emergency_text(text)  (deterministic, config.EMERGENCY_KEYWORDS), computed BEFORE the LLM.
  3. len(text) > config.MAX_INPUT_CHARS -> needs_picker, reason="too_long", LLM NOT called (emergency still set).
  4. call llm.classify(text, packages); ANY exception -> needs_picker, reason="llm_error".
  5. validate: 1..MAX_PACKAGES ids, all exist in packages -> else needs_picker, reason "invalid" / "unknown_id";
     confidence < MIN_CONFIDENCE -> needs_picker, reason="low_confidence".
  6. final emergency = keyword_emergency OR llm.emergency.
  7. success -> MatchResult(tuple(ids, de-duplicated, order kept), emergency, needs_picker=False, reason="ok").

AnthropicClassifier (adapter, Python SDK `anthropic`):
  - client = anthropic.Anthropic()  (key from ANTHROPIC_API_KEY env / Streamlit secrets; never in code)
  - client.with_options(timeout=config.LLM_TIMEOUT_S, max_retries=1).messages.parse(
        model=config.MODEL, max_tokens=1024, output_config={"effort": "low"},
        system=<rules + the package list "id: name">, messages=[{"role": "user", "content": text}],
        output_format=<pydantic model {package_ids: list[str], emergency: bool, confidence: float}>)
  - if response.stop_reason == "refusal" or parsed_output is None -> raise (match() turns it into the picker).
  - user text goes ONLY into the user message (prompt-injection hygiene); system prompt is static.
"""
from __future__ import annotations

from typing import Mapping, Protocol

from . import config
from .models import LLMClassification, MatchResult, Package


class LLMPort(Protocol):
    def classify(self, text: str, packages: Mapping[str, Package]) -> LLMClassification: ...


class AnthropicClassifier:
    """Real adapter for LLMPort. TODO(Діма)."""

    def __init__(self, model: str = config.MODEL, timeout_s: float = config.LLM_TIMEOUT_S) -> None:
        self.model = model
        self.timeout_s = timeout_s

    def classify(self, text: str, packages: Mapping[str, Package]) -> LLMClassification:
        raise NotImplementedError("D1: implement AnthropicClassifier.classify")


def is_emergency_text(text: str) -> bool:
    """Case-insensitive substring check against config.EMERGENCY_KEYWORDS. TODO(Діма)."""
    raise NotImplementedError("D1: implement is_emergency_text")


def match(text: str, packages: Mapping[str, Package], llm: LLMPort) -> MatchResult:
    """See the module docstring. TODO(Діма)."""
    raise NotImplementedError("D1: implement match")
