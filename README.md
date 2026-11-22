# Flipsky ESC Tool Protocol Research

Static reverse engineering and protocol research for **Flipsky ESC Tool V1.7**. This repository records observed application architecture, embedded parameter resources, UART framing, CRC behaviour, evidence, scripts and the roadmap toward an independently testable protocol implementation.

> **Overall progress: 50% (estimated, as of 22 November 2026).** This is a milestone-weighted estimate toward a documented protocol and an offline client, not a scientific measure of certainty or a measure of the commercial app's feature completeness.

## Project status

| Workstream | Progress |
|---|---:|
| Executable inventory and integrity | 100% |
| Embedded XML extraction and validation | 100% |
| Parameter catalog generation | 100% |
| Qt/QML architecture and class ownership | 90% |
| UART/Qt signal-slot and meta-object mapping | 85% |
| Outer frame format and CRC reconstruction | 100% |
| Receive-buffer and resynchronization analysis | 90% |
| Inner command IDs and payload layouts | 12% |
| Public V1.6 UART protocol extraction | 100% |
| V1.4-to-V1.6 documented comparison | 90% |
| V1.6 Windows binary comparison | 0% |
| Firmware-update and TEA relationship | 55% |
| VESC compatibility assessment | 25% |
| Offline frame codec and tests | 100% |
| Hardware validation | 0% |
| **Overall estimate** | **50%** |

See [docs/STATUS.md](docs/STATUS.md), [docs/PROGRESS_LOG.md](docs/PROGRESS_LOG.md), [docs/ROADMAP.md](docs/ROADMAP.md), [docs/ANALYSIS_CHECKPOINT.md](docs/ANALYSIS_CHECKPOINT.md), and [docs/NEXTCLOUD_SOURCE_INVENTORY.md](docs/NEXTCLOUD_SOURCE_INVENTORY.md).

## Artifact under analysis

- File: `Flipsky_ESC_Tool_V1.7_20261029.exe`
- Size: 50,611,200 bytes
- SHA-256: `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`
- Format: PE32, x86, native Windows GUI application
- CLR/.NET header: absent
- Tools: Ghidra 12.2, Rizin 0.9.1 and the REA reverse-engineering toolkit

The binary contains unusual `.enigma1` and `.enigma2` sections and other protection-like characteristics. A protected/packed build is plausible, but the exact protector and unpacking status have not been established.

The executable itself remains on the REA analysis host. Its exact identity and hash are documented in [docs/ARTIFACT_INVENTORY.md](docs/ARTIFACT_INVENTORY.md). The GitHub API upload path available in this session could not stream the 50.6 MB executable as a single Git object. It has not been replaced by a truncated copy or an LFS pointer.

## Confirmed application architecture

The application is built around Qt 5, C++ and QML. Identified modules include QtQuick, QtQuick.Controls, QtQuick.Layouts, QtCharts, Qt5SerialPort and Qt5Bluetooth, plus internal Flipsky modules:

- `Flipsky.ftesc.FtescLowLevelFace`
- `Flipsky.ftesc.ToolLib`
- `Flipsky.ftesc.uartcomm`
- `Flipsky.ftesc.valuesetups`
- `Flipsky.ftesc.bleuart`

The high-level `FtescLowLevelFace` façade coordinates UART and BLE paths. A separate Qt meta-object named `uartPackData` includes `sendDataToESC`, `uartPackDataFromESC`, `uartPackDataHandle` and `uartPackDataTimerSl`.

See [docs/QT_CONNECTION_REGISTRATION.md](docs/QT_CONNECTION_REGISTRATION.md) and [docs/QT_METAOBJECT.md](docs/QT_METAOBJECT.md).

## Recovered outer UART framing

The receive parser and transmit builder independently support two frame forms.

**Short frame**

`AA | LEN8 | PAYLOAD | CRC16_BE | DD`

**Extended frame**

`BB | LEN16_BE | PAYLOAD | CRC16_BE | DD`

The sender selects the short form for payloads from 1 through 255 bytes and the extended form above 255 bytes. The receiver rejects zero-length short payloads and rejects extended lengths at or below 254. The constructor initializes the maximum-payload field to `0x2710` (10,000 bytes) in this binary.

The checksum is **CRC-16/MODBUS**: reflected polynomial `0xA001`, initial value `0xFFFF`, final XOR `0x0000`. It is calculated over the payload only and transmitted high byte first. The two 256-byte lookup tables embedded in the binary match generated CRC-16/MODBUS tables; the standard check vector `123456789` yields `0x4B37`.

The receive handler distinguishes:
- a positive return value for a valid frame's consumed length;
- `-1` for an invalid candidate, after which the caller advances one byte to search again;
- `-2` for an incomplete candidate.

The handler loops after a successfully consumed frame, allowing multiple complete frames in one input buffer. See [docs/WIRE_FRAME_FORMAT.md](docs/WIRE_FRAME_FORMAT.md) and [docs/RECEIVE_BUFFER_STATE.md](docs/RECEIVE_BUFFER_STATE.md).

## Parameter resources

Thirteen compressed Zlib XML resources were recovered and validated. The derived parameter catalog contains:

- 736 rows across profile variants;
- 222 distinct parameter IDs;
- 13 profile/resource variants.

Families include CAN, UART, PPM, ADC, PAS, battery and motor current, eRPM, phase resistance and inductance, flux, FOC gains, encoders, PWM, thermal sensing and battery cutoffs.

These XML resources are application metadata. Values and limits found in them are **not** recommendations for safe ESC or motor configuration.

## Offline frame codec

The repository contains a standard-library-only Python implementation:

