"""Create a reusable static reverse-engineering project skeleton.

The source artifact is inventoried and hashed but never copied or executed.
Only the Python standard library is required.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

PROJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def detect_file_kind(header: bytes) -> str:
    if header.startswith(b"MZ"):
        return "PE/DOS executable candidate"
    if header.startswith(b"\x7fELF"):
        return "ELF"
    if header.startswith(b"PK\x03\x04"):
        return "ZIP"
    if header.startswith(b"%PDF-"):
        return "PDF"
    if header.startswith((b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf")):
        return "Mach-O big-endian"
    if header.startswith((b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe")):
        return "Mach-O little-endian"
    if header.startswith(b"\xca\xfe\xba\xbe"):
        return "Mach-O universal / Java class candidate"
    return "unknown"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_artifact(path: Path) -> dict[str, Any]:
    source = path.expanduser().resolve(strict=True)
    if not source.is_file():
        raise ValueError(f"artifact is not a regular file: {source}")
    with source.open("rb") as stream:
        header = stream.read(32)
    return {
        "filename": source.name,
        "absolute_path": str(source),
        "size_bytes": source.stat().st_size,
        "sha256": sha256_file(source),
        "detected_kind": detect_file_kind(header),
        "copied_into_project": False,
        "executed": False,
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def create_project(name: str, out_dir: Path, artifact: Path | None = None) -> Path:
    if not isinstance(name, str) or not PROJECT_RE.fullmatch(name) or ".." in name:
        raise ValueError("name must be a safe slug using letters, digits, dot, underscore or hyphen")
    root = out_dir.expanduser().resolve() / name
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"project directory is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)

    inventory = inspect_artifact(artifact) if artifact is not None else None
    created = datetime.now(timezone.utc).isoformat()
    manifest = {
        "schema_version": 1,
        "project_name": name,
        "created_at_utc": created,
        "analysis_policy": {
            "original_artifacts_are_immutable": True,
            "execute_unknown_binaries": False,
            "commit_original_binaries_by_default": False,
        },
        "artifact": inventory,
    }
    write_text(root / "project-manifest.json", json.dumps(manifest, indent=2) + "\n")

    if inventory:
        artifact_lines = (
            f"- Filename: {inventory['filename']}\n"
            f"- Size: {inventory['size_bytes']} bytes\n"
            f"- SHA-256: {inventory['sha256']}\n"
            f"- Detected kind: {inventory['detected_kind']}\n"
            f"- Original path: {inventory['absolute_path']}\n"
        )
    else:
        artifact_lines = "- No artifact inventoried yet. Add one with --artifact PATH.\n"

    write_text(root / "README.md", f"""# {name}

Static reverse-engineering project. Original files are not copied or executed by the scaffold generator.

## Artifact
{artifact_lines}
## Workflow
1. Verify the source hash in project-manifest.json.
2. Record static findings in docs/EVIDENCE_LEDGER.md.
3. Keep subsystem notes in docs/ and deterministic tools in scripts/.
4. Add tests for each extracted format or protocol hypothesis.
5. Update the checkpoint, progress log and roadmap at each milestone.
""")
    write_text(root / ".gitignore", """__pycache__/
*.py[cod]
*.log
.DS_Store
Thumbs.db

# Original binaries, firmware, libraries and dumps
artifacts/original/*
*.exe
*.dll
*.sys
*.so
*.dylib
*.pdb
*.dmp
*.bin
*.hex
*.elf
*.fw
*.img

# Temporary/generated files
*.tmp
*.restore-tmp
""")
    write_text(root / "docs/ARTIFACT_INVENTORY.md", f"""# Artifact inventory

Project: {name}

{artifact_lines}
Record each source separately. Never overwrite an original; calculate a new hash for every changed build.
""")
    write_text(root / "docs/EVIDENCE_LEDGER.md", """# Evidence ledger

Use one row per material finding. Record artifact SHA-256, address/offset, source and confidence.

| ID | Artifact SHA-256 | Address / offset | Finding | Evidence source | Confidence | Caveat |
|---|---|---|---|---|---|---|
""")
    write_text(root / "docs/ANALYSIS_CHECKPOINT.md", f"""# Analysis checkpoint — {name}

- Artifact identity: see project-manifest.json.
- Overall progress: 0%.
- Last verified test result: none.

## Confirmed findings
None yet.

## Next actions
1. Verify the artifact hash.
2. Run non-executing format, section and import triage.
3. Create an evidence ledger and subsystem notes.
4. Build deterministic extractors and tests before implementing protocol encoders.

## Current blockers
- File format, architecture and runtime not identified.
- Resources and transport/protocol boundaries not mapped.
""")
    write_text(root / "docs/PROGRESS_LOG.md", f"""# Progress log — {name}

## Project created
- Created at UTC: {created}
- Artifact hash: {inventory['sha256'] if inventory else 'not supplied'}
- Original binary was not copied or executed.
""")
    write_text(root / "docs/ROADMAP.md", """# Roadmap

- [ ] Identify artifact format, architecture and runtime.
- [ ] Map startup path and major components.
- [ ] Extract resources with bounded, hash-verified scripts.
- [ ] Document protocol framing, commands and responses.
- [ ] Implement offline codecs with published/reference vectors.
- [ ] Build reusable transport/client architecture.
- [ ] Add CI for extraction, deterministic outputs and tests.
- [ ] Compare authorized passive captures.
- [ ] Complete controlled hardware validation.
""")
    for directory in (
        "artifacts/original", "artifacts/derived", "analysis-data", "scripts", "tests"
    ):
        (root / directory).mkdir(parents=True, exist_ok=True)
    return root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="safe project folder name")
    parser.add_argument("--out", type=Path, default=Path.cwd())
    parser.add_argument("--artifact", type=Path,
                        help="optional artifact to hash and inventory; not copied")
    args = parser.parse_args()
    try:
        root = create_project(args.name, args.out, args.artifact)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Created {root}")
    print("Original artifact was not copied or executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
