# V1.7 end-to-end UART transport pipeline

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Analysis date:** 2026-11-22  
**Provider:** Ghidra 12.2 / REA 6.10.1

This report connects the request builders, Qt signals, outer frame encoder, serial write path, receive buffer and response dispatcher.

## 1. Four Qt objects identified from static meta-objects

The binary contains four adjacent revision-8 Qt static meta-objects:

| Class | Static meta-object | String data | Meta-data | Static meta-call |
|---|---:|---:|---:|---:|
| `FtescLowLevelFace` | `0x0051F218` | `0x00F215C0` | `0x00F20D60` | `0x004B98D0` |
| `ToolLib` | `0x0051F230` | `0x00F225C0` | `0x00F22380` | `0x004BAD80` |
| `UartComm` | `0x0051F248` | `0x00F232A0` | `0x00F22B40` | `0x004BC2B0` |
| `uartPackData` | `0x0051F260` | `0x00F24080` | `0x00F23FC0` | `0x004BDBA0` |

The `uartPackData` meta-object has four methods:

| Index | Method | Kind |
|---:|---|---|
| 0 | `sendDataToESC(QByteArray&)` | signal |
| 1 | `uartPackDataFromESC(QByteArray&)` | signal |
| 2 | `uartPackDataHandle(QByteArray&)` | slot |
| 3 | `uartPackDataTimerSl()` | slot |

The static meta-call at `0x004BDBA0` dispatches index 2 to `FUN_0049CA30` and index 3 to `FUN_0049C800`.

## 2. Outbound path: INFO payload to serial write

The native call and signal evidence gives this path:

1. A `UartComm` request method (for example `ftescControlDuty`) builds the INFO payload.
2. `FUN_00495910` logs the command, CAN-forward flag/ID, payload length and payload bytes, then calls `FUN_004BBC20`.
3. `FUN_004BBC20` activates UartComm signal index 0: `sendDataToESC(QByteArray&)`.
4. `FtescLowLevelFace::uartCommSendToFtesc` (method index 17, native `0x004819C0`) calls `FUN_0049C5C0`.
5. `FUN_0049C5C0` wraps the INFO payload:
   - `0xAA` + one-byte length for payload lengths 1–255;
   - `0xBB` + two-byte big-endian length for payload lengths 256–65,535;
   - CRC-16/MODBUS over payload bytes only;
   - CRC high byte, CRC low byte, `0xDD`.
6. The frame builder calls `FUN_004BDB20`, which activates `uartPackData` signal index 0: `sendDataToESC(QByteArray&)`.
7. `FtescLowLevelFace::lowLevelSendDataToFtesc` (method index 15, native `0x00481850`) checks the serial-port state and calls the QIODevice/QSerialPort write function pointer with the framed byte array.

The two signals named `sendDataToESC` belong to different Qt objects and represent different layers:
- UartComm signal index 0 carries the **unframed INFO payload**.
- uartPackData signal index 0 carries the **framed AA/BB packet**.

Do not treat these as the same signal merely because their names match.

## 3. Inbound path: serial read to response dispatch

1. The `QSerialPort::readyRead()` signal is connected to the low-level receive handler.
2. `FtescLowLevelFace::uartDataHandleAvailable` (method index 13, native `0x00481030`) checks bytes available, reads the available data through a Qt I/O function pointer, and forwards the resulting QByteArray to the receive handler.
3. The `uartPackDataHandle` slot dispatches to `FUN_0049CA30`.
4. `FUN_0049CA30` appends input bytes to the bounded receive buffer, uses the parser's missing-byte countdown, slides one byte after invalid candidates, consumes full valid frames, and preserves incomplete candidates.
5. Each validated INFO payload is collected and emitted through `FUN_004BDB60`.
6. `FUN_004BDB60` activates `uartPackData` signal index 1: `uartPackDataFromESC(QByteArray&)`.
7. The response-side slot `FtescLowLevelFace::uartPackDataFromESC` (method index 16, native `0x00481930`) forwards the INFO payload to `FUN_004997A0`, the command-byte response dispatcher.
8. `FUN_004997A0` parses the response and emits the corresponding UartComm acknowledgement/data signal. The exact response-to-signal indexes are documented in [V1_7_RESPONSE_DISPATCH_MAP.md](V1_7_RESPONSE_DISPATCH_MAP.md).

The UartComm meta-object also exposes a `uartPackHandle` slot (index 21) that dispatches to the same response parser. The exact secondary connection path for this duplicate entry remains to be resolved; the primary low-level slot path above is directly supported by the method table and function bodies.

## 4. Direct signal-index evidence

Machine code for the two `uartPackData` signal wrappers passes:
- meta-object pointer `0x0051F260`;
- index 0 in `FUN_004BDB20`;
- index 1 in `FUN_004BDB60`.

Machine code for `FUN_004BBC20` passes:
- UartComm meta-object pointer `0x0051F248`;
- signal index 0.

These immediates were read directly from the wrappers and cross-checked against the decoded Qt metadata.

## 5. Remaining uncertainties

- The complete QObject connection-registration routine at `0x00483B90` still needs a clean object-by-object argument map; several legacy string-based connect calls are visible, but their sender/receiver order is not fully annotated.
- The second UartComm `uartPackHandle` entry may serve an alternate transport path or duplicate connection; this is not assumed to be active.
- BLE receive/send callbacks exist in the same application, but this UART path does not prove BLE uses the same outer frame.
- No live serial capture was available. All conclusions are static binary analysis.

## 6. Safety

No serial port was opened and no ESC command was transmitted. The protocol code and test suite are offline-only.
