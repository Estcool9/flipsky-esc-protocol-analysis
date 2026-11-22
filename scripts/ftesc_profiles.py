"""Extract the exact V1.7 ValueSeque serialization order from ValueSetups XML."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Any

FIELDS = (
    "valName", "valType", "minimum_int", "maximum_int", "s_int", "value_int",
    "minimum_dou", "maximum_dou", "s_dou", "value_dou", "evalScl",
    "valDouScl", "decimalBitNumber", "elistName", "onlyread", "invisible",
    "valueTET",
)


class ProfileError(ValueError):
    """Invalid or inconsistent ValueSetups profile."""


def _text_map(element: ET.Element) -> dict[str, str]:
    return {child.tag: (child.text or "").strip() for child in element}


def parse_profile(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    root = ET.fromstring(raw)
    values_element = root.find("Values")
    sequence_element = root.find("ValueSeque")
    if values_element is None or sequence_element is None:
        raise ProfileError(f"{path.name}: missing Values or ValueSeque element")

    values: dict[str, dict[str, str]] = {}
    for element in values_element:
        if element.tag in values:
            raise ProfileError(f"{path.name}: duplicate ValueSetup ID {element.tag!r}")
        values[element.tag] = _text_map(element)

    sequence = [(element.text or "").strip() for element in sequence_element]
    if any(not key for key in sequence):
        raise ProfileError(f"{path.name}: empty ValueSeque entry")
    if len(sequence) != len(set(sequence)):
        raise ProfileError(f"{path.name}: duplicate ValueSeque entry")
    unknown = [key for key in sequence if key not in values]
    if unknown:
        raise ProfileError(f"{path.name}: ValueSeque IDs absent from Values: {unknown}")

    ordered = []
    for index, key in enumerate(sequence):
        row = {"sequence_index": index, "xml_id": key}
        row.update({field: values[key].get(field, "") for field in FIELDS})
        ordered.append(row)

    omitted = []
    for key, fields in values.items():
        if key not in set(sequence):
            row = {"xml_id": key}
            row.update({field: fields.get(field, "") for field in FIELDS})
            omitted.append(row)

    return {
        "profile_file": path.name,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "value_count": len(values),
        "sequence_count": len(sequence),
        "omitted_count": len(omitted),
        "ordered_parameters": ordered,
        "omitted_parameters": omitted,
    }


def build_profile_catalog(xml_dir: Path) -> list[dict[str, Any]]:
    profiles = [parse_profile(path) for path in sorted(xml_dir.glob("resource_*.xml"))]
    if not profiles:
        raise ProfileError(f"no resource_*.xml files found in {xml_dir}")
    return profiles


def write_profile_catalog(profiles: list[dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "profile-order.json").write_text(
        json.dumps(profiles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    columns = ["profile_file", "source_sha256", "sequence_index", "xml_id", *FIELDS]
    with (out_dir / "profile-order.csv").open("w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns)
        writer.writeheader()
        for profile in profiles:
            for item in profile["ordered_parameters"]:
                writer.writerow({
                    "profile_file": profile["profile_file"],
                    "source_sha256": profile["source_sha256"],
                    **item,
                })
    summary = [
        {key: profile[key] for key in (
            "profile_file", "source_sha256", "value_count", "sequence_count", "omitted_count"
        )}
        for profile in profiles
    ]
    (out_dir / "profile-order-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml_dir", type=Path)
    parser.add_argument("--out", type=Path, default=Path("analysis-data"))
    args = parser.parse_args()
    profiles = build_profile_catalog(args.xml_dir)
    write_profile_catalog(profiles, args.out)
    print(f"profiles={len(profiles)} ordered_values={sum(p['sequence_count'] for p in profiles)} "
          f"omitted_values={sum(p['omitted_count'] for p in profiles)}")


if __name__ == "__main__":
    main()
