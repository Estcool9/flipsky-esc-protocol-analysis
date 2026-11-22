# V1.6 Android QML, ValueSetup and firmware-resource reconstruction

**Analysis date:** 2026-11-22  
**Artifact:** V1.6 Android BLE APK, SHA-256 `26404ff6467971ff7c0fedbe1f326c6b0ccb5722571b7309d9913818960b4d7e`  
**Native ARM64 library:** `libFilpsky_ESC_Tool_V1.6_20251014_arm64-v8a.so`, SHA-256 `7fba6a69f3719b70dfb7eee87c97e41aad2d8f48d1feec7058a0e5975a5ea2fc`  
**Scope:** static resource extraction and source-level analysis only. No APK execution, BLE/GATT operation, ESC command or firmware transfer.

## 1. Four application-owned Qt resource collections recovered

The generic APK `assets/android_rcc_bundle.rcc` contains Qt library resources, not the Flipsky application screens. The actual application resources are registered by four native Qt resource initializer functions in the ARM64 application library:

| Initializer | Function VA | RCC tree VA | Name table VA | Data VA |
|---|---:|---:|---:|---:|
| `qInitResources_qml` | `0x00259F5C` | `0x00296F6D` | `0x002971EB` | `0x002976E5` |
| `qInitResources_ftesc` | `0x0025A088` | `0x002ACA6F` | `0x002ACD45` | `0x002ACED3` |
| `qInitResources_ftescFw` | `0x0025A1B4` | `0x002D473F` | `0x002D4A2B` | `0x002D4C49` |
| `qInitResources_ftescIcon` | `0x0025A2A4` | `0x007BC3CD` | `0x007BC585` | `0x007BC7F7` |

All four static tables use Qt RCC version 3. Their trees were parsed read-only and their compressed files extracted without execution or mutation of the source library.

| Resource group | Tree nodes | Directories | Files extracted | Extraction errors |
|---|---:|---:|---:|---:|
| QML application screens/components | 29 | 1 | 28 | 0 |
| FTESC ValueSetup/XML profiles | 33 | 9 | 24 | 0 |
| Firmware images | 34 | 3 | 31 | 0 |
| Icons | 20 | 2 | 18 | 0 |
| **Total** | **116** | **15** | **101** | **0** |

Extraction root on REA: `/data/analysis/extracted/v1.6_ble_embedded_resources/`. The resource manifests record per-file SHA-256 values. The original APK and native library remain unchanged.

## 2. QML application architecture and screen map

The application-owned resource collection contains 28 QML files under `CustomChartViewPas.qml/`, including:

- `main.qml`, `HomeScreen.qml`, `BleConnectScreen.qml`, `FtescCanScreen.qml`
- `SetupSignalInput.qml`, `MotorParamIdent.qml`, `FirmwareUpdate.qml`
- `RealTimeDisplayScreen.qml`, `CustomChartView.qml`, `CustomChartViewPas.qml`
- `PasCalibration.qml`, `PpmCalibration.qml`, `AdcCalibration.qml`
- `ValueSetters.qml`, `ValueList.qml`, `ValueSetupInt.qml`, `ValueSetupDouble.qml`
- `ValueSetupListEnum.qml`, `ValueSetupListEnumShort.qml`, `ValueSetupListEnumLong.qml`
- gauge, button, tab and spin-box components.

### Main object graph

`main.qml` imports the Flipsky QML modules `FtescLowLevelFace`, `ToolLib`, `uartcomm`, `valuesetups` and `bleuart`. The main window owns these application objects:

- `UartComm`: `FtescLf.uartComms()`
- Motor setup `ValueSetups`: `FtescLf.motorValSetup()`
- Signal/control setup `ValueSetups`: `FtescLf.signalValSetup()`
- Firmware metadata `ValueSetups`: `FtescLf.firmwareValSetup()`

The BLE connection overlay obtains the native `BleUart` instance from `FtescLf.bleDevice()`. On application completion it starts BLE scanning; a one-second reconnect timer can retry the last address up to five times after an unintentional disconnect. The scan/connect screen checks location permission before scanning and delegates a selected address to `FtescLf.connectBle(...)`.

### Initial identification and setup-read order

When the application reports a connected port, `main.qml` obtains firmware version and ESC ID. On a successful ID response, it:

1. clears CAN forwarding and selects the master path;
2. requests motor setup values;
3. invokes a 500 ms motor/signal ACK wait helper;
4. requests signal/control setup values;
5. invokes the 500 ms ACK wait helper again.

The QML also supports loading custom motor and signal XML files through `ValueSetups.qmloadXml`, and exporting them via `saveValueStreamXml`. This is a useful high-level confirmation that setup metadata is data-driven rather than hard-coded into every editor.

### Dynamic ValueSetup editor mapping

`ValueSetters.qml` chooses the component by the metadata type predicates:

- double values → `ValueSetupDouble.qml`
- integer values → `ValueSetupInt.qml`
- list/enum values → `ValueSetupListEnum.qml`
- long enum lists → `ValueSetupListEnumLong.qml`
- short enum lists → `ValueSetupListEnumShort.qml`

