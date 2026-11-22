# V1.7 ValueSeque ordering and profile-aware setup serialization

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**Analysis date:** 2026-11-22  
**XML root:** `ValueSetups`

## 1. Key discovery

Each extracted XML resource contains at least two separate ordered collections:
- `Values`: the full parameter metadata/value set;
- `ValueSeque`: a sequence of `<seque>` entries naming the values that are actually serialized and their exact order.

The V1.7 native setup serializer iterates a vector in its existing order and does not append parameter IDs. Therefore `ValueSeque`, not the order of `Values` and not alphabetical order, is the correct serialization order.

The order differs from the `Values` order in all 13 extracted resource files.

## 2. Resource families

The 13 resources classify by parameter names into 4 control-setup resources, 6 motor-setup resources and 3 motor-signal/FOC resources. Their counts are 173/273/290 Values entries and 173/261/287 ValueSeque entries respectively. These are family labels, not hardware SKU mappings. See [V1_7_FIRMWARE_CONFIG_DISCOVERY.md](V1_7_FIRMWARE_CONFIG_DISCOVERY.md).

## 3. Recovered counts

| Metric | Count |
|---|---:|
| XML resources | 13 |
| Total entries in `Values` | 736 |
| Total entries in `ValueSeque` | 721 |
| Values omitted from their sequence | 15 |
| Duplicate sequence entries | 0 |
| Sequence IDs missing from `Values` | 0 |

Per-resource counts and SHA-256 fingerprints are stored in [profile-order-summary.json](../analysis-data/profile-order-summary.json).

## 4. Values present in XML but omitted from ValueSeque

| XML ID | Name | Omission count | Notes |
|---|---|---:|---|
| `motor_rated_current` | Motor Rated Current(A) | 9 resources | Usually `valType=2,valueTET=0`; one resource uses TET 1. |
| `battery_cells_s` | Li-ion Battery Series(S) | 3 resources | TET varies across resource variants. |
| `battery_cutoff_v` | Cell Cut-Off Voltage(V) | 3 resources | TET varies across resource variants. |

These are **not in the transmit sequence** for those resource variants. The analysis does not infer whether they are display-only, derived, read-only, or intentionally excluded for another reason.

## 5. Why this matters

The XML `Values` order is not safe to use as a wire-order substitute. For example:
- resource 01 first diverges at sequence index 46: the `Values` order has `pas_min_pedal_rpm`, while `ValueSeque` has `pas_current_throttle`;
- resource 02 begins its `Values` collection with `motor_current`, but its `ValueSeque` begins with `startup_mode`.

A client that serializes the entire `Values` collection or sorts parameter IDs will produce a different byte stream.

## 6. Reproducible tooling

Added:
- `scripts/ftesc_profiles.py`: parses each XML resource, validates that sequence IDs are unique and exist in `Values`, preserves exact sequence order, and records omitted values;
- `scripts/ftesc_setup_serializer.py::encode_profile_block`: encodes a marker-prefixed block from an explicit `ValueSeque` list and a value map;
- `tests/test_ftesc_profiles.py`: verifies order, omitted values and malformed sequence rejection;
- additional serializer tests verify sequence order overrides dictionary order.

Generate the detailed artifacts from restored XML:

```bash
python scripts/restore_payloads.py --root .
python scripts/ftesc_profiles.py embedded-xml/original --out analysis-data
```

This produces:
- `analysis-data/profile-order.json`;
- `analysis-data/profile-order.csv`;
- `analysis-data/profile-order-summary.json`.

## 7. Remaining work

- Map each resource file to the corresponding product/firmware/hardware selection logic in the Qt/QML application.
- Determine how the two marker blocks and optional second motor-signal block are selected per UI operation.
- Verify whether the runtime vector can omit additional values based on visibility, read-only flags, or model capabilities.
- Compare generated profile blocks against a real captured request/response when a safe capture is available.

No hardware was connected and no setup values were sent.
