# V1.7 UART response command dispatch map

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Dispatcher:** `0x004997A0`  
**Analysis date:** 2026-11-22  
**Provider:** Ghidra 12.2 through REA

This report maps the byte returned by `FUN_0049D370` to the switch cases in the V1.7 receive-response dispatcher. The command byte is part of the INFO field. This is a response-side map; it is not yet a complete outbound-request map.

## 1. Confirmed command-to-response relationships

| Command byte | Observed V1.7 response handling | Confidence / correlation |
|---:|---|---|
| `0x00` | Parses MCU ID, error, voltage, currents, eRPM, duty, temperatures, CPU load, encoder angle, three additional scaled angular values and PAS RPM; calls telemetry callback `0x004BC060`, which emits UartComm signal index 13 `ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA)`. | **High.** Field order and lengths match V1.6's extended automatic telemetry response (45-byte INFO/DLEN, 44 DATA bytes). Extra angular-field semantics are not documented by the V1.6 PDF. |
| `0x01` | Enters a large variable-length response path; iterates over payload bytes and calls callback/dispatch helper `0x004BC200`. | Unknown. Do not equate this with V1.6 CMD 0x02. |
| `0x0D` | Reads one signed 32-bit value scaled by 1,000,000; calls `0x004BC0D0`. | PPM response; offline decoder added. |
| `0x0E` | Reads six signed 32-bit values with scales 1,000,000; 1,000,000; 1; 1; 1; 1,000,000; calls `0x004BC120`. | Six-value ADC response; semantic channel labels remain unknown. |
| `0x0F` | Handles a variable-length byte/string-like payload; calls `0x004BC010`. | Unknown response schema. |
| `0x11` | Parses firmware-version-related bytes and a variable-length text/identity field; invokes `0x004BBE10` and `0x004BBDD0`. | **High semantic correlation** with V1.6 `UART_OBTAIN_FIRMWARE_VERSION`; exact V1.7 field interpretation still needs full type mapping. |
| `0x14` | Parses a string-like payload and calls `0x004BBF50`. | Unknown. |
| `0x16` | Reads one byte as boolean and calls `0x004BBD30`. | Firmware erase acknowledgement; offline decoder added. |
| `0x18` | Reads one byte as boolean and calls `0x004BBD80`. | Firmware write-block acknowledgement; offline decoder added. |
| `0x1A` | Calls no-argument callback wrapper `0x004BBBF0`. | Auto-realtime acknowledgement with no DATA; offline decoder added. |
| `0x1B` | Calls callback wrapper `0x004BBE60` with a byte value. | Setup/acknowledgement path; exact schema unknown. |
| `0x1C` | Reads setup-related values using helper `0x0049DDB0`, performs additional checks and calls `0x004BBF90` in one branch. | Setup response path; exact schema unknown. |
| `0x1D` | Calls callback wrapper `0x004BBEB0` with a byte value. | Possible reset/reboot/setup acknowledgement family; not assigned to the public V1.6 command without call-site proof. |
| `0x1E` | Iterates over remaining payload bytes into a vector-like container and calls `0x004BC200`. | **High.** Matches V1.6 `UART_OBTAIN_ALL_FTESC_ID`: master ID followed by slave IDs. |
| `0x21` | Calls parser helper `0x0049CE00`, then callback wrapper `0x004BBCA0`. | Unknown. |
| `0x22` | Reads one byte as boolean and calls `0x004BBCE0`. | Firmware authorization acknowledgement; offline decoder added. |
| `0x24` | Calls callback wrapper `0x004BBC60` with a vector/container-like argument. | Unknown. |
| `0x29` | Reads nine signed 32-bit values, each scaled by 1,000,000; calls `0x004BC250`. | IMU calibration response; offline decoder added, semantic labels remain unknown. |
| `0x3A` | Calls callback wrapper `0x004BBEB0` with a byte value. | Setup-frame family; exact schema unknown. |
| `0x3B`, `0x3C` | Share a setup-frame parsing path. The handler checks a marker `0x54464346` in one branch. | Vendor-specific setup-frame path; meaning of marker and payload unresolved. |
| `0x3D` | Calls callback wrapper `0x004BBEB0` with a byte value. | Setup-frame family; exact schema unknown. |

The initial receive function also emits a diagnostic string `"RX setup frame command:"` for command bytes `0x1B`, `0x1C`, and `0x3A`–`0x3D`. This is direct evidence that these cases are treated as setup-related responses in the application.

## 2. Command 0x00: V1.6 extended telemetry layout found in V1.7

The case at `0x004997A0` reads the following values after the command byte. Integer readers `0x0049D540` and `0x0049D510` are the previously mapped big-endian 16-bit and 32-bit readers.

