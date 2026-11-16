"""Shared data contracts. Every module talks through these types only."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Package:
    """One NSZU medical-guarantee package (row of data/packages.csv)."""
    id: str
    name: str
    group: str


@dataclass(frozen=True)
class Facility:
    """One facility division with coordinates and the packages it is contracted for."""
    division_id: str
    legal_entity_name: str
    division_name: str
    division_type: str
    phone: str
    region: str          # e.g. "М.КИЇВ", "ЛЬВІВСЬКА"
    settlement: str      # e.g. "КИЇВ"
    address: str
    lat: float
    lng: float
    package_ids: frozenset[str]


@dataclass(frozen=True)
class LLMClassification:
    """Raw answer of the LLM port. UNTRUSTED: match.py must validate it."""
    package_ids: list[str]
    emergency: bool
    confidence: float


@dataclass(frozen=True)
class MatchResult:
    """Validated result of understanding the user's need."""
    package_ids: tuple[str, ...]   # 0..MAX_PACKAGES ids that exist in packages.csv
    emergency: bool                # True -> UI shows "Дзвоніть 103" before anything else
    needs_picker: bool             # True -> UI shows the manual package picker (fail closed)
    reason: str                    # "ok" | "empty" | "too_long" | "llm_error" | "invalid" | "unknown_id" | "low_confidence"


@dataclass(frozen=True)
class SearchResult:
    facility: Facility
    distance_km: float
