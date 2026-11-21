#!/usr/bin/env python3
"""Restore the repository's .gz.b64 payloads to their original file paths.

The repository stores selected larger text resources and generated catalogs as
base64-encoded gzip streams so their bytes survive constrained API transfers.
This script decodes every **.gz.b64 file and writes the original uncompressed
file beside it, replacing the incomplete placeholder files in the working tree.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import sys
from pathlib import Path


def restore_payload(payload: Path, *, verify_only: bool = False) -> tuple[Path, int, str]:
    encoded = payload.read_text(encoding="ascii").strip()
    try:
        compressed = base64.b64decode(encoded, validate=True)
        data = gzip.decompress(compressed)
    except (ValueError, OSError) as exc:
        raise ValueError(f"{payload}: invalid base64/gzip payload: {exc}") from exc

    output = Path(str(payload)[: -len(".gz.b64")])
    digest = hashlib.sha256(data).hexdigest()
    if not verify_only:
        output.parent.mkdir(parents=True, exist_ok=True)
        temp = output.with_name(output.name + ".restore-tmp")
        temp.write_bytes(data)
        temp.replace(output)
    return output, len(data), digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="repository root (default: parent of this script)")
    parser.add_argument("--verify-only", action="store_true",
                        help="validate payloads and print hashes without writing files")
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f"root directory does not exist: {root}")

    payloads = sorted(p for p in root.rglob("*.gz.b64") if ".git" not in p.parts)
    if not payloads:
        print(f"No .gz.b64 payloads found under {root}", file=sys.stderr)
        return 1

    failures = 0
    for payload in payloads:
        try:
            output, size, digest = restore_payload(payload, verify_only=args.verify_only)
            action = "verified" if args.verify_only else "restored"
            print(f"{action}: {output.relative_to(root)} | {size} bytes | sha256 {digest}")
        except (OSError, UnicodeError, ValueError) as exc:
            failures += 1
            print(f"ERROR: {exc}", file=sys.stderr)

    print(f"\n{len(payloads) - failures}/{len(payloads)} payloads processed successfully")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
