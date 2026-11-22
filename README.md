# Flipsky ESC Tool Protocol Research

Static reverse engineering and protocol research for **Flipsky ESC Tool V1.7**. This public repository contains the evidence log, extracted application metadata, protocol documentation, offline codecs, reproducible scripts and test suite.

> **Overall project progress: 72.6% unrounded (displayed as 73%, estimated, 22 November 2026).** This is a weighted estimate for a complete open-source desktop replacement, not merely the offline protocol codecs. It replaces the earlier 90–92% figures, which overstated readiness because the desktop UI, actual serial/BLE transports and hardware validation are not implemented.

| Work package | Relative weight (points) | Progress |
|---|---:|---:|
| Binary inventory and static application mapping | 10% | 100% |
| FTESC UART framing, parser and stream handling | 10% | 100% |
| V1.7 request/response command coverage | 20% | 87% |
| Setup metadata, ValueSeque ordering and typed serializer | 10% | 95% |
| Direct CAN and V1.7 gateway/slave routing | 10% | 60% |
| Firmware authorization, transfer and bootloader flow | 10% | 55% |
| Separate VESC/FSESC profile and source comparison | 10% | 85% |
| Open-source desktop UI and real serial/BLE integration | 15% | 20% |
| Reproducible extraction, unit tests and CI | 10% | 100% |
| Hardware validation | 5% | 0% |
| **Weighted overall estimate** | **110 points** | **72.6%** |

The project goal is a maintainable open-source client with an FTESC adapter and a separate VESC/FSESC adapter. The VESC UART profile now includes an incremental stream layer; GitHub Actions run #156 validates the full **159-test** offline suite and Python compilation. The 72.6% project score (73% rounded) does not mean it is ready to control an ESC: no hardware session has been validated and all encoders are offline-only.

See [STATUS](docs/STATUS.md), [ROADMAP](docs/ROADMAP.md), [PROGRESS_LOG](docs/PROGRESS_LOG.md), [NEXTCLOUD_SOFTWARE_INVENTORY](docs/NEXTCLOUD_SOFTWARE_INVENTORY.md), [TOOLING_AUDIT](docs/TOOLING_AUDIT.md) and [ANALYSIS_CHECKPOINT](docs/ANALYSIS_CHECKPOINT.md) for scoring, source inventory, tooling and blockers.

## Artifact under analysis

- File: `Flipsky_ESC_Tool_V1.7_20261029.exe`
- Size: 50,611,200 bytes
- SHA-256: `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`
- Format: PE32, x86, native Windows GUI application
- CLR/.NET header: absent
- Analysis tools: Ghidra 12.2, Rizin 0.9.1 and the REA reverse-engineering toolkit

The binary contains unusual `.enigma1` and `.enigma2` sections and other protection-like characteristics. A protected or packed build is plausible, but the exact protector and unpacking status have not been established.

The 50.6 MB executable remains on the REA analysis host; it is not included in this repository. It has not been replaced by a truncated copy or an LFS pointer. Its exact identity and hash are recorded in [ARTIFACT_INVENTORY](docs/ARTIFACT_INVENTORY.md).

## Confirmed application architecture

The application is built around Qt 5, C++ and QML. Identified modules include QtQuick, QtQuick.Controls, QtQuick.Layouts, QtCharts, Qt5SerialPort and Qt5Bluetooth, plus internal Flipsky modules:

- `Flipsky.ftesc.FtescLowLevelFace`
- `Flipsky.ftesc.ToolLib`
- `Flipsky.ftesc.uartcomm`
- `Flipsky.ftesc.valuesetups`
- `Flipsky.ftesc.bleuart`

The high-level `FtescLowLevelFace` façade coordinates UART and BLE. The separate `uartPackData` Qt meta-object exposes `sendDataToESC`, `uartPackDataFromESC`, `uartPackDataHandle` and `uartPackDataTimerSl`.

See [QT_CONNECTION_REGISTRATION](docs/QT_CONNECTION_REGISTRATION.md), [QT_METAOBJECT](docs/QT_METAOBJECT.md), [QT_METACALL_DISPATCH_MAP](docs/QT_METACALL_DISPATCH_MAP.md), [TRANSPORT_PIPELINE](docs/TRANSPORT_PIPELINE.md) and the new [V1.7 BLE GATT reconstruction](docs/BLE_GATT_V1_7_REVERSE_ENGINEERED.md).

