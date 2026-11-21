#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, re
from pathlib import Path
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

FIELDS = ["valName","valType","minimum_int","maximum_int","s_int","value_int","minimum_dou","maximum_dou","s_dou","value_dou","evalScl","valDouScl","decimalBitNumber","elistName","onlyread","invisible","valueTET"]

class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())

def plain(html: str) -> str:
    parser = TextOnly()
    parser.feed(html or "")
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xml_dir", type=Path)
    ap.add_argument("--out", type=Path, default=Path("analysis-data"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows, files = [], []
    for path in sorted(args.xml_dir.glob("resource_*.xml")):
        raw = path.read_bytes()
        root = ET.fromstring(raw)
        local = []
        for elem in root.iter():
            values = {child.tag: (child.text or "").strip() for child in elem}
            if "valName" not in values:
                continue
            row = {"source_file": path.name, "source_sha256": hashlib.sha256(raw).hexdigest(), "xml_id": elem.tag}
            row.update({key: values.get(key, "") for key in FIELDS})
            row["description"] = plain(values.get("appearance", ""))[:360]
            rows.append(row)
            local.append(elem.tag)
        files.append({"file": path.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "elements": sum(1 for _ in root.iter()), "parameters": len(local)})
    columns = ["source_file", "source_sha256", "xml_id"] + FIELDS + ["description"]
    with (args.out / "parameter-catalog.csv").open("w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    (args.out / "parameter-catalog.json").write_text(json.dumps({"files": files, "parameters": rows}, ensure_ascii=False, indent=2) + chr(10))
    ids = {}
    for row in rows:
        item = ids.setdefault(row["xml_id"], {"xml_id": row["xml_id"], "names": set(), "variants": set()})
        item["names"].add(row["valName"])
        item["variants"].add(row["source_file"])
    unique = [{"xml_id": key, "names": sorted(item["names"]), "variants": sorted(item["variants"])} for key, item in sorted(ids.items())]
    (args.out / "parameter-ids.json").write_text(json.dumps(unique, ensure_ascii=False, indent=2) + chr(10))

if __name__ == "__main__":
    main()
