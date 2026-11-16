"""Deterministic search over open data.   OWNER: Акім (issue "A1").

Pure functions only: no Streamlit, no network, no LLM. tests/test_search.py is the spec.
"""
from __future__ import annotations

import math
from typing import Iterable, Optional

from . import config
from .models import Facility, SearchResult

LatLng = tuple[float, float]


def haversine_km(a: LatLng, b: LatLng) -> float:
    """Great-circle distance in km (Earth radius 6371 km)."""
    lat1, lng1, lat2, lng2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 2 * 6371.0 * math.asin(min(1.0, math.sqrt(h)))


def settlement_centroid(facilities: Iterable[Facility], region: str, settlement: str) -> Optional[LatLng]:
    """Mean lat/lng of facilities in (region, settlement), case-insensitive; None if none."""
    r, s = region.strip().upper(), settlement.strip().upper()
    pts = [(f.lat, f.lng) for f in facilities if f.region.upper() == r and f.settlement.upper() == s]
    if not pts:
        return None
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def search(
    facilities: Iterable[Facility],
    required_ids: Iterable[str],
    origin: LatLng,
    region: Optional[str] = None,
    limit: int = config.DEFAULT_LIMIT,
) -> list[SearchResult]:
    """Facilities that have ALL required package ids (and are in `region` if given),
    sorted by distance from origin ascending, at most `limit`. Empty required_ids -> []."""
    required = frozenset(required_ids)
    if not required or limit <= 0:
        return []
    hits = [
        SearchResult(f, haversine_km(origin, (f.lat, f.lng)))
        for f in facilities
        if required <= f.package_ids and (region is None or f.region == region)
    ]
    hits.sort(key=lambda r: r.distance_km)
    return hits[:limit]