## V1.7 UART framing

The V1.7 sender and receiver support two frame forms.

**Short frame**

`AA | LEN8 | INFO | CRC16_BE | DD`

**Extended frame**

`BB | LEN16_BE | INFO | CRC16_BE | DD`

INFO is the command byte followed by command-specific DATA. The sender selects the short form for INFO lengths 1–255 and the extended form above 255. The receiver rejects zero-length short payloads and extended lengths at or below 254. The constructor initializes the maximum-payload field to `0x2710` (10,000 bytes).

The checksum is **CRC-16/MODBUS**: reflected polynomial `0xA001`, initial value `0xFFFF`, final XOR `0x0000`. It covers INFO only and is transmitted high byte first. The embedded split lookup tables match CRC-16/MODBUS; the standard check vector `123456789` yields `0x4B37`.

The receive parser distinguishes valid consumed frames, invalid candidates and incomplete candidates. It advances one byte after invalid input and loops after each complete frame, so multiple frames in one input buffer are supported. See [WIRE_FRAME_FORMAT](docs/WIRE_FRAME_FORMAT.md), [RECEIVE_BUFFER_STATE](docs/RECEIVE_BUFFER_STATE.md) and [TRANSPORT_PIPELINE](docs/TRANSPORT_PIPELINE.md).

## Parameter resources

**Nineteen unique Zlib XML resources** were recovered from 20 candidate offsets (one duplicate). The derived parameter catalog now contains:

- 1,152 metadata rows across profile variants;
- 286 distinct XML parameter IDs;
- 19 profile/resource variants;
- 1,135 parameters listed in `ValueSeque` transmission order;
- 17 metadata entries omitted from `ValueSeque` (preserved as omitted, not serialized).

Families: 7 control, 6 motor, 5 motor-signal/FOC and 1 encoder profile. Only 1 of 19 profiles has its `Values` XML order identical to `ValueSeque`; the serializer therefore uses the explicit sequence, never document order.

Families include CAN, UART, PPM, ADC, PAS, battery and motor current, eRPM, phase resistance and inductance, flux, FOC gains, encoders, PWM, thermal sensing and battery cutoffs.

The XML files are application metadata, not firmware images. Values and limits in them are **not** recommendations for safe ESC or motor configuration.

The large catalog/resource artifacts are stored as gzip-compressed Base64 payloads to keep transfers reproducible. Restore them with:

```bash
python scripts/restore_payloads.py --root .
```

Rebuild the catalog and ordered profiles with `scripts/build_parameter_catalog.py` and `scripts/ftesc_profiles.py`.

## Offline protocol implementation

The repository contains standard-library-only Python codecs for both protocol families. They build and parse byte structures only; they do not open serial/CAN/BLE interfaces or transmit commands.

- `scripts/ftesc_frame.py`: CRC-16/MODBUS, short/extended frame encoder, frame decoder and concatenated-frame decoder.
- `scripts/ftesc_stream.py`: incremental UART decoder, retaining incomplete frames and recovering after invalid candidates.
- `scripts/ftesc_protocol.py`: INFO envelopes, realtime telemetry, V1.4/V1.6 legacy response parsing and ESC-ID lists.
- `scripts/ftesc_requests.py`: V1.7 request builders plus version-specific V1.4/V1.6 UART builders, including CMD 0x10 CAN forwarding, CMD 0x02 control layouts and CMD 0x20.
- `scripts/ftesc_responses.py`: V1.7 PPM/ADC, firmware identity, UUID, text, setup ACK, motor-signal and generic TopFlow response decoders.
- `scripts/ftesc_setup_serializer.py`: typed ValueSetup encoder and marker-validated ValueSeque response decoder.
- `scripts/ftesc_firmware.py`: offline-only V1.7 firmware erase/write payload and 240-byte XOR block codec.
- `scripts/ftesc_can.py`: direct FTESC CAN V1.4 extended-ID codec, CRC validation, periodic telemetry decoders and offline control-command encoders.
- `scripts/vesc_uart.py`: VESC 0x02/0x03/0x04 UART frame codec and CRC-16/XMODEM-compatible checksum parameters.
- `scripts/vesc_can.py`: VESC 29-bit extended CAN identifier composition and offline basic command encoders.
- `scripts/extract_embedded_xml.py`, `scripts/build_parameter_catalog.py`, `scripts/ftesc_profiles.py`: reproducible XML extraction, catalog generation and ValueSeque ordering.
- `tests/`: unit tests covering framing, streaming, requests, responses, setup encoding/decoding, firmware blocks and direct CAN.

