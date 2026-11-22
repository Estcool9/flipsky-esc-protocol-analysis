# V1.7 UartComm meta-object and outbound request map

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**UartComm meta-object:** `0x0051F248`  
**String-data:** `0x00F232A0`  
**Meta-data:** `0x00F22B40`  
**Static meta-call:** `0x004BC2B0`  
**Analysis date:** 2026-11-22

This is the main outbound-protocol milestone: the UartComm Qt method table has been decoded and its request methods have been traced to the byte-append helpers. The command bytes below are observed constants in the V1.7 executable, not inferred from UI labels.

## 1. UartComm class recovered

The static meta-object at `0x0051F248` points to:
- string-data table `0x00F232A0`;
- metadata table `0x00F22B40`;
- static meta-call function `0x004BC2B0`.

The revision-8 metadata reports **58 methods**. The string table identifies the class as `UartComm`. The static dispatcher maps methods 21–57 to native functions; methods 0–20 are signal-activation cases.

### Signals (indexes 0–20)

| Index | Signal | Args |
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
| 9 | `ftescTopFlowSetupReadAck` | 2 |
| 10 | `ftescTopFlowSecretKeyCheckAck` | 1 |
| 11 | `ftescAutoGetRealtimeDataAck` | 0 |
| 12 | `ftescSignalReadAckToRtData` | 2 |
| 13 | `ftescGetRealtimeDataOnce` | 1 |
| 14 | `ftescTermialPrint` | 1 |
| 15 | `ftescSamplesPrint` | 1 |
| 16 | `signalPPMRecAck` | 1 |
| 17 | `signalADCRecAck` | 6 |
| 18 | `motorIdentifyResAck` | 2 |
| 19 | `ftescGetIDResAck` | 2 |
| 20 | `imuCalibrationReceived` | 1 |

### Request methods and native dispatch

| Qt index | Method | Native implementation |
|---:|---|---:|
| 21 | `uartPackHandle` | `0x004997A0` |
| 22 | `ftescObtainFwVerSlot` | `0x00495EE0` |
| 23 | `ftescEraseFirmware` | `0x00495FE0` |
| 24 | `ftescWriteFirmware` | `0x004960E0` |
| 25 | `ftescJPMBootMode` | `0x00496280` |
| 26 | `ftescControlDuty` | `0x00496370` |
| 27 | `ftescControlCurrent` | `0x00496480` |
| 28 | `ftescControlIdCurrent` | `0x00496590` |
| 29 | `ftescControlSpeed` | `0x004966A0` |
| 30 | `ftescControlPosition` | `0x004967B0` |
| 31 | `ftescControlBrakeCurrent` | `0x004968C0` |
| 32 | `ftescGetAutoRealtimeData` | `0x004993F0` |
| 33 | `ftescObtainUuid` | `0x004969D0` |
| 34 | `writeMcuEncrypt` | `0x00496AD0` |
| 35 | `ftescObtainMotorSiganlSetup` | `0x00496BF0` |
| 36 | `ftescObtainMotorSetup` | `0x00497110` |
| 37 | `ftescObtainSiganlSetup` | `0x00497200` |
| 38 | `ftescObtainTopFlowSetup` | `0x004972F0` |
| 39 | `ftescObtainTopFlowDefaultSetup` | `0x00497900` |
| 40–41 | `clearTopFlowSetupPending` (overloads) | `0x00495550` |
| 42 | `resetandRebootMotorSignalSetup` | `0x00497E20` |
| 43 | `resetTopFlowSetup` | `0x00497F30` |
| 44 | `ftescSetMotorSignalSetup` | `0x00498540` |
| 45 | `ftescSetTopFlowSetup` | `0x00498960` |
| 46 | `ftescSetMotorSetup` | `0x00498D60` |
| 47 | `ftescReboot` | `0x00498450` |
| 48 | `ftescObtainSignalPPM` | `0x00498E70` |
| 49 | `ftescObtainSignalADC` | `0x00498F70` |
| 50 | `ftescObtainImuCalibration` | `0x00499070` |
| 51 | `ftescIdentifyMotorOverCan` | `0x00499180` |
| 52 | `ftescObtainIdOverCan` | `0x004992F0` |
| 53 | `uartCommTimerSlot` | `0x00499540` |
| 54–55 | `setCanForwardSendFlag` (overloads) | `0x004954D0` |
| 56 | `obtainCanForwardSendFlag` | `0x00495510` |
| 57 | `obtainCanForwardID` | `0x00495520` |

## 2. Confirmed outbound command bytes

The shared byte-append helper is a thunk at `0x0049CE30`; the 32-bit writer is `0x0049CFB0`, which appends the high byte first. The 16-bit writer is `0x0049CE50`. `0x0049D150` multiplies a floating-point input by a scale, rounds it and passes the signed integer to the 32-bit big-endian writer.

