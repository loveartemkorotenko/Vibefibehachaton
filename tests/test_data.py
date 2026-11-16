"""Data sanity: the open-data files the demo depends on are present and sane."""
from garantovano import data

UA_LAT, UA_LNG = (44.0, 53.0), (22.0, 41.0)
FLAGSHIP_PACKAGES = {"35", "7", "8", "66", "5", "6"}


def test_packages_dictionary_has_flagship_ids():
    packages = data.load_packages()
    assert len(packages) >= 80
    assert FLAGSHIP_PACKAGES <= packages.keys()


def test_facilities_have_valid_coordinates():
    facilities = data.load_facilities()
    assert len(facilities) > 10_000
    assert all(UA_LAT[0] < f.lat < UA_LAT[1] and UA_LNG[0] < f.lng < UA_LNG[1] for f in facilities)
    assert all(f.package_ids for f in facilities)


def test_kyiv_flagship_scenario_has_data():
    kyiv = [f for f in data.load_facilities() if f.region == "М.КИЇВ"]
    assert sum({"7", "8"} <= f.package_ids for f in kyiv) >= 5      # childbirth + neonatal
    assert sum("35" in f.package_ids for f in kyiv) >= 20           # pregnancy follow-up


def test_rights_cards_have_required_fields_and_sources():
    rights = data.load_rights()
    for pid in ("35", "7", "66"):
        card = rights[pid]
        for key in ("title", "included", "if_asked_to_pay", "sources"):
            assert key in card, f"{pid} missing {key}"
        assert card["sources"], f"{pid} has no sources"


def test_meta_points_to_data_gov_ua():
    meta = data.load_meta()
    assert all("data.gov.ua" in url for url in meta["sources"].values())
    assert meta["coverage"] > 0.95
