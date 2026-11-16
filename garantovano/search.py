"""Deterministic search over open data.   OWNER: Акім (issue "A1").

Pure functions only: no Streamlit, no network, no LLM. tests/test_search.py is the spec.
"""
from __future__ import annotations

from typing import Iterable, Optional

from . import config
from .models import Facility, SearchResult

LatLng = tuple[float, float]


def haversine_km(a: LatLng, b: LatLng) -> float:
    """Great-circle distance in km (Earth radius 6371 km). TODO(Акім)."""
    raise NotImplementedError("A1: implement haversine_km")


def settlement_centroid(facilities: Iterable[Facility], region: str, settlement: str) -> Optional[LatLng]:
    """Mean lat/lng of facilities in (region, settlement), case-insensitive; None if none. TODO(Акім)."""
    raise NotImplementedError("A1: implement settlement_centroid")


def search(
    facilities: Iterable[Facility],
    required_ids: Iterable[str],
    origin: LatLng,
    region: Optional[str] = None,
    limit: int = config.DEFAULT_LIMIT,
) -> list[SearchResult]:
    """Facilities that have ALL required package ids (and are in `region` if given),
    sorted by distance from origin ascending, at most `limit`. Empty required_ids -> []. TODO(Акім)."""
    raise NotImplementedError("A1: implement search")
