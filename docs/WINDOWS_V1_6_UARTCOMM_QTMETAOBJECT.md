# Windows V1.6 UartComm QMetaObject and firmware-method map

**Reference date:** 2026-11-22  
**Artifact:** `Flipsky_ESC_Tool_V1.6_20260912.exe`  
**SHA-256:** `051d57a776782ae8daaeaa45179f9b568f7e89b4a78ab8dd8e558ecd3e53b968`  
**Analysis:** REA 6.10.1 / Ghidra 12.2; Rizin 0.9.1 for raw metadata inspection  
**Scope:** static analysis only; application not executed.

## 1. QMetaObject identity and layout

The V1.6 `UartComm` QMetaObject is located at `0x00519248`:

| Field | Address/value |
|---|---|
| QMetaObject | `0x00519248` |
| stringdata pointer | `0x00c1e900` |
| meta_data pointer | `0x00c1e280` |
| static metacall | `FUN_004b5bf0` at `0x004b5bf0` |
| Qt metadata revision | 8 |
| Method count | 50 |
| Signal count | 19 |

The stringdata is a Qt 5 `QByteArrayData` descriptor table (95 entries) followed by its byte-string pool at `0x00c1eef0`. The names below were reconstructed by resolving each method record's string index through its relative descriptor offset, rather than by guessing from the standalone symbol strings.

The dispatcher at `0x004b5bf0` consumes the method indices from this metadata. The first 19 methods (flags 6) are signals; methods from 19 onward are slots or ordinary invokable methods (flags vary by method).

## 2. Complete method index map

### Signals — indices 0–18

| Index | Method | Args |
|---:|---|---:|
| 0 | `sendDataToESC` | 1 |
| 1 | `ftescGetUuidAck` | 1 |
| 2 | `writeEncryptSuccess` | 1 |
| 3 | `ftescFirmwareVerRec` | 1 |
| 4 | `ftescFirmwareEraseRespenseFlag` | 1 |
| 5 | `ftescFirmwareVerRecType` | 1 |
| 6 | `ftescFirmwareWriteBlockSuccessFalg` | 1 |
| 7 | `ftescMotorSignalReadAck` | 2 |
| 8 | `ftescMotorSignalSecretKeyCheckAck` | 1 |
| 9 | `ftescAutoGetRealtimeDataAck` | 0 |
| 10 | `ftescSignalReadAckToRtData` | 2 |
| 11 | `ftescGetRealtimeDataOnce` | 1 |
| 12 | `ftescTermialPrint` | 1 |
| 13 | `ftescSamplesPrint` | 1 |
| 14 | `signalPPMRecAck` | 1 |
| 15 | `signalADCRecAck` | 6 |
| 16 | `motorIdentifyResAck` | 2 |
| 17 | `ftescGetIDResAck` | 2 |
| 18 | `imuCalibrationReceived` | 1 |

### Slots / invokable methods — indices 19–49

