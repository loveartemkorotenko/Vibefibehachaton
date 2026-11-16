"""Spec for garantovano/search.py (OWNER: Акім). Remove the xfail marker in your PR."""
import pytest

from garantovano.models import Facility
from garantovano.search import haversine_km, search, settlement_centroid

pytestmark = pytest.mark.xfail(raises=NotImplementedError, strict=False, reason="A1 not implemented yet")

KYIV, LVIV = (50.4501, 30.5234), (49.8397, 24.0297)


def fac(i, lat, lng, pkgs, region="М.КИЇВ", settlement="КИЇВ"):
    return Facility(f"d{i}", f"Entity {i}", f"Division {i}", "Лікарня", "", region, settlement,
                    f"addr {i}", lat, lng, frozenset(pkgs))


FACILITIES = [
    fac(1, 50.50, 30.50, {"7", "8", "35"}),          # ~6 km from KYIV
    fac(2, 50.45, 30.53, {"7", "35"}),               # closest
    fac(3, 50.30, 30.60, {"35"}),
    fac(4, 49.84, 24.03, {"7", "8"}, "ЛЬВІВСЬКА", "ЛЬВІВ"),
]


def test_haversine_kyiv_lviv():
    assert haversine_km(KYIV, LVIV) == pytest.approx(468, abs=5)
    assert haversine_km(KYIV, KYIV) == pytest.approx(0, abs=1e-6)


def test_search_requires_all_packages_and_sorts_by_distance():
    res = search(FACILITIES, {"7", "35"}, KYIV)
    assert [r.facility.division_id for r in res] == ["d2", "d1"]
    assert res[0].distance_km <= res[1].distance_km


def test_search_respects_region_and_limit():
    assert [r.facility.division_id for r in search(FACILITIES, {"7"}, KYIV, region="ЛЬВІВСЬКА")] == ["d4"]
    assert len(search(FACILITIES, {"35"}, KYIV, limit=2)) == 2


def test_search_empty_required_returns_nothing():
    assert search(FACILITIES, set(), KYIV) == []


def test_settlement_centroid():
    lat, lng = settlement_centroid(FACILITIES, "м.київ", "київ")
    assert lat == pytest.approx((50.50 + 50.45 + 50.30) / 3)
    assert settlement_centroid(FACILITIES, "ОДЕСЬКА", "ОДЕСА") is None
