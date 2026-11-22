# V1.7 firmware-directory configuration discovery

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**Analysis date:** 2026-11-22

## 1. Embedded default table paths

The helper at `0x00488010` selects built-in V1.7 table paths:
- when its second parameter equals 1: `ftesc/1.7/TopFlowSetupValueTable.xml`;
- otherwise: `ftesc/1.7/MotorSetupValueTable_official.xml + ftesc/1.7/ControlSetupValueTable.xml`.

The paths are direct string references in the executable. This identifies the built-in V1.7 default table family but does not by itself identify which extracted compressed XML stream maps to each path.

## 2. Firmware-directory scanner

The function at `0x00492570` is a firmware-directory/configuration scanner. Its decompiled body:
- opens/monitors the `://ftesc` directory;
- enumerates candidate firmware directories;
- reads `MotorSetupValueTable_official.xml`;
- reads `ControlSetupValueTable.xml`;
- reads `TopFlowSetupValueTable.xml`;
- reads `FirmwareVersionInf.xml`;
- compares two parsed integer fields against its two input parameters;
- reports `Configurations not found in firmware directory` when the required tables/version metadata cannot be found;
- separately reports `TopFlow setup configuration not found in firmware directory` when the TopFlow table is absent.

Both call sites pass the values `(1, 7)`: startup helper `0x0047F530` and main-window constructor `0x0048E570`. These correspond to the major/minor firmware directory `ftesc/1.7`, and the loader compares the two parsed integers from `FirmwareVersionInf.xml` against those values. The selector is therefore the firmware version tuple (major=1, minor=7), not a hardware SKU.

## 3. Family classification of the 13 extracted ValueSetups resources

The parameter names provide a reliable family-level classification:

| Family | Resource files | Values | ValueSeque entries | Omitted |
|---|---:|---:|---:|---:|
| Control setup | 4 | 173 | 173 | 0 |
| Motor setup | 6 | 273 | 261 | 12 |
| Motor signal / FOC setup | 3 | 290 | 287 | 3 |
| **Total** | **13** | **736** | **721** | **15** |

Classification signatures:
- Control setup: includes `Input Signal Type` / `Throttle Response Level`;
- Motor setup: includes `Motor Current(A)`;
- Motor signal / FOC setup: includes `FOC Current Kp` and related observer/HFI fields.

These are parameter-family labels, not verified hardware model names. The 13 compressed streams have not yet been mapped to exact Qt resource paths or to specific controller SKUs.

## 4. Reproducible outputs

The profile extractor now adds a `family` label to every profile record. The full CSV/JSON artifacts and summary are published:
- [profile-order-summary.json](../analysis-data/profile-order-summary.json)
- `analysis-data/profile-order.csv.gz.b64`
- `analysis-data/profile-order.json.gz.b64`

After restoring the compressed artifacts, the CSV/JSON files contain the exact ordered parameter IDs, metadata and omissions for all 13 resource variants.

## 5. Remaining selection work

- Map the 13 resource IDs to named files and actual controller/SKU variants.
- Resolve the resource IDs to the named XML files/Qt resource paths.
- Determine how the application chooses motor, control and motor-signal tables for a connected ESC.
- Identify the independent TopFlow table schema and its marker/data sequence.
- Compare each selected table against a live read response only when a safe capture is available.

No ESC was connected and no setup request was sent.