| Command byte | UartComm method | Payload observed after command byte | Confidence |
|---:|---|---|---|
| `0x01` | `ftescObtainIdOverCan` | No explicit data field; request has a 200 ms local timeout counter. | High |
| `0x03` | `ftescControlDuty` | One signed 32-bit big-endian value, input × 100,000, rounded. | High |
| `0x04` | `ftescControlCurrent` | One signed 32-bit big-endian value, input × 1,000, rounded. | High |
| `0x06` | `ftescControlBrakeCurrent` | One signed 32-bit big-endian value, input × 1,000, rounded. | High |
| `0x07` | `ftescSetMotorSetup` | Serialized setup data; optional marker `0xD2C6EF10` when the associated setup sub-block is present. | High for command; medium for field semantics |
| `0x09` | `ftescObtainMotorSetup` | No explicit data field. | High |
| `0x0A` | `ftescObtainSiganlSetup` | No explicit data field. | High |
| `0x0D` | `ftescObtainSignalPPM` | No explicit data field. | High |
| `0x0E` | `ftescObtainSignalADC` | No explicit data field. | High |
| `0x0F` | `ftescIdentifyMotorOverCan` | Command followed by byte fields, a 16-bit field, a scaled 16-bit value (input × 100) and a final byte; exact parameter names need type/call-site validation. | High for command; medium for layout |
| `0x11` | `ftescObtainFwVerSlot` | No explicit data field. | High |
| `0x13` | `ftescJPMBootMode` | No explicit data field. | High |
| `0x16` | `ftescEraseFirmware` | Appends the supplied byte-array argument. | High |
| `0x18` | `ftescWriteFirmware` | Appends firmware bytes after a bytewise XOR transform. The transform starts with `0xD0` and advances through a table at `0x00530F61`; table contents are not reproduced here. | High |
| `0x1A` | `ftescGetAutoRealtimeData` | One enable byte followed by a 16-bit big-endian interval/frequency. | High |
| `0x1B` | `ftescSetMotorSignalSetup` | Serialized setup data; optional markers `0xD2C6EF10` and `0x4879187D` introduce present sub-blocks. | High for command; medium for field semantics |
| `0x1C` | `ftescObtainMotorSiganlSetup` | No explicit data field. | High |
| `0x1D` | `resetTopFlowSetup`; `resetandRebootMotorSignalSetup` | No explicit data for the former; one byte for the latter. | High |
| `0x21` | `ftescObtainUuid` | No explicit data field. | High |
| `0x22` | `writeMcuEncrypt` | Forwards a 16-byte argument through an encryption/key-related helper. No key material is included in this report. | High for command and argument length |
| `0x23` | `ftescReboot` | No explicit data field. | High |
| `0x25` | `ftescControlIdCurrent` | One signed 32-bit big-endian value, input × 1,000, rounded. | High |
| `0x26` | `ftescControlPosition` | One signed 32-bit big-endian value, input × 1,000, rounded. | High |
| `0x27` | `ftescControlSpeed` | One signed 32-bit big-endian value, input × 1, rounded. | High |
| `0x29` | `ftescObtainImuCalibration` | One signed 32-bit big-endian value, input × 1,000, rounded. | High |
| `0x3A` | `ftescSetTopFlowSetup` | Serialized setup data; optional marker `0x54464346` introduces a present sub-block. | High for command; medium for field semantics |
| `0x3B` | `ftescObtainTopFlowSetup` | No explicit data field in the initial command path; CAN-forward state is logged/consulted. | High |
| `0x3C` | `ftescObtainTopFlowDefaultSetup` | No explicit data field in the initial command path. | High |

**Important:** these command bytes are not Qt method indexes. They are the actual first byte appended to the INFO payload by the native UartComm request method.

## 3. Control numeric encoding

The six motor-control methods share the same shape:
1. initialize an INFO byte array;
2. append the command byte;
3. scale and round the supplied floating-point input;
4. append a 32-bit big-endian integer;
5. hand the INFO payload to the common send path.

| Control | Command | Scale factor | Encoded field |
|---|---:|---:|---|
| Duty | `0x03` | 100,000 | signed 32-bit BE |
| Current | `0x04` | 1,000 | signed 32-bit BE |
| Brake current | `0x06` | 1,000 | signed 32-bit BE |
| D-axis current | `0x25` | 1,000 | signed 32-bit BE |
| Position | `0x26` | 1,000 | signed 32-bit BE |
| Speed | `0x27` | 1 | signed 32-bit BE |

The scaling factors are encoding details, **not safe control limits or recommended operating values**. No motor was connected and no command was transmitted.

## 4. Firmware update request path

The request methods now provide a clearer static sequence:

