"""Download NSZU open data and build one clean file: facility division -> packages + coordinates.

Sources (data.gov.ua, no auth, checked 16.11.2026):
  packages:   pmg_package_groups.csv
  contracts:  pmg_contracts_package_addresses.csv  (updated 2026-10-29)
  divisions:  pmg_legal_entity_divisions_info.csv  (has lat/lng)

Output (data/):
  packages.csv    package_id, package_name, group_name
  facilities.csv  one row per division: ids, names, phone, region, settlement, address, lat, lng,
                  package_ids (";"-separated)
  meta.json       source URLs, download time, row counts, coverage

Run:  python3 ingest.py            (stdlib only, ~40 MB download)
"""
import csv
import json
import os
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

SOURCES = {
    "packages": "https://data.gov.ua/dataset/f353f9e1-0900-4a4e-bab0-4f2f267a8459/resource/ae5179be-d154-4863-9063-b7a916853c6b/download/pmg_package_groups.csv",
    "contracts": "https://data.gov.ua/dataset/f353f9e1-0900-4a4e-bab0-4f2f267a8459/resource/28c2d31f-59a4-418d-b72e-f97d4a73c66d/download/pmg_contracts_package_addresses.csv",
    "divisions": "https://data.gov.ua/dataset/46fa40f9-875b-41ee-8d6f-be2cc3e40ace/resource/d98f7120-59fd-47f6-a5a5-e7f220bebc53/download/pmg_legal_entity_divisions_info.csv",
}
# Ukraine bounding box: rejects NULL / swapped / zero coordinates.
LAT_RANGE, LNG_RANGE = (44.0, 53.0), (22.0, 41.0)

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "data", "raw")
OUT = os.path.join(HERE, "..", "data")


def download(name: str, url: str) -> str:
    path = os.path.join(RAW, f"{name}.csv")
    if not os.path.exists(path):
        print(f"downloading {name} ...", file=sys.stderr)
        urllib.request.urlretrieve(url, path)
    return path


def read_csv(path: str):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        yield from csv.DictReader(fh)


def parse_coord(value: str, lo_hi):
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if lo_hi[0] < x < lo_hi[1] else None


def main() -> None:
    os.makedirs(RAW, exist_ok=True)
    paths = {k: download(k, u) for k, u in SOURCES.items()}

    packages = {r["package_id"]: r for r in read_csv(paths["packages"])}

    divisions = {}
    for r in read_csv(paths["divisions"]):
        lat, lng = parse_coord(r["lat"], LAT_RANGE), parse_coord(r["lng"], LNG_RANGE)
        if lat is None or lng is None:
            continue
        divisions[r["division_id"]] = {
            "division_name": r["division_name"],
            "division_type": r["division_type"],
            "phone": r["division_phone"],
            "region": r["residence_area"],
            "settlement": r["residence_settlement"],
            "lat": lat,
            "lng": lng,
        }

    by_division = defaultdict(lambda: {"package_ids": set()})
    total = matched = 0
    for r in read_csv(paths["contracts"]):
        total += 1
        div = divisions.get(r["division_id"])
        if div is None:
            continue
        matched += 1
        row = by_division[r["division_id"]]
        row.update(div)
        row["legal_entity_edrpou"] = r["legal_entity_edrpou"]
        row["legal_entity_name"] = r["legal_entity_name"]
        row["address"] = r["address"]
        row["package_ids"].add(r["package_id"])

    with open(os.path.join(OUT, "packages.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["package_id", "package_name", "group_name"])
        for pid, p in sorted(packages.items(), key=lambda kv: int(kv[0])):
            w.writerow([pid, p["package_name"], p["group_name"]])

    cols = ["division_id", "legal_entity_edrpou", "legal_entity_name", "division_name", "division_type",
            "phone", "region", "settlement", "address", "lat", "lng", "package_ids"]
    with open(os.path.join(OUT, "facilities.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for did, row in by_division.items():
            w.writerow({**row, "division_id": did,
                        "package_ids": ";".join(sorted(row["package_ids"], key=int))})

    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": SOURCES,
        "contract_rows": total,
        "contract_rows_with_coords": matched,
        "coverage": round(matched / total, 4) if total else 0,
        "divisions_out": len(by_division),
        "packages": len(packages),
    }
    with open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
