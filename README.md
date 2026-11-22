# Flipsky ESC Tool Protocol Research

Static reverse engineering and protocol research for **Flipsky ESC Tool V1.7**. This public repository contains the evidence log, extracted application metadata, protocol documentation, offline codecs, reproducible scripts and test suite.

> **Overall progress: 92% (estimated, 22 November 2026).** This is a milestone-weighted estimate for completing the documented offline protocol model. It is not a measure of certainty, commercial-app feature completeness, hardware safety, or live-device validation.

## Project status

| Workstream | Progress |
|---|---:|
| Executable inventory and integrity | 100% |
| Embedded XML extraction and validation | 100% |
| Parameter catalog generation | 100% |
| Qt/QML architecture and class ownership | 90% |
| Qt meta-object, signal/slot and method dispatch | 100% |
| UART outer frame and CRC reconstruction | 100% |
| UART receive buffering and resynchronization | 95% |
| V1.7 request payload builders | 90% |
| V1.7 response dispatch and decoders | 95% |
| ValueSetup serializer and response decoder | 98% |
| Firmware authorization and block codec | 85% |
| Direct CAN V1.4 identifier, CRC, telemetry and command codec | 95% |
| UART CAN-over envelope codec | 90% |
| V1.7 native CAN wrapper insertion and slave routing | 40% |
| BLE transport static analysis | 75% |
| VESC compatibility assessment | 75% |
| Reproducible extraction, catalog and CI | 95% |
| TopFlow XML and SKU/profile mapping | 40% |
| V1.6 executable comparison | 0% |
| Hardware validation | 0% |
| **Overall estimate** | **92%** |

See [STATUS](docs/STATUS.md), [PROGRESS_LOG](docs/PROGRESS_LOG.md), [ROADMAP](docs/ROADMAP.md) and [ANALYSIS_CHECKPOINT](docs/ANALYSIS_CHECKPOINT.md) for the current checkpoint and detailed work history.

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

See [QT_CONNECTION_REGISTRATION](docs/QT_CONNECTION_REGISTRATION.md), [QT_METAOBJECT](docs/QT_METAOBJECT.md), [QT_METACALL_DISPATCH_MAP](docs/QT_METACALL_DISPATCH_MAP.md) and [TRANSPORT_PIPELINE](docs/TRANSPORT_PIPELINE.md).

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

Thirteen compressed Zlib XML resources were recovered and validated. The derived parameter catalog contains:

- 736 rows across profile variants;
- 222 distinct parameter IDs;
- 13 profile/resource variants.

Families include CAN, UART, PPM, ADC, PAS, battery and motor current, eRPM, phase resistance and inductance, flux, FOC gains, encoders, PWM, thermal sensing and battery cutoffs.

The XML files are application metadata, not firmware images. Values and limits in them are **not** recommendations for safe ESC or motor configuration.

The large catalog/resource artifacts are stored as gzip-compressed Base64 payloads to keep transfers reproducible. Restore them with:

```bash
python scripts/restore_payloads.py --root .
```

Rebuild the catalog and ordered profiles with `scripts/build_parameter_catalog.py` and `scripts/ftesc_profiles.py`.

## Offline protocol implementation

The repository contains a standard-library-only Python codec. It builds and parses byte structures only; it does not open serial/CAN/BLE interfaces or transmit commands.

- `scripts/ftesc_frame.py`: CRC-16/MODBUS, short/extended frame encoder, frame decoder and concatenated-frame decoder.
- `scripts/ftesc_stream.py`: incremental UART decoder, retaining incomplete frames and recovering after invalid candidates.
- `scripts/ftesc_protocol.py`: INFO envelopes, realtime telemetry, V1.4/V1.6 legacy response parsing and ESC-ID lists.
- `scripts/ftesc_requests.py`: V1.7 request builders plus version-specific V1.4/V1.6 UART builders, including CMD 0x10 CAN forwarding, CMD 0x02 control layouts and CMD 0x20.
- `scripts/ftesc_responses.py`: V1.7 PPM/ADC, firmware identity, UUID, text, setup ACK, motor-signal and generic TopFlow response decoders.
- `scripts/ftesc_setup_serializer.py`: typed ValueSetup encoder and marker-validated ValueSeque response decoder.
- `scripts/ftesc_firmware.py`: offline-only V1.7 firmware erase/write payload and 240-byte XOR block codec.
- `scripts/ftesc_can.py`: direct FTESC CAN V1.4 extended-ID codec, CRC validation, periodic telemetry decoders and offline control-command encoders.
- `scripts/extract_embedded_xml.py`, `scripts/build_parameter_catalog.py`, `scripts/ftesc_profiles.py`: reproducible XML extraction, catalog generation and ValueSeque ordering.
- `tests/`: unit tests covering framing, streaming, requests, responses, setup encoding/decoding, firmware blocks and direct CAN.

Run the test suite from the repository root:

```bash
python -m unittest discover -s tests -v
python -m compileall -q scripts tests
```

**Latest verified result on REA:** **124 tests passed, 0 failures**. The catalog and profile regeneration comparisons also passed. GitHub Actions is configured in [offline-checks.yml](.github/workflows/offline-checks.yml) to restore payloads, regenerate the catalog and profiles, compare them byte-for-byte, run the tests and compile Python sources.

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

Separate native request methods implement boot mode (0x13), erase (0x16) and firmware block write (0x18). The write path uses a 240-byte block payload and a separate XOR transform. The complete UI/bootloader state machine, retry progression and exact firmware image format remain unfinished. No firmware image was available in the analysis workspace and no firmware was flashed.

See [FIRMWARE_UPDATE_FLOW](docs/FIRMWARE_UPDATE_FLOW.md).

## VESC compatibility

Flipsky's official product-family description distinguishes FT ESC (NON-VESC) from VESC-based FSESC products and says their tools are not interchangeable. Similar Qt technology, motor-control terminology or UI controls do not establish wire-protocol compatibility.

See [VESC_COMPARISON](docs/VESC_COMPARISON.md).

## What remains before 100%

1. Recover the missing TopFlow ValueSetup XML and map profiles to exact hardware SKUs.
2. Locate the V1.7 native insertion point for UART CMD 0x10 and complete slave response routing/correlation.
3. Complete the firmware-update state machine, retries, bootloader transitions and exact image format; obtain a legitimate firmware sample for offline validation.
4. Compare against a V1.6 executable if one becomes available.
5. Map the packed Qt/QML resource tree and the remaining dynamic UI/property behaviour.
6. Validate protocol assumptions against captured UART/CAN/BLE traffic and hardware, including BLE characteristic UUIDs/write mode, UART baud selection and timing units.

Hardware validation is still **0%**. The 92% estimate means the static evidence and offline implementation are substantially complete; it does not mean the protocol is safe or verified on a live ESC.

## Safety and scope

No serial, CAN or BLE command was transmitted. No physical ESC was connected and no firmware was flashed. The builders are offline byte encoders, not hardware-control tools. Do not use parameter values, current limits, motor-control commands or firmware images from this research as operating recommendations without Flipsky documentation and controlled hardware validation.