- `ftescObtainFwVerSlot`: CMD `0x11`.
- `ftescJPMBootMode`: CMD `0x13`.
- `ftescEraseFirmware`: CMD `0x16` plus a supplied byte array.
- `ftescWriteFirmware`: CMD `0x18` plus a bytewise XOR-transformed firmware block.
- The separate `firmwareUpdatePro` orchestration path calls the TEA buffer wrapper at `0x00481BC0`; the wrapper zero-pads to 8-byte blocks and uses the 32-round TEA block function at `0x00481B30`.

The XOR transform in the CMD 0x18 writer and the TEA buffer wrapper are separate observed layers. Their exact ordering in every firmware-update mode and the full block/acknowledgement state machine still need to be documented. No encryption key material is published.

## 5. Setup payload markers

The setup write methods call `FUN_004A0B00`, which writes a marker and serializes a vector-like sequence of values.

Observed markers:
- motor setup: `0xD2C6EF10`;
- motor-signal setup: `0xD2C6EF10`, `0x4879187D`;
- TopFlow setup: `0x54464346`.

The exact field names, units, optional-block semantics and relationship to the XML parameter catalog remain under analysis. Do not send synthetic setup payloads to hardware.

## 6. Response-side cross-reference

The request map now lines up with the response dispatcher:
- CMD `0x01` → variable-length ESC ID list response.
- CMD `0x0F` → motor-identification response path.
- CMD `0x11` → firmware identity/version response.
- CMD `0x16` → firmware erase response flag.
- CMD `0x18` → firmware block-write acknowledgement.
- CMD `0x1A` → automatic telemetry acknowledgement.
- CMD `0x1B`–`0x1C` → motor-signal setup response family.
- CMD `0x1D` → reset/setup acknowledgement family.
- CMD `0x1E` → ESC ID enumeration response.
- CMD `0x29` → nine-value IMU calibration response.
- CMD `0x3A`–`0x3D` → TopFlow setup response family.

Some mappings are based on matching command/response semantics and the method names; exact acknowledgement callback-to-signal indexes still need confirmation. See [V1_7_RESPONSE_DISPATCH_MAP.md](V1_7_RESPONSE_DISPATCH_MAP.md).

## 7. Still unresolved

- CMD `0x02` one-shot control/telemetry path and the separate `ftescGetRealtimeDataOnce` API.
- Exact payload fields for setup commands `0x07`, `0x1B`, `0x1C`, `0x3A`, `0x3B`, `0x3C`.
- CAN-forward nested payload structure and the full motor-identification request schema.
- IMU calibration request/response units and exact member names.
- Full firmware-update sequencing, block numbering, acknowledgements, retry and bootloader transitions.
- BLE framing and whether it reuses the same INFO payload.
- Runtime validation against passive captures or a safe isolated ESC setup.

No serial/BLE traffic was sent. The project remains static-analysis plus offline tests.


## Response callback correlation update

The matching response acknowledgements are now tied to exact UartComm signal indexes; see [V1_7_RESPONSE_DISPATCH_MAP.md](V1_7_RESPONSE_DISPATCH_MAP.md), section 8. This closes the signal-name ambiguity for the currently mapped response switch cases.


## 8. Typed setup-value serialization

The generic serializer behind the marker blocks is now documented and implemented offline. See [SETUP_VALUE_SERIALIZER.md](SETUP_VALUE_SERIALIZER.md) for the `valType` / `valueTET` / `evalScl` mapping and the native helper chain. The offline script `scripts/ftesc_setup_serializer.py` emits a marker followed by typed values in supplied vector order; it deliberately does not guess missing profile-order rules.


## 8. Native payload schema cross-reference

The resolved payload layouts and offline builders are documented in [V1_7_REQUEST_PAYLOAD_SCHEMAS.md](V1_7_REQUEST_PAYLOAD_SCHEMAS.md).

Additional native method details:
- UartComm meta-object index 32, `ftescGetAutoRealtimeData(uint8,uint16)`, dispatches to `FUN_004993F0` at `0x004993F0`.
- It emits CMD 0x1A, one-byte enable, then 16-bit big-endian interval.
- Motor setup setter `FUN_00498D60` emits CMD 0x07 with marker 0xD2C6EF10 and the first setup vector.
- Motor-signal setup setter `FUN_00498540` emits CMD 0x1B with marker 0xD2C6EF10 and optionally a second marker 0x4879187D when the second vector exists.
- TopFlow setter `FUN_00498960` emits CMD 0x3A with marker 0x54464346.
- TopFlow reset `FUN_00497F30` emits CMD 0x1D with no DATA; motor-signal reset/reboot `FUN_00497E20` emits CMD 0x1D plus one byte.
- IMU calibration `FUN_00499070` emits CMD 0x29 with a signed 32-bit big-endian value scaled by 1,000.