- `scripts/ftesc_frame.py`: CRC-16/MODBUS, frame encoder, single-frame decoder and concatenated-frame decoder.
- `scripts/ftesc_stream.py`: incremental decoder retaining incomplete frames across chunks and recovering after invalid candidates.
- `tests/test_ftesc_frame.py`: unit tests for checksum, both frame forms, boundary lengths, incomplete input, corruption and concatenated frames.

Run the test suite from the repository root:

```bash
python -m unittest discover -s tests -v
```

**Observed result on REA:** 36 tests passed, 0 failures, including incremental stream tests.

This codec handles only the outer frame layer. It does not yet interpret inner command IDs, parameter payloads, authentication, firmware-update payloads or BLE-specific wrappers.

## VESC compatibility

Flipsky distinguishes its FT ESC family from VESC-based FSESC products. Similar Qt technology or similar UI controls do not establish protocol compatibility. The recovered Flipsky outer frame format is documented here; compatibility with VESC framing, opcodes and payload schemas remains unproven.

See [docs/VESC_COMPARISON.md](docs/VESC_COMPARISON.md).

## Open technical questions

- Inner command IDs/opcodes and operation-specific payload layouts.
- How read/write requests match acknowledgement signals.
- CAN forwarding and multi-ESC request/response semantics.
- Firmware-update block format and precise TEA routine usage.
- Whether ordinary UART payloads ever use TEA encryption.
- BLE's exact outer framing and whether it wraps the same frame format.
- Exact persistence/reset behaviour for all fragmented or corrupted input patterns.
- Compatibility across FT ESC hardware revisions.

The method named `tea_encrypt` is present in the Qt meta-object and TEA-like code was identified. Its confirmed use is in the firmware-update path. Systematic encryption of ordinary UART frames has **not** been demonstrated.

## Repository contents

- `docs/`: status, progress log, checkpoints, protocol evidence, inventories and VESC comparison.
- `reports/`: technical summary, startup path and initial Qt/UART wiring.
- `scripts/`: repeatable XML extraction, parameter catalog generation, payload restoration and frame codec.
- `tests/`: offline frame codec tests.
- `analysis-data/`: derived parameter catalogs (complete payloads are stored as gzip/base64).
- `embedded-xml/`: extracted embedded XML resources and extraction manifest (stored as gzip/base64).

To reconstruct the full catalogs and XML resources in a local clone, run:

```bash
python scripts/restore_payloads.py --root .
```

See [docs/PAYLOAD_FORMAT.md](docs/PAYLOAD_FORMAT.md) for the payload layout and verification procedure.

## Safety and handling

This is currently a static-analysis and offline-testing project. No physical ESC was tested and no firmware was flashed during this analysis. Do not send unknown frames to a motor-connected controller. Do not treat defaults or software limits as safe operating recommendations. Firmware flashing, bootloader erasure and motor-control writes remain out of scope until their protocols and failure modes are fully understood.

## References

- [Flipsky — Differences Between FT ESC and FSESC](https://flipsky.net/blogs/vesc-tool/differences-between-ft-esc-and-fsesc)
- [Flipsky — Tips for compatible FSESC and VESC Tool versions](https://flipsky.net/blogs/vesc-tool/tips-for-compatible-fsesc-and-vesc_tool-version)
- [VESC Tool source repository](https://github.com/vedderb/vesc_tool)
- [VESC firmware source repository](https://github.com/vedderb/bldc)


## Public V1.6 UART specification and version delta

The official Flipsky V1.6 UART protocol PDF and the earlier V1.4 protocol PDF were read from the Nextcloud project folder. The supplied ECU-side example source is preserved under reference/; it is not the ESC Tool application's source code or ESC firmware.

Confirmed V1.4-to-V1.6 changes:
- CMD 00 keeps the 28-byte base telemetry response and documents a longer auto-telemetry response with 12 reserved bytes and PAS RPM.
- CMD 02 moves the current request from DATA D0-D1 to D2-D3, with D0-D1 reserved.
- V1.6 adds a PAS-mode semantic alias for CMD 02; only D0 (PAS gear) is used in that mode.
- The outer AA/BB framing, INFO length definition, CRC-16/MODBUS and big-endian integer conventions remain unchanged.

One V1.6 PAS-response section lists extra PAS RPM bytes but retains DLEN 0x1C. Those extra bytes would require DLEN 0x20, so this is recorded as a source-document inconsistency.

See [docs/FTESC_UART_PROTOCOL_V1.6.md](docs/FTESC_UART_PROTOCOL_V1.6.md), [docs/V1_4_TO_V1_6_PROTOCOL_CHANGES.md](docs/V1_4_TO_V1_6_PROTOCOL_CHANGES.md), [docs/V1_7_BINARY_CROSS_REFERENCE.md](docs/V1_7_BINARY_CROSS_REFERENCE.md), and [docs/V1.6_MANUAL_NOTES.md](docs/V1.6_MANUAL_NOTES.md).

## More offline protocol tooling

scripts/ftesc_protocol.py now builds command INFO fields and complete outer frames, and parses selected V1.6 telemetry responses for CMD 00, CMD 02/CMD 20, CMD 1A and CMD 1E. The combined frame and command test suite has **26 passing tests** on REA.


## V1.7 Qt API string map

A new static map records high-level methods found in the V1.7 Qt string/meta-object data, including controls for duty, current, D-axis current, speed, position and brake current; automatic telemetry; CAN ID/identification flows; firmware version and firmware update methods; and encryption-related names. Candidate V1.6 opcode relationships are marked as hypotheses until their call paths and emitted bytes are confirmed.

See [docs/V1_7_QT_API_STRING_MAP.md](docs/V1_7_QT_API_STRING_MAP.md).
