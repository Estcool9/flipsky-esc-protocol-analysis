"""Bounded scanner for zlib-compressed XML embedded in native binaries.

This is a static-analysis helper. It never executes the target binary.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zlib


@dataclass(frozen=True, slots=True)
class XmlStream:
    offset: int
    compressed_size: int
    uncompressed_size: int
    sha256: str
    root_tag: str
    duplicate_of_offset: int | None
    qcompress_length_prefix: int | None
    qcompress_prefix_matches: bool


@dataclass(frozen=True, slots=True)
class ScanResult:
    candidate_headers: int
    completed_zlib_streams: int
    xml_streams: tuple[XmlStream, ...]
    unique_xml: tuple[XmlStream, ...]


def _valid_zlib_header(data: bytes, offset: int) -> bool:
    if offset + 2 > len(data):
        return False
    cmf, flg = data[offset], data[offset + 1]
    return (
        (cmf & 0x0F) == 8
        and (cmf >> 4) <= 7
        and (((cmf << 8) | flg) % 31) == 0
        and (flg & 0x20) == 0
    )


def scan_zlib_xml(
    data: bytes | bytearray | memoryview,
    *,
    max_output_size: int = 4 * 1024 * 1024,
    root_tag: str | None = None,
) -> ScanResult:
    """Find complete, bounded zlib streams that decode to well-formed XML.

    Streams are scanned by their RFC1950 header. A four-byte big-endian
    length immediately before a stream is reported as a possible Qt
    qCompress length prefix when it equals the uncompressed size.
    Duplicate XML contents are retained in xml_streams but only the first
    copy is present in unique_xml.
    """
    if isinstance(max_output_size, bool) or max_output_size <= 0:
        raise ValueError("max_output_size must be positive")
    raw_data = bytes(data)
    view = memoryview(raw_data)
    cursor = 0
    candidate_headers = 0
    completed_streams = 0
    matches: list[XmlStream] = []
    unique: list[XmlStream] = []
    seen: dict[str, int] = {}

    while cursor + 2 <= len(raw_data):
        offset = raw_data.find(b"\x78", cursor)
        if offset < 0 or offset + 2 > len(raw_data):
            break
        cursor = offset + 1
        if not _valid_zlib_header(raw_data, offset):
            continue
        candidate_headers += 1
        try:
            decoder = zlib.decompressobj()
            decoded = decoder.decompress(view[offset:], max_output_size + 1)
        except zlib.error:
            continue
        if len(decoded) > max_output_size or not decoder.eof:
            continue
        completed_streams += 1
        consumed = len(raw_data[offset:]) - len(decoder.unused_data)
        if consumed <= 0:
            continue
        next_cursor = offset + consumed
        if not decoded or b"<!DOCTYPE" in decoded.upper() or b"<!ENTITY" in decoded.upper():
            cursor = next_cursor
            continue
        try:
            root = ET.fromstring(decoded)
        except ET.ParseError:
            cursor = next_cursor
            continue
        tag = str(root.tag)
        if root_tag is not None and tag != root_tag:
            cursor = next_cursor
            continue
        prefix = (
            int.from_bytes(raw_data[offset - 4:offset], "big")
            if offset >= 4 else None
        )
        prefix_matches = prefix == len(decoded) if prefix is not None else False
        digest = hashlib.sha256(decoded).hexdigest()
        duplicate_of = seen.get(digest)
        item = XmlStream(
            offset=offset,
            compressed_size=consumed,
            uncompressed_size=len(decoded),
            sha256=digest,
            root_tag=tag,
            duplicate_of_offset=duplicate_of,
            qcompress_length_prefix=prefix,
            qcompress_prefix_matches=prefix_matches,
        )
        matches.append(item)
        if duplicate_of is None:
            seen[digest] = offset
            unique.append(item)
        cursor = offset + consumed

    return ScanResult(
        candidate_headers=candidate_headers,
        completed_zlib_streams=completed_streams,
        xml_streams=tuple(matches),
        unique_xml=tuple(unique),
    )


def write_results(result: ScanResult, out_dir: Path, data: bytes) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    resources = []
    for index, item in enumerate(result.unique_xml, 1):
        name = f"resource_{index:02d}_{item.offset:08x}.xml"
        offset = item.offset
        decoder = zlib.decompressobj()
        decoded = decoder.decompress(memoryview(data)[offset:], item.uncompressed_size + 1)
        if len(decoded) != item.uncompressed_size or not decoder.eof:
            raise RuntimeError(f"stream changed or failed to decode at 0x{offset:x}")
        (out_dir / name).write_bytes(decoded)
        resources.append({
            **asdict(item),
            "file": name,
        })
    manifest = {
        "scanner": "scan_compressed_xml.py",
        "candidate_headers": result.candidate_headers,
        "completed_zlib_streams": result.completed_zlib_streams,
        "xml_streams": len(result.xml_streams),
        "unique_xml": len(result.unique_xml),
        "resources": resources,
        "all_matches": [asdict(x) for x in result.xml_streams],
    }
    (out_dir / "scan-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-output-size", type=int, default=4 * 1024 * 1024)
    parser.add_argument("--root-tag")
    args = parser.parse_args()
    data = args.binary.read_bytes()
    result = scan_zlib_xml(
        data, max_output_size=args.max_output_size, root_tag=args.root_tag
    )
    write_results(result, args.out, data)
    print(
        f"zlib_headers={result.candidate_headers} "
        f"completed_streams={result.completed_zlib_streams} "
        f"xml_streams={len(result.xml_streams)} "
        f"unique_xml={len(result.unique_xml)}"
    )


if __name__ == "__main__":
    main()