`SetupSignalInput.qml` selects the UI branch from `input_signal_type`: off, UART, PPM, ADC or PAS. UART-only controls include the tank-turnaround mode and slow-release behavior. PPM and ADC expose calibration views; PAS exposes calibration and curve/realtime views.

### CAN master/slave UI

`FtescCanScreen.qml` reads master and slave IDs and obtains firmware versions for the selected nodes. Switching between master and slave changes `setCanForwardSendFlag` and the selected CAN ID before issuing motor and signal setup reads. This is UI-level evidence of target selection and read routing; it does not establish the exact transmitted CMD `0x10` envelope in the native lower-level send path.

## 3. FTESC ValueSetup schema and version evolution

The application resources contain `ControlSetupValueTable.xml`, motor setup XML files (legacy, official and beta variants depending on release), and `FirmwareVersionInf.xml` for V1.0 through V1.6.

All profiles use the same outer structure:

```xml
<ValueSetups>
  <Values> ... </Values>
  <ValueSeque><seque>...</seque> ... </ValueSeque>
  <Clustering> ... </Clustering>
</ValueSetups>
```

Each entry in `Values` has an XML ID (element tag) and metadata such as `valName`, `valType`, range/step/default fields, scale, decimal precision, enum labels, read-only/invisible flags and display appearance. The explicit `ValueSeque` is the serialization order; it must not be replaced with XML child order or alphabetic sorting. `Clustering` provides the UI grouping hierarchy.

### Control profile counts

| Embedded resource version | Values | ValueSeque entries | Clusters |
|---|---:|---:|---:|
| 1.0 | 24 | 24 | 4 |
| 1.1 | 24 | 24 | 4 |
| 1.2 | 26 | 26 | 4 |
| 1.3 | 36 | 36 | 5 |
| 1.4 | 46 | 46 | 5 |
| 1.5 | 67 | 67 | 6 |
| 1.6 | 69 | 69 | 6 |

Type-code distributions in the V1.6 control table: type 1 = 36, type 2 = 8, type 4 = 19, type 6 = 3, type 7 = 3. The QML editor factory above confirms distinct handling for double, integer and enum/list variants. The V1.6 control clusters include General, PPM, ADC, UART and PAS.

The 1.1→1.2 table changes the smart-switch enum and introduces additional ADC/UART fields; V1.3 adds PAS settings; V1.4 adds brake-light/cruise/tank-turnaround/multi-ESC fields; V1.5 grows to 67; V1.6 has 69 serialized control fields. The detailed per-version XML files and hashes remain on the REA analysis host and are not copied into this public repository.

### Motor profile serialization and metadata-only entries

| Version | Profile | Values | ValueSeque | Values omitted from sequence |
|---|---|---:|---:|---|
| 1.0–1.3 | legacy motor table | 24–25 | 21–22 | 3 metadata/UI entries |
| 1.4 | official / beta | 60 | 59 | `motor_rated_current` |
| 1.5 | official | 94 | 93 | `motor_rated_current` |
| 1.5 | beta | 80 | 79 | `motor_rated_current` |
| 1.6 | official | 94 | 93 | `motor_rated_current` |
| 1.6 | beta | 94 | 93 | `motor_rated_current` |

The legacy motor tables omit `battery_cells_s`, `motor_rated_current` and `battery_cutoff_v` from `ValueSeque`; the newer official/beta tables omit `motor_rated_current`. This is deliberate metadata-vs-serialization evidence: the existence of a UI metadata field does not mean it is transmitted in the ordered setup stream. Any replacement serializer must use `ValueSeque` as the authority.

### Direct compatibility check against the offline serializer

The actual V1.6 control and official motor XML files were checked against the repository's existing type-encoding branches:

| Profile | Observed (valType, valueTET) combinations | Missing/unsupported required type metadata |
|---|---|---:|
| Control V1.6 | (2,1)=7; (4,1)=19; (1,9)=33; (2,3)=1; (1,7)=3; (6,1)=3; (7,1)=3 | 0 |
| Motor official V1.6 | (4,1)=9; (1,9)=61; (2,5)=1; (1,7)=13; (2,1)=9 | 0 |

Every serialized entry has a `valType` and `valueTET` combination accepted by the existing offline encoder/decoder branches. The actual Values child order differs from `ValueSeque` in **both** V1.6 tables, so serializing by XML child order would produce a wrong byte layout even when all individual encoders are correct. The existing `encode_profile_block(..., profile_order, ...)` design correctly makes the explicit sequence authoritative.

This is a static compatibility check of field/type metadata, not a validation against live ESC responses. The source XML remains on the REA analysis host; no copyrighted full profile table is copied into the repository.

Each `FirmwareVersionInf.xml` has a `firmware_ver` field whose enum label tracks that resource version (1.0–1.6).

**Important boundary:** these are the Android V1.6 app's embedded FTESC profiles. They do not close the separately unresolved TopFlow V1.7 XML resource or TopFlow model/SKU mapping.

## 4. Firmware resource inventory and static image characteristics

The native `ftescFw` resource contains 31 filename entries but only **17 unique binaries by SHA-256**; the duplicate entries are retained in the extraction manifest. Every unique image is exactly **165,880 bytes**.

