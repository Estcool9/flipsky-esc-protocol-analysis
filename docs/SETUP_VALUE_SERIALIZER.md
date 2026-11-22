# V1.7 typed setup-value serialization

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Serializer loop:** `0x004A0B00`  
**Per-value serializer:** `0x004A0790`  
**Value metadata/cache helper:** `0x004EBE20`  
**Analysis date:** 2026-11-22

## 1. Serialization call path

The three setup-write methods use marker-prefixed blocks:
- motor setup: marker `0xD2C6EF10`;
- motor-signal setup: marker `0xD2C6EF10`, then optional second block `0x4879187D`;
- TopFlow setup: marker `0x54464346`.

Each block is handled by `FUN_004A0B00`:
1. append the 32-bit marker in big-endian order using `FUN_0049D080`;
2. iterate a vector-like collection in its existing order;
3. pass each item to `FUN_004A0790`.

The per-value function resolves the parameter ID against the current parameter setup/cache, obtains its typed metadata, and serializes the value according to the outer `valType` and inner transmit-type discriminator. The parameter ID is used for lookup; **this helper does not append the ID itself**. The serialized values are emitted in the vector order.

This is direct evidence for a schema-driven, ordered payload rather than a stream of repeated ID/value pairs.

## 2. XML field correlation

The extracted `ValueSetups` XML resources contain:
- `valType`;
- `valueTET`;
- `evalScl`;
- `value_int`;
- `value_dou`.

The serializer's outer discriminator matches the XML `valType` domain. Its inner discriminator at metadata offset `+0x48` matches the observed `valueTET` domain; the scaling field at `+0x50` is used as the multiplier for scaled floating values and matches `evalScl`.

Observed XML `(valType, valueTET)` pairs across the 736 catalog rows:

| Pair | Rows | Serializer path |
|---|---:|---|
| (1, 9) | 469 | IEEE-754 float32, big-endian |
| (1, 7) | 60 | scaled signed 16-bit, big-endian |
| (1, 0) | 2 | no matching transmit branch observed |
| (2, 1) | 53 | one byte |
| (2, 0) | 10 | no matching transmit branch observed |
| (2, 3) | 1 | unsigned 16-bit, big-endian |
| (2, 5) | 7 | unsigned 32-bit, big-endian |
| (4, 1) or missing | 108 | one byte |
| (6, 1) or missing | 12 | one byte |
| (7, 1) or missing | 14 | one byte |

Counts are across profile variants, so the same logical parameter may occur in several XML files.

## 3. Primitive encoding table recovered from `FUN_004A0790`

| Outer `valType` | Inner `valueTET` | Source value | Native writer | Encoded form |
|---:|---:|---|---|---|
| 1 | 7 | `value_dou × evalScl`, rounded | `FUN_0049D1E0` → `FUN_0049CE50` | signed 16-bit BE |
| 1 | 8 | `value_dou × evalScl`, rounded | `FUN_0049D150` → `FUN_0049CFB0` | signed 32-bit BE |
| 1 | 9 | `value_dou` cast to float | `FUN_0049D270` → `FUN_0049D080` | IEEE-754 float32 BE |
| 2 | 1 or 2 | `value_int` | `FUN_0049CE40` | one byte |
| 2 | 3 | `value_int` | `FUN_0049CF00` | unsigned 16-bit BE |
| 2 | 4 | `value_int` | `FUN_0049CE50` | signed 16-bit BE |
| 2 | 5 | `value_int` | `FUN_0049D080` | unsigned 32-bit BE |
| 2 | 6 | `value_int` | `FUN_0049CFB0` | signed 32-bit BE |
| 4, 6 or 7 | any observed | `value_int` byte | `FUN_0049CE30` | one byte |

All multi-byte writers append most-significant byte first.

For scaled floating values, the native code multiplies by the scale, adds/subtracts 0.5 based on sign and converts to an integer before writing. The offline implementation uses round-half-away-from-zero to match that observed intent.

## 4. Unsupported XML combinations

The XML catalog includes `valType=1,valueTET=0` and `valType=2,valueTET=0`. The recovered serializer's switch has no matching case for these combinations and logs a type/transmit-type error. The offline encoder rejects them rather than guessing.

The XML contains no observed `valType=1,valueTET=8` records, but the native function explicitly implements that branch. The offline encoder supports it and has a synthetic test.

## 5. Offline implementation

Added:
- `scripts/ftesc_setup_serializer.py`: scalar encoder, marker-prefixed block builder, and `encode_profile_block()` using explicit XML sequence IDs;
- `scripts/ftesc_profiles.py`: validates and extracts `ValueSeque` order and omitted values from each XML resource;
- `tests/test_ftesc_setup_serializer.py`: tests for float32, scaled 16/32-bit values, integer widths, byte types, marker order, explicit profile order, unsupported types and range failures;
- `tests/test_ftesc_profiles.py`: tests for sequence ordering, omissions, duplicate IDs and unknown IDs.

The implementation is intentionally strict about numeric range and finite values. It does not connect to USB, serial, CAN or BLE and does not send data to a controller.

The exact wire order is now recovered from each XML resource's `ValueSeque` element. It differs from the `Values` element order in all 13 resources. `scripts/ftesc_profiles.py` extracts this sequence and records values present in `Values` but omitted from `ValueSeque`; `encode_profile_block()` uses the explicit sequence rather than dictionary/XML `Values` order. Product/hardware selection logic and conditional second-block selection remain separate tasks.

## 6. Profile order extraction

Across the 13 XML resources, `Values` contains 736 entries while `ValueSeque` contains 721 entries. There are 15 omitted values, no duplicate sequence entries, and no sequence IDs missing from `Values`. The exact ordered artifacts are stored as `analysis-data/profile-order.json.gz.b64` and `analysis-data/profile-order.csv.gz.b64`; `scripts/restore_payloads.py` restores them automatically. The small per-resource summary is `analysis-data/profile-order-summary.json`.

See [V1_7_PROFILE_SERIALIZATION_ORDER.md](V1_7_PROFILE_SERIALIZATION_ORDER.md).

## 7. Verification

The published GitHub tree was cloned afresh on REA, the compressed XML/catalog/profile-order artifacts were restored, and the scripts were tested:

- **77 tests passed, 0 failed**;
- Python `compileall` completed successfully;
- tests include the existing frame parser, command codec, streaming decoder and new typed setup serializer.

No hardware was connected. No configuration payload was transmitted.
