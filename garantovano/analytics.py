"""Straight-line access from primary-care points to contracted care. OWNER: Діма (#5).

These are shares of facility points in the source dataset, never population shares.
No I/O, network, UI, or model calls; the distance threshold is supplied by the caller.
"""
from __future__ import annotations

from collections import Counter
from math import isfinite
from statistics import median
from typing import Iterable

from .models import Facility
from .search import haversine_km


def analyze_access(
    facilities: Iterable[Facility],
    package_id: str,
    *,
    threshold_km: float,
) -> tuple[dict[str, float], float | None, float | None]:
    """Return (regional shares, national share, median distance in km).

    Each facility with primary-care package "1" is one observation. Its nearest
    target may be in any region. A point is distant only when its distance is
    strictly greater than threshold_km; shares are fractions in [0, 1]. Regions
    with primary points are ordered by descending share, then name on ties.
    No primary points -> ({}, None, None); no target -> ValueError, not zero access.
    Co-located target coordinates are equivalent, but every primary point counts.
    """
    if (isinstance(threshold_km, bool) or not isinstance(threshold_km, (int, float))
            or threshold_km < 0 or not isfinite(threshold_km)):
        raise ValueError("threshold_km must be a finite nonnegative distance")
    facilities = tuple(facilities)
    primary = [facility for facility in facilities if "1" in facility.package_ids]
    if not primary:
        return {}, None, None
    targets = {(facility.lat, facility.lng) for facility in facilities
               if package_id in facility.package_ids}
    if not targets:
        raise ValueError("No contracted facilities for the selected package")

    totals: Counter[str] = Counter()
    distant: Counter[str] = Counter()
    distances: list[float] = []
    for facility in primary:
        origin = (facility.lat, facility.lng)
        distance = min(haversine_km(origin, target) for target in targets)
        distances.append(distance)
        totals[facility.region] += 1
        if distance > threshold_km:
            distant[facility.region] += 1

    shares = {region: distant[region] / count for region, count in totals.items()}
    shares = dict(sorted(shares.items(), key=lambda item: (-item[1], item[0])))
    national_share = sum(distant.values()) / len(primary)
    return shares, national_share, float(median(distances))
