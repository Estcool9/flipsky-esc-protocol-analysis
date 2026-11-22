# V1.7 typed setup-response decoding

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**Marker validator / block iterator:** `FUN_004A10C0`  
**Per-value decoder:** `FUN_004A0B70`  
**Value metadata lookup:** `FUN_004EBE20`  
**Analysis date:** 2026-11-22

## 1. Native response decode path

The setup response parser uses the same ordered ValueSetup metadata as the request serializer:

1. `FUN_004A10C0` reads a 32-bit big-endian marker using `FUN_0049D4B0`.
2. It compares the marker with the expected value supplied by the caller.
3. On a match, it iterates the ValueSetup vector at object offset `+0x18` in its existing order.
4. For each vector entry it calls `FUN_004A0B70`.
5. `FUN_004A0B70` resolves the parameter's metadata with `FUN_004EBE20`, reads the correct number/type of bytes, scales or converts the value, and updates the corresponding ValueSetup value if it changed.
6. On a marker mismatch, the native code logs `Invalid SecretKey` and returns failure.

The parameter ID is not sent in the response block. The XML `ValueSeque` order and local metadata determine how the byte stream is interpreted.

## 2. Marker validation is not the firmware TEA handshake

The strings “Invalid SecretKey” are used for a failed 32-bit setup marker check. The setup markers are fixed constants:
- motor setup: `0xD2C6EF10`;
- optional motor-signal block: `0x4879187D`;
- TopFlow: `0x54464346`.

This marker validation is distinct from firmware authorization, which uses a UUID-derived 16-byte TEA key and CMD 0x21/0x22.

## 3. Native read-type map

| Outer `valType` | `valueTET` | Native reader | Decoded representation |
|---:|---:|---|---|
| 1 | 7 | `FUN_0049D540(evalScl)` | signed int16 ÷ scale |
| 1 | 8 | `FUN_0049D510(evalScl)` | signed int32 ÷ scale |
| 1 | 9 | `FUN_0049D570()` | IEEE-754 float32 BE |
| 2 | 1 | `FUN_0049D370()` | unsigned byte |
| 2 | 2 | `FUN_0049D330()` | signed byte |
| 2 | 3 | `FUN_0049D400()` | unsigned int16 BE |
| 2 | 4 | `FUN_0049D3B0()` | signed int16 BE |
| 2 | 5 | `FUN_0049D4B0()` | unsigned int32 BE |
| 2 | 6 | `FUN_0049D450()` | signed int32 bit pattern |
| 4, 6, 7 | any observed | `FUN_0049D330()` | signed byte |

The current XML catalog has no `(valType=2,valueTET=2)` rows; the native decoder nevertheless implements it. Outer types 4, 6 and 7 currently use only small nonnegative values (0–3) in the extracted resources, although the native reader treats the byte as signed.

## 4. Offline decoder

Added to `scripts/ftesc_setup_serializer.py`:
- `decode_profile_block(data, marker, profile_order, metadata_by_id, offset=0)`;
- `DecodedSetupBlock`, which returns decoded values and `next_offset`.

The decoder:
- validates the 32-bit marker;
- consumes values in the exact `ValueSeque` order;
- uses `valType`, `valueTET` and `evalScl` from the selected XML resource;
- returns `value_dou` for floating entries and `value_int` for integer/byte entries;
- allows a caller to decode an optional second block from the returned `next_offset`.

The offline encoder was also refined: `valType=2,valueTET=2` and outer types 4/6/7 use signed-byte range validation, matching the native reader.

## 5. Response paths covered

- CMD 0x1B motor-signal response: first marker `0xD2C6EF10`, optional second marker `0x4879187D`.
- CMD 0x3A / 0x3D TopFlow response: marker `0x54464346`; the parser path is known, but the TopFlow XML schema is still missing.
- The motor setup read response also uses the marker-driven ValueSetup decode path.

The decoder is generic and can decode any supported ValueSetup table once the matching metadata/order list is supplied. The exact resource-to-SKU mapping remains open.

## 6. Verification

Four tests cover all observed primitive decode types, signed bytes, marker mismatch/truncation and sequential decoding of two marker blocks. The full public clone suite now has **104 passing tests** and `compileall` succeeds.

No hardware was connected and no setup response was captured.
