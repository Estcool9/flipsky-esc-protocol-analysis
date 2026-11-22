# Artifact inventory and integrity record

Reference date: **22 November 2026**

## Primary executable examined

| Artifact | Size | SHA-256 | Repository status |
|---|---:|---|---|
| `Flipsky_ESC_Tool_V1.7_20261029.exe` | 50,611,200 bytes | `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38` | Kept in REA at `/data/samples/Flipsky_ESC_Tool_V1.7_20261029.exe`; not currently mirrored into GitHub |

The executable hash was checked on the analysis host and remained unchanged after the Rizin analysis commands. Its format is PE32 x86; no CLR/.NET header was identified.

The GitHub API transfer available in this session did not provide a practical single-object path for this 50.6 MB executable. The artifact identity and analysis evidence are recorded here rather than silently substituting a partial file.

## Derived catalogs

| File | Size | SHA-256 | GitHub representation |
|---|---:|---|---|
| `analysis-data/parameter-catalog.csv` | 262,831 bytes | `012933243a2a7f8e7cc1af6d6e09e1bfd41ef91f7e41bd4c3a01746a774d03ff` | Complete `.gz.b64` payload |
| `analysis-data/parameter-catalog.json` | 637,890 bytes | `0aa1fe4be40570c239e4a78a31e14a0572f29483c30f44818712ecc62837f741` | Complete `.gz.b64` payload |
| `analysis-data/parameter-ids.json` | 72,910 bytes | `338627bfbf0d95374140ea4d3991320d17c2f076526cc46d710bcfb3712669da` | Complete `.gz.b64` payload |

## Extracted embedded XML resources

The 13 resources below are decompressed XML files recovered from the application, not firmware images.

| File | Size | SHA-256 |
|---|---:|---|
| `resource_01_001e2ce8.xml` | 315,367 | `3bd75125f48c39a12e47184fcdcff8f143e9066ff03f06f4c5cbcd97338665f7` |
| `resource_02_001e8420.xml` | 125,765 | `217ccf2b0d11c0c92032c9fc6f585b8058771a7ec870eebc63493d92e6e12edb` |
| `resource_03_001eab68.xml` | 162,855 | `a6aee37f394c14c39531301c372149d83d33c0ff1e27aecdb7bab9e566bca95d` |
| `resource_04_001edb48.xml` | 139,391 | `729177495616b87105dbff87eb76dfff8ce06f97da3a3ef9d2d380c4effe3746` |
| `resource_05_001f0530.xml` | 93,683 | `77661c7e8c5caea40d4bc3603327f4e188eb048d0a46b3bd8508b20cae8bc0e7` |
| `resource_06_001f263d.xml` | 93,608 | `a1cab3ee0f0839c13450ba5f90bc52c88bfa1a61b845cf84e946a268f531b50c` |
| `resource_07_001f4767.xml` | 113,554 | `ee6844f1c8c022a2b966a41f39a0ec67ad2232e84d82eb003bb314c90919adf3` |
| `resource_08_001f68f3.xml` | 41,057 | `447603096775a9cf74af27a59751dcb51f3cee9b2ba038c957da1b9b45b15fe7` |
| `resource_09_001f9273.xml` | 38,702 | `f8d19ad975e44fe90da8d7408bccf1a253f99b18eb189694772a0dfee9cadff0` |
| `resource_10_001fa14c.xml` | 75,055 | `83c9b84975be63af5238163d4ae56f755e6b148d85b6a11909cbc852958368fc` |
| `resource_11_001fb879.xml` | 38,632 | `a20aabef0c16f5842ca2136dd686cd9c313e37251a1b402f2e9afba0d77eb69a` |
| `resource_13_00209c88.xml` | 164,539 | `9174a70828c6145c46f01b55200a8c28d86d78020969165fee2ff987707f3e25` |
| `resource_14_0021c2bb.xml` | 163,147 | `71467575ef14cf0499d578b2445d9b32ec41daf6657a26f102aad5ed1fdf2be0` |

## Extraction manifest and analysis tooling