Offsets below are relative to the DATA portion after the command byte, consistent with the V1.6 PDF.

| DATA offset | Size | Observed scaling / conversion | V1.6 field correlation |
|---:|---:|---|---|
| 0 | 1 | Raw byte | MCU/controller ID |
| 1 | 1 | Raw signed/byte value | Error code |
| 2 | 2 | ÷ 100 | Battery voltage |
| 4 | 4 | ÷ 1,000,000 | Battery current |
| 8 | 4 | ÷ 1,000,000 | Motor current |
| 12 | 4 | ÷ 1 | Motor electrical RPM |
| 16 | 2 | ÷ 10,000 | Duty |
| 18 | 2 | ÷ 100 | MOSFET temperature |
| 20 | 2 | ÷ 100 | Motor temperature |
| 22 | 2 | ÷ 10,000 | CPU utilization |
| 24 | 4 | ÷ 1,000,000 | Encoder angle |
| 28 | 4 | ÷ 1,000,000, then radians-to-degrees | Additional angular value 1; V1.6 calls these bytes reserved |
| 32 | 4 | ÷ 1,000,000, then radians-to-degrees | Additional angular value 2; V1.6 calls these bytes reserved |
| 36 | 4 | ÷ 1,000,000, then radians-to-degrees | Additional angular value 3; V1.6 calls these bytes reserved |
| 40 | 4 | Raw 32-bit value | PAS RPM |

Total DATA length: **44 bytes**. INFO length including command byte: **45 bytes (0x2D)**.

This is an important cross-check: the V1.7 parser reads the three 32-bit fields occupying the 12 bytes that the public V1.6 PDF labels reserved, and then reads PAS RPM. It converts those three fields to degrees, so they are not simply discarded by V1.7. Their exact names/meanings are still unknown and should not be guessed.

## 3. Command 0x11: firmware-version response

The V1.7 case:
- reads the first two firmware-version bytes;
- reads a mode/status byte;
- calls a variable-length reader at `0x0049D5E0`;
- reads another status byte;
- passes the parsed values to callback wrappers `0x004BBE10` and `0x004BBDD0`.

The V1.6 protocol describes CMD 0x11 as firmware/hardware identity, including major/minor version, bootloader/application mode marker, hardware name and serial number. This is a strong semantic match. More work is needed to map each V1.7 local variable to the exact public field and determine whether the V1.7 parser consumes the serial number in this function or in a subsequent callback.

## 4. Command 0x1E: ESC ID enumeration

The V1.7 case iterates over the remaining DATA bytes, appending each byte to a vector-like Qt container, then calls `0x004BC200`. This is consistent with the V1.6 response layout:
- first byte: master MCU/ESC ID;
- remaining bytes: slave MCU/ESC IDs.

The exact callback signal signature should be confirmed against the relevant meta-object before naming the emitted Qt signal.

## 5. Parser helper widths and scaling

The receive path uses:
- `FUN_0049D370`: one-byte field reader (also used for the command byte);
- `FUN_0049D330`: one-byte field reader with signed/character interpretation in the decompiler;
- `FUN_0049D540`: big-endian 16-bit numeric reader;
- `FUN_0049D510`: big-endian 32-bit numeric reader;
- `FUN_0049D5E0`: variable-length/text-like reader;
- `FUN_0049DDB0`: setup-related numeric reader, not yet fully classified.

The first four reader roles are corroborated by the telemetry case and previously mapped big-endian helpers. The exact return types and signedness of every reader should still be validated against its full implementation and caller.

## 6. What is not proven

- This is a response dispatcher, not the complete request encoder.
- The Qt callback wrappers do not by themselves reveal the public signal names.
- Command bytes 0x0D, 0x0E, 0x0F, 0x14, 0x16, 0x18, 0x1B, 0x1C, 0x1D, 0x21, 0x22, 0x24, 0x29 and 0x3A–0x3D are not assigned to named V1.6 commands here.
- The V1.6 PDF's 12 reserved telemetry bytes are interpreted as three angular values by the V1.7 app, but their semantic labels are unknown.
- No actual ESC response capture was available for runtime validation.

## 7. Next steps

1. Map the callback wrappers to their receiving Qt signals/slots and exact meta-object indexes.
2. Trace the outbound methods for CMD 0x00, 0x11, 0x1A and 0x1E to confirm request construction.
3. Investigate the setup-frame family 0x1B/0x1C/0x3A–0x3D and marker 0x54464346.
4. Trace CAN forwarding and the CMD 0x10 path.
5. Extend the offline protocol model with the V1.7 telemetry extension only after assigning stable names to the additional angular fields.


