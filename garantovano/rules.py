"""Deterministic fast path: common needs -> NSZU package ids, before any model call.

The model is asked only when no rule in config.KEYWORD_RULES matches; both paths return the same
MatchResult contract, and match() keeps all its fail-closed checks for the model path.
"""
from __future__ import annotations

from typing import Mapping

from . import config
from .match import LLMPort, is_emergency_text, match
from .models import MatchResult, Package


def keyword_packages(text: str, packages: Mapping[str, Package]) -> tuple[str, ...]:
    """Package ids of every matching rule, in rule order, de-duplicated, at most MAX_PACKAGES."""
    normalized = text.casefold()
    ids: list[str] = []
    for groups, package_ids in config.KEYWORD_RULES:
        if all(any(stem in normalized for stem in group) for group in groups):
            ids.extend(pid for pid in package_ids if pid in packages)
    return tuple(dict.fromkeys(ids))[: config.MAX_PACKAGES]


def understand(text: str, packages: Mapping[str, Package], llm: LLMPort) -> MatchResult:
    """Rules first (instant, predictable), the model only for everything else."""
    cleaned = text.strip()
    if 0 < len(cleaned) <= config.MAX_INPUT_CHARS:
        ids = keyword_packages(cleaned, packages)
        if ids:
            return MatchResult(ids, is_emergency_text(cleaned), needs_picker=False, reason="rule")
    return match(text, packages, llm)
