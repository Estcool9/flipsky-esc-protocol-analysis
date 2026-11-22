# Windows V1.6 UART response dispatcher — command-to-signal map

**Reference date:** 2026-11-22  
**Artifact:** `Flipsky_ESC_Tool_V1.6_20260912.exe`  
**SHA-256:** `051d57a776782ae8daaeaa45179f9b568f7e89b4a78ab8dd8e558ecd3e53b968`  
**Analysis:** REA 6.10.1 / Ghidra 12.2; Rizin 0.9.1 for Qt signal-stub checks  
**Scope:** static analysis only; no application or hardware execution.

## 1. Receive dispatcher entry

The Qt `UartComm` meta-object maps method index 19, `uartPackHandle(QByteArray&)`, to `FUN_004948d0` at `0x004948d0`.

The handler:

1. Receives a validated INFO QByteArray from the UART stream layer.
2. Reads the first INFO byte as command ID using the native byte reader.
3. Routes the command through a switch/jump-table dispatcher when the command value is at most `0x29`.
4. Invokes command-specific parsing and Qt signal wrappers.
5. Resets relevant request-throttle counters for responses which complete outstanding operations.

The response function has a non-contiguous body of approximately 5,093 bytes in the Ghidra FunctionManager view. Ghidra pseudocode identifies these command cases:

`00, 01, 09, 0A, 0D, 0E, 0F, 11, 14, 16, 18, 1A, 1B, 1C, 1E, 21, 22, 24, 29`.

A command not listed here is not proven to be unsupported by the device or by another application path; it simply does not have a recovered branch in this dispatcher view.

## 2. Command-to-Qt-signal mapping

The signal index is resolved against the V1.6 `UartComm` QMetaObject at `0x00519248`. The wrapper functions below were checked by their immediate method-index argument passed to the Qt activation helper.

| INFO CMD | Parser/branch action observed | Qt signal or follow-up | Confidence / remaining question |
|---:|---|---|---|
| `0x00` | Reads a telemetry block: status/byte fields, scaled numeric fields and angular values; builds a structured set of values | `FUN_004b59a0`, index 11 `ftescGetRealtimeDataOnce` | Wrapper link confirmed; exact field-name/unit mapping should be cross-checked against the existing CMD00 schema |
| `0x01` | Parses an ESC-ID/list response and manages the list object | `FUN_004b5b40`, index 17 `ftescGetIDResAck`; also `FUN_004b5630`, index 13 `ftescSamplesPrint` for a text/sample output path | Signal links confirmed; full list element layout and duplicate/termination rules still need documentation |
| `0x09` | Parses a motor-signal-read response path | `FUN_004b5830`, index 7 `ftescMotorSignalReadAck` | Two-argument signal wrapper confirmed; payload schema not yet fully written |
| `0x0A` | Parses another motor/signal-read response path and emits the same ACK signal | `FUN_004b5830`, index 7 `ftescMotorSignalReadAck` | Shared signal is confirmed; semantic distinction from 0x09 remains open |
| `0x0D` | Parses PPM signal response, resets throttle at `this+0x30` | `FUN_004b5a10`, index 14 `signalPPMRecAck` | Wrapper method index 14 confirmed |
| `0x0E` | Parses ADC signal response, resets throttle at `this+0x34`; recovers six values for the signal arguments | `FUN_004b5a60`, index 15 `signalADCRecAck` | Wrapper index 15 directly confirmed in the tail of the function; exact units still need review |
| `0x0F` | Parses motor-identification response and forwards result values | `FUN_004b5950`, index 16 `motorIdentifyResAck` | Wrapper index 16 confirmed; full response payload schema not yet recovered |
| `0x11` | Parses firmware major/minor/type/status fields; resets firmware-version throttle at `this+0x20` | `FUN_004b57e0`, index 5 `ftescFirmwareVerRecType`, then `FUN_004b57a0`, index 3 `ftescFirmwareVerRec` | Both wrappers confirmed; the three version/status fields need a typed schema write-up |
| `0x14` | Extracts a text-like response and routes it to terminal output | `FUN_004b58d0`, index 12 `ftescTermialPrint` | Wrapper index 12 confirmed; encoding/termination details not fully verified |
| `0x16` | Converts response status to a boolean-like value | `FUN_004b5700`, index 4 `ftescFirmwareEraseRespenseFlag` | Wrapper index 4 confirmed; no retry policy inferred |
| `0x18` | Converts response status to a boolean-like value | `FUN_004b5750`, index 6 `ftescFirmwareWriteBlockSuccessFalg` | Wrapper index 6 confirmed; ACK sequence/retry semantics remain open |
| `0x1A` | Auto-realtime status response | `FUN_004b55c0`, index 9 `ftescAutoGetRealtimeDataAck` | No-argument wrapper index 9 confirmed |
| `0x1B` | Parses motor-signal/setup read response, including multiple values | `FUN_004b5830`, index 7 `ftescMotorSignalReadAck` | Shared signal index 7 confirmed; the branch's marker and field semantics need fuller annotation |
| `0x1C` | Checks setup/secret-key acknowledgement path and produces an integer-like result; resets motor-signal related cooldown at `this+0x24` | `FUN_004b5910`, index 8 `ftescMotorSignalSecretKeyCheckAck` | Wrapper index 8 confirmed; do not infer cryptographic algorithm or key material from the ACK handler |
| `0x1E` | Parses a second ESC-ID/list response variant; resets CAN/ID cooldown at `this+0x38` | `FUN_004b5b40`, index 17 `ftescGetIDResAck`; may also print diagnostic sample text through index 13 | Signal link confirmed; exact relation to CMD01 and target-ID correlation remains open |
| `0x21` | Parses UUID bytes; resets UUID throttle at `this+0x28` | `FUN_004b5670`, index 1 `ftescGetUuidAck` | Wrapper index 1 confirmed; exact UUID normalization/validation not asserted here |
| `0x22` | Reads an encryption/write-success status byte; resets encryption throttle at `this+0x2c` | `FUN_004b56b0`, index 2 `writeEncryptSuccess` | Wrapper index 2 confirmed; no key or challenge bytes are exposed |
| `0x24` | Converts a byte sequence to a textual/sample output | `FUN_004b5630`, index 13 `ftescSamplesPrint` | Wrapper index 13 directly confirmed; this is a sample/diagnostic output, not proven control telemetry |
| `0x29` | Parses a set of IMU calibration numeric values | `FUN_004b5b90`, index 18 `imuCalibrationReceived` | Wrapper index 18 confirmed; full units/ranges/field names not yet documented |

