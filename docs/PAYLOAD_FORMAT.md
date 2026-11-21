# Large payload representation and restoration

## Why some files are stored as `.gz.b64`

The repository contains selected resources as `.gz.b64` files. Each is the original file compressed with gzip and then encoded as base64 text. This preserves the exact uncompressed bytes while allowing the GitHub API transfer path to handle files that exceed its per-response text boundary.

This applies to the full derived parameter catalogs, the resource extraction manifest, and all 13 extracted embedded XML resources.

## Restore the original files

Run from a clone of this repository:

```bash
python scripts/restore_payloads.py --root .
```

The script:
1. finds all `.gz.b64` payloads outside `.git`;
2. validates base64 and gzip decompression;
3. writes the uncompressed content to the matching path (removing the `.gz.b64` suffix);
4. prints byte size and SHA-256 for each restored file.

To verify all payloads without writing files:

```bash
python scripts/restore_payloads.py --root . --verify-only
```

The files `analysis-data/parameter-catalog.csv`, `analysis-data/parameter-catalog.json`, `analysis-data/parameter-ids.json`, and `embedded-xml/extraction-manifest.json` are currently small explanatory placeholders in Git. Run the restore script to replace them with their complete original contents.

## Payload paths

- `analysis-data/parameter-catalog.csv.gz.b64`
- `analysis-data/parameter-catalog.json.gz.b64`
- `analysis-data/parameter-ids.json.gz.b64`
- `embedded-xml/extraction-manifest.json.gz.b64`
- `embedded-xml/original/resource_*.xml.gz.b64` (13 XML resources)

## Original executable

The analysed Windows executable is 50,611,200 bytes. Its SHA-256 is recorded in [ARTIFACT_INVENTORY.md](ARTIFACT_INVENTORY.md). It remains in the REA analysis workspace; this GitHub API transfer workflow could not stream a binary of that size into the repository as one Git object. No executable bytes were altered during analysis.
