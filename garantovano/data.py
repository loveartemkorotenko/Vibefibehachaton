"""Data adapter: reads the files built by scripts/ingest.py. No network, no UI."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from . import config
from .models import Facility, Package


def load_packages(path: Path = config.PACKAGES_CSV) -> dict[str, Package]:
    with open(path, encoding="utf-8", newline="") as fh:
        return {r["package_id"]: Package(r["package_id"], r["package_name"], r["group_name"])
                for r in csv.DictReader(fh)}


def load_facilities(path: Path = config.FACILITIES_CSV) -> list[Facility]:
    with open(path, encoding="utf-8", newline="") as fh:
        return [
            Facility(
                division_id=r["division_id"],
                legal_entity_name=r["legal_entity_name"],
                division_name=r["division_name"],
                division_type=r["division_type"],
                phone=r["phone"],
                region=r["region"],
                settlement=r["settlement"],
                address=r["address"],
                lat=float(r["lat"]),
                lng=float(r["lng"]),
                package_ids=frozenset(p for p in r["package_ids"].split(";") if p),
            )
            for r in csv.DictReader(fh)
        ]


def load_rights(path: Path = config.RIGHTS_JSON) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_meta(path: Path = config.META_JSON) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