For all 17 unique images:

- the first little-endian word is a pointer in SRAM, generally `0x20011F40` (one variant uses `0x20012EE8`);
- the second word is `0x08009019`, a Thumb reset-vector address;
- the prefix is consistent with a Cortex-M vector table and an image laid out for internal flash near `0x08009000`.

This is a strong architectural inference from the vector-table shape, **not** identification of the exact MCU, flash geometry or board revision. Binwalk/file did not identify a standard container format. The sample images show non-uniform data and some visible strings; no conclusion is made that the binaries are encrypted or signed.

No firmware images are committed to GitHub. The extracted files, their names and SHA-256 values remain in the private REA analysis workspace.

## 5. Firmware UI/update workflow

The QML update screen:

- lists bundled firmware names through `FtescLf.qmlfirmwareList()`;
- accepts custom `.bin` selection separately;
- warns that the selected firmware must be correct because an incorrect image may damage the ESC;
- states that the update must be performed with the target as master (the UI blocks updating a slave through the current master route);
- calls `FtescLf.firmwareUpdatePro(mode, statusType, confirmed, bundledVersion, customFile)` only after user confirmation;
- exposes an explicit `Enter bootloader` action and warns that entering bootloader clears settings;
- after success, waits five seconds, disconnects and instructs the user to reconnect.

The native API `qmlfirmwareList()` is at `0x00232C48`; it uses the resource path template `:/ftescFw/%1`. `qmlfirmwareData(QString const&)` is at `0x00232D30` and performs a `QFile` open/read-all flow for a selected file. The native `firmwareWriteToFtesc(QByteArray&)` routine at `0x002310B4` calls `eraseFirmware` before the later write loop. This establishes an erase-then-write sequence, but not the cryptographic transform, checksum/signature verification or exact block protocol.

The QML result codes map to:

| Return | UI meaning |
|---:|---|
| 1 | success; wait and reconnect |
| -1 | Bluetooth not connected |
| -2 | not in bootloader mode |
| -3 | invalid firmware |
| -4 | file could not be opened |
| -5 | file too large; custom-file UI limit states 150 Kbyte |
| -6 | UUID acquisition timeout |
| -7 | encrypted-data write timeout |
| -8 | firmware update failed; reconnect and retry |

The 150 Kbyte UI limit is associated with the custom-file validation path. It must not be naively applied to the separate bundled-firmware path: the embedded bundled images are 165,880 bytes. The difference is recorded for further source tracing, not treated as evidence that the bundled images are rejected.

### Firmware protocol still unresolved

- exact bootloader entry command and bootloader response;
- exact erase layout and region boundaries;
- exact write block size and sequence numbering;
- meaning and generation of “encrypted data”;
- key derivation, cipher, nonce/IV, authentication and checksum;
- firmware integrity/version/model binding checks;
- retry, resume, abort and recovery after partial flash;
- mapping of the 17 unique binaries to exact hardware/SKU/ESC revisions.

No update was started, no firmware was transmitted, and no ESC was connected.

## 6. Progress and next work

This pass closes a substantial static-resource discovery gap: app-owned QML, FTESC parameter profiles, grouping/editor behavior, CAN screen logic and embedded firmware inventory are now recovered. It does not implement the replacement UI or serializer and does not validate protocol or firmware behavior on hardware. The whole-product weighted estimate therefore remains **72.6%** (79.9 / 110).

Suggested separate static sub-workstream: Android V1.6 UI/resource reconstruction **80%** (resource tables, screen inventory, ValueSetup metadata and update UI recovered; exact runtime binding/complete native call graph still open).

Next probes:
1. resolve QML signal handlers and native bindings for each setup editor;
2. compare V1.6 embedded FTESC ValueSetup profiles with the existing repository ValueSetup parser and add safe synthetic regression fixtures;
3. recover the full native firmware image selection/mapping and firmware protocol without execution;
4. continue Windows V1.6/V1.7 function-level diff and resolve the protected Windows BLE write edge;
5. recover TopFlow V1.7 metadata independently; do not substitute FTESC profiles.

## 7. Evidence and reproducibility details

- Android package SHA-256: `26404ff6467971ff7c0fedbe1f326c6b0ccb5722571b7309d9913818960b4d7e`.
- ARM64 application library SHA-256: `7fba6a69f3719b70dfb7eee87c97e41aad2d8f48d1feec7058a0e5975a5ea2fc`.
- QML resource initializer table roots: see section 1.
- QML extraction: 29 nodes / 28 files, no errors.
- FTESC XML extraction: 33 nodes / 24 files, no errors.
- Firmware extraction: 34 nodes / 31 entries / 17 unique binaries, no errors.
- Icon extraction: 20 nodes / 18 files, no errors.

## Safety record

- No APK or native library was executed.
- No Android handset was contacted.
- No BLE scan, pairing, connection or GATT operation was performed.
- No UART/CAN transmission, ESC command, bootloader command or firmware write was performed.
- No extracted firmware binary was executed or flashed.
- Nextcloud original files remain unchanged.