| File | Size | SHA-256 |
|---|---:|---|
| `embedded-xml/extraction-manifest.json` | 38,462 | `6ae96c7079c935cc2c8551d05913f9532668cde40f0f83f6b6e960315fc01514` |
| `scripts/build_parameter_catalog.py` | 2,803 | `c7e3e5904ac6b8b8761734c56fb605d0bf9547cb27951b82892ed8282ba8d27f` |
| `scripts/extract_embedded_xml.py` | 2,403 | `ce121c9d3cfa75f09117809cc5158ad4ea09a9effbd63f6eff61c2f34e67d8f0` |

The complete extracted resources and catalogs are available as `.gz.b64` payloads. Run [scripts/restore_payloads.py](../scripts/restore_payloads.py) to reconstruct the original files. Then check the SHA-256 values above.

## Scope and confidence

- These hashes establish byte identity for the files read on the analysis host at the time of measurement.
- The executable was analyzed statically; this inventory does not claim a runtime dump or a captured hardware session.
- The extracted XML resources are software metadata, not an ESC firmware package.


## Additional reference sources — V1.4 and V1.6

| Artifact | Original size | Source location | Repository representation |
|---|---:|---|---|
| V1.4 English UART protocol PDF | 510,037 bytes | Nextcloud / Flipsky ESC Tool V1.4 | Extracted findings in docs/V1_4_TO_V1_6_PROTOCOL_CHANGES.md |
| V1.6 English UART protocol PDF | 534,546 bytes | Nextcloud / Flipsky ESC Tool V1.6 | Extracted protocol digest in docs/FTESC_UART_PROTOCOL_V1.6.md |
| V1.6 Chinese UART protocol PDF | 520,303 bytes | Nextcloud / Flipsky ESC Tool V1.6 | Not yet transcribed separately |
| V1.6 User Manual PDF | 7,387,878 bytes | Nextcloud / Flipsky ESC Tool V1.6 | Extracted findings in docs/V1.6_MANUAL_NOTES.md |
| V1.6 ECU-side C example | 12,314 bytes | Nextcloud / Flipsky ESC Tool V1.6 | Preserved at reference/ftesc_v1.4_1.5_1.6_uart_handle.c |

The PDFs have been text-extracted from Nextcloud; visual page layout and diagrams have not yet been reviewed.

## Windows builds inventoried in Nextcloud

- V1.4 20240826: 18,999,808 bytes.
- V1.5 20250511: 97,531,904 bytes.
- V1.6 20251014: 97,949,184 bytes.
- V1.6 20260806: 44,867,072 bytes.
- V1.6 20260912: 45,582,336 bytes.
- V1.7 20261029: 50,611,200 bytes.

All three Windows V1.6 builds are staged read-only on the REA host under `/data/analysis/pe/v1.6_<date>/`. Their remote SHA-256 values were re-measured on 2026-11-23:

| Build | Size (bytes) | SHA-256 | Staged path |
|---|---:|---|---|
| V1.6 20251014 | 97,949,184 | `1dc93bd84f4dab1a3ee7b3946fa0522c78fc870227523d8d5fe6d6e187ea2b07` | `/data/analysis/pe/v1.6_20251014/Flipsky_ESC_Tool_V1.6_20251014.exe` |
| V1.6 20260806 | 44,867,072 | `94cfd851a5ccce38b8c42c9f154128e10fa2906ce9efc9cddfa39c4a00361a03` | `/data/analysis/pe/v1.6_20260806/Flipsky_ESC_Tool_V1.6_20260806.exe` |
| V1.6 20260912 | 45,582,336 | `051d57a776782ae8daaeaa45179f9b568f7e89b4a78ab8dd8e558ecd3e53b968` | `/data/analysis/pe/v1.6_20260912/Flipsky_ESC_Tool_V1.6_20260912.exe` |

The original Nextcloud sources were preserved; the REA staging copies are used for static disassembly only. No Windows executable was run and no hardware transport was opened. See [the three-build UUID/helper cross-build report](WINDOWS_V1_6_UUID_HELPER_CROSS_BUILD.md).
