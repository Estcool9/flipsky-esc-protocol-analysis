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

`FUN_00492ab0` is the common send/log wrapper used by the firmware methods inspected here. The function:

1. Checks the UartComm CAN-forward flag at object offset `+0x0c` and, when enabled, logs the selected ID at `+0x10`.
2. Builds a debug message beginning `Sending to ESC:`.
3. Appends the supplied QByteArray to the debug output.
4. Calls `FUN_004b55f0`.

`FUN_004b55f0` is a short Qt signal activation stub. Its instructions pass QMetaObject address `0x00519248` and method index `0` to the Qt activation helper. Index 0 is the decoded `sendDataToESC(QByteArray&)` signal.

This connects the UartComm firmware methods to the common Qt send signal. The lower V1.6 path already mapped in [WINDOWS_V1_6_UART_FRAME_PARSER.md](WINDOWS_V1_6_UART_FRAME_PARSER.md) then passes this QByteArray through the `FtescLowLevelFace` transport wrapper and outer frame builder as appropriate.

## 4. Firmware-related slot bodies

### Firmware-version request — index 20, `FUN_00492d00`

The method checks a throttle/state field at `this+0x20`. If the cooldown is not active it copies `this+0x1c` into that field and invokes the common send wrapper with an empty QByteArray. It therefore acts as a rate-limited no-argument send request. The method's meta-object name is `ftescObtainFwVerSlot`.

### Erase firmware — index 21, `FUN_00492e00`

The method takes one integer-like argument and calls `FUN_00496ad0`. That helper appends the four bytes of the value in high-byte-first order to a QByteArray. The resulting four-byte payload is passed to `FUN_00492ab0`, which emits the common `sendDataToESC` signal.

This establishes the local payload construction and outbound Qt signal, but does not alone identify the numeric firmware command byte or the device-side erase ACK state machine.

### Write firmware — index 22, `FUN_00492f00`

The method takes a QByteArray-like argument, writes a debug representation of its bytes, and then passes the original input object to `FUN_00492ab0`. The per-byte XOR expression visible in this function belongs to the debug-output path: the function reads the source byte array and sends the original QByteArray pointer; no in-place mutation of the input buffer is visible in the decompiled body.

Do not interpret that debug formatting as a firmware payload transform. Do not publish the associated debug-table bytes as a firmware key or protocol constant.

### Boot-mode command — index 23, `FUN_004930a0`

This no-argument method creates an empty QByteArray and sends it through `FUN_00492ab0`, which activates `sendDataToESC`. The method name is `ftescJPMBootMode`; the exact command byte and controller-side state transition require tracing the downstream consumer/ACK.

### MCU encryption writer — index 32, `FUN_004938f0`

This method has one argument and a throttle field at `this+0x2c). Its body invokes an unresolved Qt/helper function with arguments shaped as `(1, 0x10, param_1)`, then passes the resulting QByteArray-like object to `FUN_00492ab0`. The helper target and exact byte semantics are not yet established here. No key bytes or secret material are included in this report.

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
