# V1.7 Qt API string map — candidate command cross-reference

**Binary:** Flipsky_ESC_Tool_V1.7_20261029.exe  
**SHA-256:** dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38  
**Static-analysis area:** Qt string data around VAs 0x00F23A00-0x00F23FA5 and related signature strings in .rdata.

This report records identifiers found in the V1.7 executable's Qt string/meta-object data. Names are useful reverse-engineering anchors, but a string is not proof of a numeric wire opcode. The "candidate V1.6 command" column is a semantic lead only until a caller and payload builder are traced.

## 1. Telemetry, acknowledgement and CAN identifiers

| V1.7 method / slot string | Observed role/name | Candidate V1.6 relationship | Confidence |
|---|---|---|---|
| ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA) | Request-style method; Qt signature strings found with legacy signal/slot prefixes | CMD 0x00 | Strong semantic match; numeric value not yet proven from V1.7 code |
| ftescAutoGetRealtimeDataAck() | Qt slot signature string | CMD 0x1A periodic telemetry acknowledgement | Strong semantic match; numeric value not yet proven |
| ftescGetAutoRealtimeData | Method string in the same facade string block | CMD 0x1A configuration | Strong semantic match |
| ftescGetIDResAck(QVector<int>,bool) | Qt slot signature string | CMD 0x1E master/slave ID enumeration | Strong semantic match; response parser call chain still open |
| ftescMotorSignalReadAck(QString,bool) | Qt slot signature repeated in multiple meta-object regions | Parameter read/response flow, not yet assigned to one V1.6 opcode | Identified API; opcode unknown |
| ftescTopFlowSetupReadAck(QString,bool) | Qt slot signature | Top-flow setup response; exact command not assigned | Identified API; opcode unknown |
| ftescMotorSignalSecretKeyCheckAck(int) | Qt slot signature | Secret-key validation / setup handshake | Identified API; wire semantics unknown |
| ftescSignalReadAckToRtData | Method string | Signal path from parameter-read acknowledgement to real-time data | Identified API; opcode unknown |

The Qt legacy connection signature strings include prefixed forms such as 2ftescAutoGetRealtimeDataAck() and 2ftescGetIDResAck(QVector<int>,bool). In Qt's legacy connection notation, the numeric prefix identifies signal/slot signature form. This places these names in Qt meta-object connection metadata; it does not itself identify the underlying UART byte sequence.

## 2. Control and configuration method names

The string region also contains the following method names:

| V1.7 method string | Candidate public V1.6 operation | What is established |
|---|---|---|
| ftescControlDuty | CMD 0x03 duty control | App-level method name only |
| ftescControlCurrent | CMD 0x04 motor current | App-level method name only |
| ftescControlBrakeCurrent | CMD 0x06 brake current | App-level method name only |
| ftescControlIdCurrent | CMD 0x25 D-axis current | App-level method name only |
| ftescControlPosition | CMD 0x26 position control | App-level method name only |
| ftescControlSpeed | CMD 0x27 electrical RPM | App-level method name only |
| ftescControlMotorSetup | Motor configuration workflow | App-level method name only |
| ftescObtainMotorSetup | Motor setup read flow | App-level method name only |
| ftescObtainMotorSiganlSetup | Motor-signal setup read flow; source spelling contains "Siganl" | App-level method name only |
| ftescSetMotorSignalSetup | Motor-signal setup write flow | App-level method name only |
| ftescObtainSignalSetup | Control-signal setup read flow | App-level method name only |
| ftescObtainTopFlowSetup | Top-flow setup read flow | App-level method name only |
| ftescSetTopFlowSetup | Top-flow setup write flow | App-level method name only |
| resetTopFlowSetup | Top-flow setup reset helper | App-level method name only |
| resetandRebootMotorSignalSetup | Signal configuration reset/reboot helper | App-level method name only |
| ftescReboot | Reboot helper | Could correspond to CMD 0x23 or a broader reconnect/reset workflow; not assigned |

The control-method names align semantically with several public V1.6 command definitions. They do not yet prove whether the application packs those exact opcodes, whether it wraps them in a higher-level command, or whether some are transported through CAN.

## 3. CAN and firmware-related method names

| V1.7 method string | Likely area | Current interpretation |
|---|---|---|
| ftescObtainIdOverCan | CAN enumeration / ID lookup | Candidate relationship to CMD 0x1E or CMD 0x10 forwarding; unresolved |
| ftescIdentifyMotorOverCan | Motor identification over CAN | CAN-mediated operation; underlying command not mapped |
| setCanForwardSendFlag | CAN forwarding state | Internal flag / flow control, not itself an opcode |
| obtainCanForwardSendFlag | CAN forwarding state read | Internal flag / flow control, not itself an opcode |
| ftescObtainFwVerSlot | Firmware-version acknowledgement slot | Candidate CMD 0x11, but call chain not proven |
| ftescEraseFirmware | Firmware erase flow | Firmware-update API; exact wire payload unknown |
| ftescWriteFirmware | Firmware write flow | Firmware-update API; exact block/transport unknown |
| ftescJPMBootMode | Boot-mode handling | Bootloader workflow helper; exact request/response not mapped |
| ftescObtainUuid | UUID acquisition | Identity/key setup context; purpose needs tracing |
| writeMcuEncrypt | MCU encryption-related method name | Strong indication of an encryption-related path, not proof of ordinary UART packet encryption |
| encrypt_res | Encryption result field/name | Context requires caller analysis |

These strings are important leads for the existing firmware-update and TEA workstream. They must not be used to claim that all UART payloads are encrypted. The currently confirmed use of the TEA-related helper remains in firmware-update analysis; ordinary command payload encryption is not established.

## 4. V1.7 string-table regions and observations

- The high-level façade names listed above occur in the V1.7 .rdata string block around VAs 0x00F23A00-0x00F23FA5.
- The UART helper has a separate string group around VA 0x00F24110. It names uartPackData, sendDataToESC, uartPackDataFromESC, uartPackDataHandle and uartPackDataTimerSl.
- The UART helper is therefore distinct from the high-level FtescLowLevelFace façade.
- The V1.7 binary contains Qt legacy signature strings for telemetry request and acknowledgement paths, supporting a Qt-level connection graph.
- No physical ESC interaction was performed.

## 5. Next call-graph targets

1. Identify the native implementations behind ftescGetRealtimeDataOnce and ftescGetAutoRealtimeData.
2. Trace ftescControlDuty, ftescControlCurrent and ftescControlBrakeCurrent into the byte-array/frame builder at 0x0049C5C0.
3. Trace ftescObtainIdOverCan and ftescIdentifyMotorOverCan to the CAN forwarding request and response handlers.
4. Trace ftescObtainFwVerSlot, ftescEraseFirmware, ftescWriteFirmware and ftescJPMBootMode.
5. Find the actual command IDs in the emitted payload buffers before updating the confidence column from "candidate" to "confirmed".