## 8. Exact Qt acknowledgement signal mapping

The callback wrappers called by the response switch were inspected at machine-code level. Each wrapper passes the UartComm meta-object pointer `0x0051F248` and a literal signal index to Qt's activation helper. This resolves the response-to-signal map without relying only on method-name guesses.

| Response command | Callback wrapper(s) | Qt signal index | Exact UartComm signal |
|---:|---|---:|---|
| `0x00` | `0x004BC060` | 13 | `ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA)` |
| `0x01`, `0x1E` | `0x004BC200` | 19 | `ftescGetIDResAck(QVector<int>, bool)` |
| `0x0D` | `0x004BC0D0` | 16 | `signalPPMRecAck(...)` |
| `0x0E` | `0x004BC120` | 17 | `signalADCRecAck(...)` |
| `0x0F` | `0x004BC010` | 18 | `motorIdentifyResAck(...)` |
| `0x11` | `0x004BBDD0` | 3 | `ftescFirmwareVerRec(...)` |
| `0x11` | `0x004BBE10` | 5 | `ftescFirmwareVerRecType(...)` |
| `0x14` | `0x004BBF50` | 14 | `ftescTermialPrint(...)` |
| `0x16` | `0x004BBD30` | 4 | `ftescFirmwareEraseRespenseFlag(...)` |
| `0x18` | `0x004BBD80` | 6 | `ftescFirmwareWriteBlockSuccessFalg(...)` |
| `0x1A` | `0x004BBBF0` | 11 | `ftescAutoGetRealtimeDataAck()` |
| `0x1B` | `0x004BBE60` | 7 | `ftescMotorSignalReadAck(QString, bool)` |
| `0x1C` | `0x004BBF90` | 8 | `ftescMotorSignalSecretKeyCheckAck(int)` |
| `0x1D`, `0x3A`, `0x3D` | `0x004BBEB0` | 9 | `ftescTopFlowSetupReadAck(QString, bool)` |
| `0x21` | `0x004BBCA0` | 1 | `ftescGetUuidAck(...)` |
| `0x22` | `0x004BBCE0` | 2 | `writeEncryptSuccess(...)` |
| `0x24` | `0x004BBC60` | 15 | `ftescSamplesPrint(...)` |
| `0x29` | `0x004BC250` | 20 | `imuCalibrationReceived(FTESC_IMU_CALIBRATION)` |
| `0x3B`, `0x3C` | `0x004BBFD0` | 10 | `ftescTopFlowSecretKeyCheckAck(int)` |

Signal indexes were read from the wrapper's immediate arguments and cross-checked against the decoded 58-method UartComm meta-object table. This is direct evidence for the callback signal identity.

Signal index 12, `ftescSignalReadAckToRtData(QString, bool)`, is not emitted by the response cases above; it is connected through a separate application-level path and remains a target for follow-up tracing.


## 8. Independent V1.4 implementation cross-check

A third-party Python/Arduino FTESC UART V1.4 implementation was inspected at pinned commit `49989ac0cde531a68799284d1de9efdd7ba14c7f`. Its common short-frame format and CRC agree with V1.7. Exact example `AA 01 11 4C 7F DD` is reproduced by the offline codec. The third-party driver's base telemetry field order/scales align with the V1.7 CMD 0x00 base layout.

The V1.7 response handler additionally interprets the 12 bytes labelled reserved in V1.6 as three signed micro-radian angular values and reads PAS RPM at DATA offset 40. The parser and tests now cover all four extension values. See [EXTERNAL_IMPLEMENTATION_CROSSCHECK.md](EXTERNAL_IMPLEMENTATION_CROSSCHECK.md).

The third-party implementation's FT85BD hardware compatibility claims remain attributed to its author; no hardware was tested in this project.


## 9. Offline response decoders added

`scripts/ftesc_responses.py` now decodes the response layouts that are fully established:
- CMD 0x0D: one signed int32 scaled by 1,000,000 (PPM response);
- CMD 0x0E: six signed int32 values with scales [1e6, 1e6, 1, 1, 1, 1e6];
- CMD 0x16, 0x18 and 0x22: one-byte boolean acknowledgements;
- CMD 0x1A: no-DATA acknowledgement;
- CMD 0x29: nine signed int32 values, each scaled by 1,000,000.

The six CMD 0x0E values and nine CMD 0x29 calibration values retain generic names until the UI/API semantics are mapped. See the tests in `tests/test_ftesc_responses.py`.


CMD 0x21 raw UUID DATA is decoded by `parse_uuid_response()` in `scripts/ftesc_responses.py`. The decoder preserves the raw length; the firmware preflight expects a 16-byte TEA key but the response dispatcher itself does not visibly validate that length.