Run the test suite from the repository root:

```bash
python -m unittest discover -s tests -v
python -m compileall -q scripts tests
```

**Latest verified result:** GitHub Actions [run #195](https://github.com/Estcool9/flipsky-esc-protocol-analysis/actions/runs/45018768452) passed **159 tests, 0 failures**; catalog/profile regeneration and `compileall` also passed. The offline workflow restores payloads, regenerates the catalog and profiles, validates deterministic outputs, runs the tests and compiles Python sources.

## Official V1.4/V1.6 protocol references

The repository keeps published protocol versions distinct from direct observations of the V1.7 executable.

- [FTESC UART Protocol V1.6](docs/FTESC_UART_PROTOCOL_V1.6.md): serial framing, CRC, command layouts, CAN-over, keepalive, firmware identity and V1.4-to-V1.6 differences.
- [FTESC Direct CAN Protocol V1.4](docs/FTESC_CAN_PROTOCOL_V1.4.md): 29-bit extended IDs, fixed prefix, direct-CAN command namespace, CRC and periodic telemetry.
- [CAN forwarding state](docs/CAN_FORWARDING_STATE.md): V1.7 target-ID state and the still-unresolved native insertion/routing path.
- [External implementation cross-check](docs/EXTERNAL_IMPLEMENTATION_CROSSCHECK.md): independent FT85BD implementation and concrete frame-vector comparison.
- [External references](docs/EXTERNAL_REFERENCES.md): official Flipsky product and update references.

Important version differences:
- V1.4 and V1.6 use different byte ordering for the first four DATA bytes of UART CMD 0x02. Separate builders are provided.
- V1.4/V1.6 CMD 0x1A documents a seven-byte response; the V1.7 desktop response dispatcher emits a no-DATA acknowledgement.
- V1.4 CMD 0x1D is reset/reboot with one reserved zero byte. V1.7 reuses 0x1D for TopFlow and motor-signal setup operations.
- Direct-CAN command 0x00 means current-with-gear; UART INFO command 0x00 means realtime telemetry. Numeric command IDs are bus-specific.

## Firmware update analysis

The V1.7 application performs a UUID-based TEA authorization preflight:
- requests the UUID with CMD 0x21;
- uses a 16-byte challenge and a 32-round TEA block transform with the device UUID as key;
- sends the encrypted challenge with CMD 0x22;
- waits for an authorization acknowledgement.

Separate native request methods implement boot mode (0x13), erase (0x16) and firmware block write (0x18). The write path uses a 240-byte block payload and a separate XOR transform. The complete UI/bootloader state machine, retry progression and exact V1.7 firmware image format remain unfinished. The V1.6 Android APK now provides 17 unique embedded firmware images (165,880 bytes each) with raw Cortex-M-like vector-table headers; this does not prove their MCU/SKU mapping or establish the V1.7 update image format. No firmware was flashed. See [Android V1.6 QML/ValueSetup/firmware resources](docs/ANDROID_V1_6_QML_VALUESETUPS_AND_FIRMWARE_RESOURCES.md).

See [FIRMWARE_UPDATE_FLOW](docs/FIRMWARE_UPDATE_FLOW.md).

## VESC / FSESC compatibility

The new Nextcloud source folder contained four Flipsky VESC V1.0 PDFs (UART and direct CAN, English and Chinese). They specify VESC firmware V3.00+ and match the pinned upstream VESC Tool/firmware source for UART framing, CRC, command IDs and basic CAN identifier composition.

This is a **different product family** from the FTESC binary analyzed here. Flipsky identifies FT ESC as NON-VESC and FSESC as VESC-based; their programming tools and CAN gateways are not interchangeable.

New offline modules:
- `scripts/vesc_uart.py`: VESC 02/03/04 framing and 0x1021 CRC.
- `scripts/vesc_can.py`: VESC extended CAN identifiers and basic control-payload encoders.
- `scripts/ftesc_*.py`: separate FTESC framing, commands and CRC.

See [Flipsky VESC V1.0 analysis](docs/FLIPSKY_VESC_PROTOCOL_V1.0.md), [protocol-family matrix](docs/PROTOCOL_FAMILY_MATRIX.md) and [source-pinned comparison](docs/VESC_COMPARISON.md).

## BLE GATT reconstruction

Static analysis of V1.7 confirms the BLE UART service UUID (`0000fff0-0000-1000-8000-00805f9b34fb`), TX characteristic UUID (`0000fff2-0000-1000-8000-00805f9b34fb`) and RX characteristic UUID (`0000fff1-0000-1000-8000-00805f9b34fb`). Controller/service state callbacks and the CCCD descriptor lookup (`0x2902`) are mapped.

The receive callback `FUN_004828D0` passes the incoming `QByteArray` to the shared AA/BB incremental frame-stream handler `FUN_0049CA30`, the same parser used by UART. On transmit, the shared lower-level send slot routes the already-framed byte array into a BLE branch which slices it into fixed 20-byte application chunks and processes them through an asynchronous queue. The independent V1.6 Android native implementation confirms 20-byte chunks, directly calls `QLowEnergyService::writeCharacteristic` with C++ `WriteMode=1` (`WriteWithoutResponse`), and writes CCCD bytes `01 00` to `0x2902` (notifications). Its `FtescLowLevelFace::bleDataRx` slot calls `uartPackData::uartPackDataHandle`, the same FTESC stream parser. These are static observations, not a live BLE capture; 20 bytes is not asserted to be the negotiated ATT MTU.

For Windows V1.7, the final indirect `writeCharacteristic` target and write mode remain unresolved inside the protected Enigma region. Android V1.6's exact `WriteWithoutResponse` mode and CCCD `01 00` provide strong cross-platform corroboration, not proof of the Windows call edge. Negotiated ATT MTU, retries and live BLE behavior remain unverified. See [BLE_GATT_V1_7_REVERSE_ENGINEERED](docs/BLE_GATT_V1_7_REVERSE_ENGINEERED.md), [BLE_TRANSPORT_SHARED_PARSER_AND_CHUNKING](docs/BLE_TRANSPORT_SHARED_PARSER_AND_CHUNKING.md), [ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED](docs/ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md) and [TRANSPORT_PIPELINE](docs/TRANSPORT_PIPELINE.md).

## What remains before 100%

1. Recover the missing TopFlow ValueSetup XML and map profiles to exact hardware SKUs. The separate FTESC V1.0–V1.6 Android ValueSetup XML family is now extracted and analyzed; do not substitute it for TopFlow.
2. Locate the V1.7 native insertion point for UART CMD 0x10 and complete slave response routing/correlation.
3. Complete the firmware-update state machine, retries, bootloader transitions and exact image format; obtain a legitimate firmware sample for offline validation.
4. Complete function-level comparison of the three staged V1.6 Windows executables against V1.7; first-pass PE32 identity/marker comparison is now recorded.
5. Resolve the remaining Android Qt signal/slot connection edge, dynamic QML/native method bindings and compare screen behavior with the Windows desktop version.
6. Map the remaining dynamic UI/property behavior and implement the desktop replacement views.
7. Validate protocol assumptions against captured UART/CAN/BLE traffic and hardware, including negotiated ATT MTU, retransmission, UART baud selection and timing units. BLE application chunking, Android V1.6 write mode/CCCD and shared parser routing are now statically identified; Windows V1.7 call-edge proof remains open.

Hardware validation is still **0%**. The 72.6% weighted estimate reflects static evidence, offline implementation and CI-verified tests; it does not mean the protocol is safe or verified on a live ESC.

## Safety and scope

No serial, CAN or BLE command was transmitted. No physical ESC was connected and no firmware was flashed. The builders are offline byte encoders, not hardware-control tools. Do not use parameter values, current limits, motor-control commands or firmware images from this research as operating recommendations without Flipsky documentation and controlled hardware validation.