| Index | Method | Args | Static handler / implementation |
|---:|---|---:|---|
| 19 | `uartPackHandle` | 1 | `FUN_004948d0` |
| 20 | `ftescObtainFwVerSlot` | 0 | `FUN_00492d00` |
| 21 | `ftescEraseFirmware` | 1 | `FUN_00492e00` |
| 22 | `ftescWriteFirmware` | 1 | `FUN_00492f00` |
| 23 | `ftescJPMBootMode` | 0 | `FUN_004930a0` |
| 24 | `ftescControlDuty` | 1 | `FUN_00493190` |
| 25 | `ftescControlCurrent` | 1 | `FUN_004932a0` |
| 26 | `ftescControlIdCurrent` | 1 | `FUN_004933b0` |
| 27 | `ftescControlSpeed` | 1 | `FUN_004934c0` |
| 28 | `ftescControlPosition` | 1 | `FUN_004935d0` |
| 29 | `ftescControlBrakeCurrent` | 1 | `FUN_004936e0` |
| 30 | `ftescGetAutoRealtimeData` | 2 | `FUN_004946b0` |
| 31 | `ftescObtainUuid` | 0 | `FUN_004937f0` |
| 32 | `writeMcuEncrypt` | 1 | `FUN_004938f0` |
| 33 | `ftescObtainMotorSiganlSetup` | 0 | `FUN_00493a10` |
| 34 | `ftescObtainMotorSetup` | 0 | `FUN_00493b10` |
| 35 | `ftescObtainSiganlSetup` | 0 | `FUN_00493c00` |
| 36 | `resetandRebootMotorSignalSetup` | 1 | `FUN_00493cf0` |
| 37 | `ftescSetMotorSignalSetup` | 0 | `FUN_00493ef0` |
| 38 | `ftescSetMotorSetup` | 0 | `FUN_00494020` |
| 39 | `ftescReboot` | 0 | `FUN_00493e00` |
| 40 | `ftescObtainSignalPPM` | 0 | `FUN_00494130` |
| 41 | `ftescObtainSignalADC` | 0 | `FUN_00494230` |
| 42 | `ftescObtainImuCalibration` | 1 | `FUN_00494330` |
| 43 | `ftescIdentifyMotorOverCan` | 5 | `FUN_00494440` |
| 44 | `ftescObtainIdOverCan` | 0 | `FUN_004945b0` |
| 45 | `uartCommTimerSlot` | 0 | `FUN_004947f0` |
| 46 | `setCanForwardSendFlag` | 2 | `FUN_00492a50` |
| 47 | `setCanForwardSendFlag` | 1 | `FUN_00492a50` |
| 48 | `obtainCanForwardSendFlag` | 0 | `FUN_00492a90` |
| 49 | `obtainCanForwardID` | 0 | `FUN_00492aa0` |

Function-handler addresses are recovered from the switch in `FUN_004b5bf0`. The last four methods correspond to the CAN-forward state accessors and both setter overloads.

## 3. Shared UartComm outbound signal

`FUN_00492ab0` is the common send/log wrapper used by the methods inspected here. The function:

1. Checks the UartComm CAN-forward flag at object offset `+0x0c` and, when enabled, logs the selected ID at `+0x10`.
2. Builds a debug message beginning `Sending to ESC:`.
3. Appends the supplied QByteArray to the debug output.
4. Calls `FUN_004b55f0`.

`FUN_004b55f0` is a short Qt signal activation stub. Its instructions pass QMetaObject address `0x00519248` and method index `0` to the Qt activation helper. Index 0 is the decoded `sendDataToESC(QByteArray&)` signal.

This connects the UartComm methods to the common Qt send signal. The lower V1.6 path already mapped in [WINDOWS_V1_6_UART_FRAME_PARSER.md](WINDOWS_V1_6_UART_FRAME_PARSER.md) then passes this QByteArray through the `FtescLowLevelFace` transport wrapper and outer frame builder as appropriate.

### Qt stream append helpers

- `FUN_00496880` and `FUN_00496890` both sign-extend one input byte and tail-jump to the Qt stream byte-insertion target at `PTR_FUN_00c53300`. They are byte writers; calls such as `FUN_00496880(0x11)` append a real INFO command byte.
- `FUN_004968a0` writes a 16-bit value as high byte followed by low byte (big-endian).
- `FUN_00496ad0` writes a 32-bit value high byte first.
- `FUN_00496c30` multiplies its floating input by its scale argument, then rounds to nearest with half-values away from zero before writing a signed 16-bit big-endian value. The observed command-0x0F caller passes scale 100.
- The command byte is part of the same QByteArray before the common signal; the command/data split below follows the native call order.

## 4. Firmware and CAN-related slot bodies

### Firmware-version request — index 20, `FUN_00492d00`

The method checks a throttle/state field at `this+0x20`. If the cooldown has expired it copies `this+0x1c` into that field, initializes its output stream and appends command byte `0x11` via `FUN_00496880`, then calls `FUN_00492ab0`. The INFO request is therefore `11` with no DATA, not an empty INFO QByteArray.

### Erase firmware — index 21, `FUN_00492e00`

The method initializes an INFO stream, appends command byte `0x16`, then passes its one integer-like argument to `FUN_00496ad0`. That helper appends the four bytes high-byte-first (big-endian). The common sender then emits `16 | ARG32_BE` through `sendDataToESC`.

The exact device-side erase ACK/state-machine and any device-specific preconditions remain open.

### Write firmware — index 22, `FUN_00492f00`

