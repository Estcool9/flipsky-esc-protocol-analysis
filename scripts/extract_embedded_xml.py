#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, zlib
from pathlib import Path
import xml.etree.ElementTree as ET

EXPECTED_SHA256 = "dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38"
OFFSETS = [0x1e2ce8,0x1e8420,0x1eab68,0x1edb48,0x1f0530,0x1f263d,0x1f4767,0x1f68f3,0x1f9273,0x1fa14c,0x1fb879,0x1fde78,0x209c88,0x21c2bb,0x1f78ba,0x1fed4a,0x204444,0x20cd8c,0x20fe7f,0x21f2bc]
MAX_OUTPUT = 4 * 1024 * 1024

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser(description="Extract known embedded ValueSetups XML streams; never execute the PE.")
    ap.add_argument("exe", type=Path)
    ap.add_argument("--out", type=Path, default=Path("embedded-xml"))
    args = ap.parse_args()
    source = args.exe.read_bytes()
    source_hash = digest(source)
    if source_hash != EXPECTED_SHA256:
        raise SystemExit(f"Unexpected SHA-256: {source_hash}; expected {EXPECTED_SHA256}")
    args.out.mkdir(parents=True, exist_ok=True)
    seen, records = {}, []
    for index, offset in enumerate(OFFSETS, 1):
        if not 0 <= offset < len(source):
            raise SystemExit(f"Offset outside file: {offset:#x}")
        dec = zlib.decompressobj()
        raw = dec.decompress(source[offset:], MAX_OUTPUT)
        if not dec.eof:
            raise SystemExit(f"Stream at {offset:#x} did not reach EOF within {MAX_OUTPUT} bytes")
        sha = digest(raw)
        if sha in seen:
            records.append({"offset": hex(offset), "status": "duplicate", "duplicate_of": seen[sha], "bytes": len(raw), "sha256": sha})
            continue
        root = ET.fromstring(raw)
        name = f"resource_{index:02d}_{offset:08x}.xml"
        (args.out / name).write_bytes(raw)
        seen[sha] = name
        records.append({"offset": hex(offset), "file": name, "status": "saved", "bytes": len(raw), "sha256": sha, "root": root.tag})
    manifest = {"source": args.exe.name, "source_sha256": source_hash, "method": "bounded zlib streams at known offsets; no executable run", "max_decompressed_bytes_per_stream": MAX_OUTPUT, "records": records}
    (args.out / "extraction-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + chr(10))
    print(json.dumps({"unique_resources": len(seen), "records": records}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
