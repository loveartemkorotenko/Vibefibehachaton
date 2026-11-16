"""D2 accessibility calculations: synthetic geometry plus NSZU data regression."""
import math

import pytest

from garantovano.analytics import analyze_access
from garantovano.data import load_facilities
from garantovano.models import Facility
from garantovano.search import haversine_km


def facility(identifier, lat, lng, packages, region="A"):
    """Demo data: one division, used only to exercise deterministic geometry."""
    return Facility(
        identifier, identifier, identifier, "Demo data", "", region, "Demo data",
        "Demo data", lat, lng, frozenset(packages),
    )


def test_national_share_weights_primary_points_and_regions_sort_descending():
    facilities = [
        facility("a-near-1", 0, 0, {"1"}),
        facility("a-near-2", 0, 0.1, {"1"}),
        facility("a-far", 0, 2, {"1"}),
        facility("b-far", 0, 3, {"1"}, region="B"),
        facility("target", 0, 0, {"6"}, region="C"),
    ]
    regions, national_share, median_km = analyze_access(facilities, "6", threshold_km=50)

    assert list(regions) == ["B", "A"]
    assert regions == pytest.approx({"B": 1.0, "A": 1 / 3})
    assert national_share == pytest.approx(2 / 4)
    assert median_km == pytest.approx(
        (haversine_km((0, 0.1), (0, 0)) + haversine_km((0, 2), (0, 0))) / 2
    )


def test_nearest_target_can_be_in_another_region():
    origin, nearby = (50, 30), (50.01, 30)
    facilities = [
        facility("primary", *origin, {"1"}),
        facility("distant-local-target", 52, 30, {"6"}),
        facility("nearby-other-region-target", *nearby, {"6"}, region="B"),
        facility("closer-unrelated-package", *origin, {"7"}),
    ]
    regions, national_share, median_km = analyze_access(facilities, "6", threshold_km=50)

    assert regions == {"A": 0.0}
    assert national_share == 0.0
    assert median_km == pytest.approx(haversine_km(origin, nearby))


def test_exact_threshold_is_not_counted_as_further_away():
    target, boundary = (0, 0), (0, 1)
    threshold = haversine_km(boundary, target)
    facilities = [
        facility("at-boundary", *boundary, {"1"}),
        facility("beyond-boundary", 0, 2, {"1"}),
        facility("target", *target, {"6"}),
    ]
    regions, national_share, _ = analyze_access(facilities, "6", threshold_km=threshold)

    assert regions == {"A": 0.5}
    assert national_share == 0.5


def test_primary_divisions_are_counted_even_when_coordinates_coincide():
    facilities = [
        facility("near", 0, 0, {"1"}),
        facility("far-one", 0, 1, {"1"}),
        facility("far-two", 0, 1, {"1"}),
        facility("target", 0, 0, {"6"}),
    ]
    regions, national_share, median_km = analyze_access(facilities, "6", threshold_km=50)

    assert regions == pytest.approx({"A": 2 / 3})
    assert national_share == pytest.approx(2 / 3)
    assert median_km == pytest.approx(haversine_km((0, 1), (0, 0)))


def test_primary_point_with_target_package_has_zero_distance():
    facilities = [facility("primary-and-target", 50, 30, {"1", "6"})]

    assert analyze_access(facilities, "6", threshold_km=0) == ({"A": 0.0}, 0.0, 0.0)


def test_one_shot_iterable_produces_the_same_result():
    facilities = [
        facility("primary", 50, 30, {"1"}),
        facility("target", 50.1, 30, {"6"}),
    ]

    assert analyze_access(iter(facilities), "6", threshold_km=50) == analyze_access(
        facilities, "6", threshold_km=50
    )


@pytest.mark.parametrize("facilities", [[], [facility("target-only", 50, 30, {"6"})]])
def test_no_primary_points_is_missing_information_not_zero_coverage(facilities):
    assert analyze_access(facilities, "6", threshold_km=50) == ({}, None, None)


def test_no_target_does_not_report_misleading_zero_distance():
    with pytest.raises(ValueError):
        analyze_access([facility("primary-only", 50, 30, {"1"})], "6", threshold_km=50)


@pytest.mark.parametrize("threshold", [-1, math.nan, math.inf, -math.inf, True, "50", None])
def test_threshold_must_be_finite_and_nonnegative(threshold):
    with pytest.raises(ValueError):
        analyze_access([], "6", threshold_km=threshold)


@pytest.fixture(scope="module")
def nszu_facilities():
    return load_facilities()


@pytest.mark.parametrize("package_id,expected_share", [("5", 0.024), ("6", 0.20), ("7", 0.017)])
def test_real_nszu_primary_care_access_matches_issue_reference(nszu_facilities, package_id, expected_share):
    regions, national_share, median_km = analyze_access(nszu_facilities, package_id, threshold_km=50)

    assert national_share == pytest.approx(expected_share, abs=0.01)
    assert list(regions.values()) == sorted(regions.values(), reverse=True)
    assert median_km is not None and math.isfinite(median_km)
    if package_id == "6":
        assert median_km == pytest.approx(22.9, abs=1.0)