## 3. Wrapper verification

Rizin inspection of the short signal wrappers confirms the method-index immediates loaded before the common Qt activation helper:

| Wrapper | Meta-object index | QMetaObject name |
|---|---:|---|
| `FUN_004b59a0` | 11 | `ftescGetRealtimeDataOnce` |
| `FUN_004b5b40` | 17 | `ftescGetIDResAck` |
| `FUN_004b5830` | 7 | `ftescMotorSignalReadAck` |
| `FUN_004b5a10` | 14 | `signalPPMRecAck` |
| `FUN_004b5a60` | 15 | `signalADCRecAck` |
| `FUN_004b5950` | 16 | `motorIdentifyResAck` |
| `FUN_004b57e0` | 5 | `ftescFirmwareVerRecType` |
| `FUN_004b57a0` | 3 | `ftescFirmwareVerRec` |
| `FUN_004b58d0` | 12 | `ftescTermialPrint` |
| `FUN_004b5700` | 4 | `ftescFirmwareEraseRespenseFlag` |
| `FUN_004b5750` | 6 | `ftescFirmwareWriteBlockSuccessFalg` |
| `FUN_004b55c0` | 9 | `ftescAutoGetRealtimeDataAck` |
| `FUN_004b5910` | 8 | `ftescMotorSignalSecretKeyCheckAck` |
| `FUN_004b5670` | 1 | `ftescGetUuidAck` |
| `FUN_004b56b0` | 2 | `writeEncryptSuccess` |
| `FUN_004b5630` | 13 | `ftescSamplesPrint` |
| `FUN_004b5b90` | 18 | `imuCalibrationReceived` |

All wrapper methods use the same `UartComm` static meta-object address `0x00519248`; the index is the key to the exact signal name in the fully reconstructed metadata table.

## 4. Cooldown bookkeeping observed in the response handler

The response handler clears these request throttle fields:

| Response CMD | Object offset reset |
|---:|---:|
| `0x11` firmware version | `this+0x20` |
| `0x21` UUID | `this+0x28` |
| `0x22` encryption/write key helper | `this+0x2c` |
| `0x0D` PPM | `this+0x30` |
| `0x0E` ADC | `this+0x34` |
| `0x01`, `0x1E` ID/CAN discovery | `this+0x38` |

The timer slot `FUN_004947f0` decrements positive fields at offsets `+0x20` through `+0x38` on each timer tick. Therefore the request-side cooldown value `200` for CMD01 is a tick count, not a confirmed number of milliseconds; the actual QTimer interval remains unverified.

## 5. Offline implementation status

The response dispatcher now provides a command-to-signal map, but this is not yet sufficient to implement every response codec safely.

Already represented elsewhere in the repository:
- CMD00 realtime telemetry decode work.
- CMD11 firmware version decoder.
- Firmware ACK signal surface and partial firmware-flow analysis.
- CMD0F motor-identification request builder, with the native signed-conversion rules corrected and tests passing.

Still requiring full field-level reconstruction before implementation:
- CMD01 / CMD1E ESC ID list formats and target correlation.
- CMD09 / CMD0A / CMD1B shared motor-signal response layouts and distinctions.
- CMD0D PPM and CMD0E ADC six-field response schemas.
- CMD0F identify response payload.
- CMD14 / CMD24 text/sample output encoding and lengths.
- CMD16 / CMD18 exact success/failure status semantics and retry/timeout behavior.
- CMD1C secret-key/setup ACK meaning (no secrets).
- CMD21 UUID byte order/format.
- CMD29 IMU calibration units, ranges and conversion rules.

Do not implement a field schema from method names alone. Keep undecoded response branches as raw/unknown values until all byte readers, lengths, marker checks and signal argument positions are documented.

## 6. Safety and limitations

- Static PE analysis only; the Windows application was not executed.
- No physical ESC was connected and no UART/CAN/BLE command was sent.
- No firmware was flashed.
- Cryptographic key material, protected lookup tables and secret provisioning values are intentionally excluded.
- Ghidra decompiler output is derived pseudocode, not the original source code.