The method initializes an INFO stream, appends command byte `0x18`, then appends the input QByteArray and sends it through `FUN_00492ab0`. Its per-byte XOR expression belongs to the debug-output path: the function reads the source byte array for a log string and passes the original input object to the common sender; no in-place mutation of the payload is visible.

Do not interpret that debug formatting as a firmware payload transform. Do not publish the associated debug-table bytes as a firmware key or protocol constant.

### Boot-mode command — index 23, `FUN_004930a0`

This no-argument method initializes an INFO stream, appends command byte `0x13` and sends it through `FUN_00492ab0`. It is a one-byte INFO command, not an empty INFO payload. The controller-side state transition and ACK handling remain open.

### Obtain UUID — index 31, `FUN_004937f0`

The method checks a throttle field at `this+0x28`; after expiry it copies the interval from `this+0x1c`, appends command byte `0x21`, then sends through the common wrapper. The INFO request is the single byte `21`.

### MCU encryption writer — index 32, `FUN_004938f0`

The method has one argument and a throttle field at `this+0x2c`. It appends command byte `0x22`, then calls a helper pointer with arguments shaped as `(1, 0x10, param_1)`, and sends the resulting QByteArray through `FUN_00492ab0`. The pointer resolves into an opaque/protected area around `0x00855110`; Ghidra does not identify an ordinary function there and Rizin reports no function at the address. The helper's exact byte semantics, key/challenge selection and secret material remain unresolved. No key bytes or protected tables are included in this report.

### Obtain ESC ID over CAN — index 44, `FUN_004945b0`

The method has a throttle counter at `this+0x38`; once expired it sets the counter to `200`, initializes the output stream, appends command byte `0x01`, then sends through `FUN_00492ab0`. The observed request INFO is `01` with no DATA. The unit of the 200 counter and the response mapping are not established here.

### Identify motor over CAN — index 43, `FUN_00494440`

The five-argument method constructs INFO command `0x0F` and appends seven DATA bytes in this exact order:

| Field position | Native source | Wire encoding |
|---:|---|---|
| DATA[0] | second formal argument | one byte |
| DATA[1] | low byte of first formal argument | one byte |
| DATA[2:4] | fourth formal float argument | signed int16, truncated toward zero, big-endian |
| DATA[4:6] | third formal float argument | multiplied by 100, rounded nearest / ties away from zero, signed int16 big-endian |
| DATA[6] | fifth formal argument | one byte |

The five arguments' semantic names and units are not proven by this method body. The offline Python builder `build_identify_motor_over_can_info` uses neutral argument names; it now matches the native distinction between truncation for formal arg4 and scaled half-away rounding for formal arg3. The INFO content is `0F | 7-byte DATA`.

## 5. Related firmware response signals

The meta-object exposes the response/ACK signals required by the firmware state machine:

- `ftescGetUuidAck`
- `writeEncryptSuccess`
- `ftescFirmwareVerRec`
- `ftescFirmwareEraseRespenseFlag`
- `ftescFirmwareVerRecType`
- `ftescFirmwareWriteBlockSuccessFalg`
- `ftescMotorSignalSecretKeyCheckAck`

The signal names establish API surface only; the exact incoming command IDs, byte layouts, timeouts and retry rules must be linked through the response dispatcher before the firmware state machine is considered complete.

## 6. Cross-version and implementation impact

This method table gives exact V1.6 Qt names and dispatcher indexes for a portion of the API previously inferred only from string scans. It allows targeted comparison against V1.7 and narrows the gap between QML/UI actions and the UartComm request API.

No Python firmware command builder was changed from this metadata alone. The V1.6 static UART framing/parser parity work remains valid; the project-wide weighted progress remains 72.6% until a functional milestone (e.g. complete offline command/response path, application integration, firmware recovery logic or hardware validation) is completed.

## 7. Safety and limitations

- Analysis is static; the Windows PE was not run.
- No ESC was connected, and no UART/CAN/BLE command was transmitted.
- No firmware was flashed.
- Cryptographic tables, keys and secret provisioning data are intentionally omitted.
- Decompiled pseudocode is a Ghidra-derived representation, not original source; function classifications and argument types must be cross-checked before implementation.
