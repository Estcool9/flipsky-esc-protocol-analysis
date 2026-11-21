# Flipsky ESC Tool Protocol Research

Static reverse engineering and protocol research for **Flipsky ESC Tool V1.7**. This repository records the observed application architecture, parameter resources, Qt/UART wiring, hypotheses, evidence, and the roadmap toward an independently testable protocol implementation.

> **Overall progress: 32% (estimated, as of 22 November 2026).** This is a milestone-based estimate toward a sufficiently evidenced protocol specification and offline client, not a scientific measure of completeness.

## Project status

| Workstream | Estimated progress |
|---|---:|
| Binary inventory and integrity | 100% |
| Embedded XML extraction and validation | 100% |
| Parameter catalog generation | 100% |
| Qt/QML architecture identification | 80% |
| UART/Qt signal-slot mapping | 65% |
| UART implementation analysis | 30% |
| Frame format, command IDs, CRC and replies | 5% |
| VESC compatibility assessment | 25% |
| Offline parser / independent client | 0% |
| Hardware validation | 0% |
| **Overall** | **32%** |

Percentages describe progress by milestone. They are reviewed when new evidence is added. See [docs/STATUS.md](docs/STATUS.md), [docs/PROGRESS_LOG.md](docs/PROGRESS_LOG.md), and [docs/ROADMAP.md](docs/ROADMAP.md).

## Artifact under analysis

- File: `Flipsky_ESC_Tool_V1.7_20261029.exe`
- Size: 50,611,200 bytes
- SHA-256: `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`
- Format: PE32, x86, native Windows GUI application
- CLR/.NET header: absent
- Analysis tools: Ghidra 12.2, Rizin 0.9.1, REA reverse-engineering toolkit

The application contains unusual `.enigma1` and `.enigma2` sections and other protection-like characteristics. A protected/packed build is plausible; the exact protector and unpacking status are not confirmed.

## Findings so far

### Application architecture

The application is built around Qt 5, C++ and QML. Identified modules include QtQuick, QtQuick.Controls, QtQuick.Layouts, QtCharts, Qt5SerialPort and Qt5Bluetooth, as well as internal Flipsky modules:

- `Flipsky.ftesc.FtescLowLevelFace`
- `Flipsky.ftesc.ToolLib`
- `Flipsky.ftesc.uartcomm`
- `Flipsky.ftesc.valuesetups`
- `Flipsky.ftesc.bleuart`

The `ftesc` namespace is a strong clue that this binary targets the FT ESC software family. The exact ESC model and board revision still need confirmation.

### UART and Qt connection wiring

The Qt connection-registration code at VA `0x00483910` contains these observed signal/slot relationships:

- `QSerialPort::readyRead()` → `UartComm::uartDataHandleAvailable()`
- `uartPackDataFromESC(QByteArray&)` → `uartPackDataFromESC(QByteArray&)` (legacy Qt signal/slot signature pairing)
- `uartCommSendToFtesc(QByteArray&)` → `sendDataToESC(QByteArray&)`
- `lowLevelSendDataToFtesc(QByteArray&)` → `sendDataToESC(QByteArray&)`
- Firmware-version and motor-configuration acknowledgement slots are also wired.
- BLE receive and disconnect signals are registered in the same component.

These findings show event wiring, not yet the packet encoding, CRC, command IDs or exact serial frame boundaries. See [docs/QT_CONNECTION_REGISTRATION.md](docs/QT_CONNECTION_REGISTRATION.md).

### Parameter resources

Thirteen compressed Zlib XML resources have been recovered and validated. The derived catalog has:

- 736 rows across profile variants
- 222 distinct parameter IDs
- 13 profile/resource variants

Parameter families include CAN, UART, PPM, ADC, PAS, battery and motor current, eRPM, phase resistance and inductance, flux, FOC gains, encoders, PWM, thermal sensing and battery cutoffs.

The catalog is application metadata; values found in it are **not** recommendations for safe ESC or motor configuration.

## VESC Tool comparison

Flipsky distinguishes between VESC-based FSESC products and the independently developed FT ESC family. Its published documentation describes the FT ESC line as intended for Flipsky ESC Tool, while FSESC products use VESC Tool and corresponding firmware versions.

The application name, Qt stack and control features may look similar to VESC Tool, but that does not demonstrate wire-protocol compatibility. The `Flipsky.ftesc.*` namespaces make an FT ESC target likely. We will compare actual opcodes, framing and checksum logic before asserting any compatibility.

See [docs/VESC_COMPARISON.md](docs/VESC_COMPARISON.md).

## What is still unknown

We have not yet established, with sufficient evidence:

- start/end markers and frame boundaries;
- length field and its encoding;
- command IDs / opcodes;
- payload structures for each query and response;
- CRC/checksum algorithm and parameters;
- integer and floating-point endianness;
- escaping, fragmentation, retry and timeout behaviour;
- authentication or secret-key handshake details;
- exact BLE framing and whether it wraps the UART protocol;
- whether any FT ESC operation shares wire-level code with VESC.

## Next technical steps

1. Locate the executable implementations behind the Qt meta-object slots and signal dispatch.
2. Trace `uartPackDataFromESC`, `sendDataToESC`, `lowLevelSendDataToFtesc` and `uartCommSendToFtesc`.
3. Identify buffer length checks, frame accumulation, checksums and dispatch tables.
4. Trace read-only query flows and acknowledgement structures end-to-end.
5. Compare observed constants and algorithms with the open VESC Tool and firmware implementations.
6. Build an offline parser and synthetic-frame tests before any physical ESC interaction.

No ESC firmware or passive serial capture is currently available. Static analysis of the application can continue without either.

## Repository contents

- `reports/`: technical summary, startup path and initial UART mapping
- `docs/`: project status, evidence notes, VESC comparison and roadmap
- `scripts/`: repeatable XML extraction and parameter-catalog generation
- `analysis-data/`: derived parameter catalog
- `embedded-xml/`: extracted embedded XML resources and extraction manifest

## Safety and handling

This project is currently a static-analysis effort. The application has not been used to flash firmware or send commands to a physical ESC during this analysis. Do not send unknown frames to a controller connected to a motor. Do not treat default values or hardware limits found in the application as safe operating recommendations. Firmware flashing, bootloader erasure and motor-control writes are out of scope until the protocol and failure modes are understood.

## References

- [Flipsky — Differences Between FT ESC and FSESC (9 January 2026)](https://flipsky.net/blogs/vesc-tool/differences-between-ft-esc-and-fsesc)
- [Flipsky — Tips for compatible FSESC and VESC Tool versions (27 September 2024)](https://flipsky.net/blogs/vesc-tool/tips-for-compatible-fsesc-and-vesc_tool-version)
- [VESC Tool source repository](https://github.com/vedderb/vesc_tool)
- [VESC firmware source repository](https://github.com/vedderb/bldc)
