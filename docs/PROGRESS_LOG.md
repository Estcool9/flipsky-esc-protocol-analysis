# Progress log

## 2026-11-22 — Project baseline

- Identified the Windows executable as PE32 x86, native, with no CLR/.NET header.
- Verified its SHA-256: `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`.
- Observed unusual `.enigma1` and `.enigma2` sections; a protected/packed build is plausible, but the exact protector is not confirmed.
- Recovered and validated 13 Zlib-compressed XML resources.
- Built a reproducible catalog with 736 profile rows, 222 unique parameter IDs and 13 profile/resource variants.
- Identified Qt 5, C++, QML, QtSerialPort and QtBluetooth components.
- Mapped the first UART signal/slot connections in the FtescLowLevelFace initialization path.
- Published the project reports, analysis scripts, catalogs and all 13 extracted XML resources to GitHub. Larger text files are stored as gzip/base64 payloads; [the restoration guide](PAYLOAD_FORMAT.md) explains how to reconstruct them.

## 2026-11-22 — FtescLowLevelFace class and meta-object

- Reopened the same PE in REA/Ghidra 12.2 and verified the same SHA-256. Targeted Ghidra calls timed out; static work continued with REA's integrated Rizin 0.9.1.
- Confirmed that routine VA `0x00483910` initializes an object whose vtable and Qt meta-cast path identify the class as `FtescLowLevelFace`. This is a high-level façade constructor/initialization path, not the UART parser.
- Located its static meta-object at `0x0051f218`, string-data table at `0x00f215c0`, meta-data at `0x00f20d60`, and static meta-call function at `0x004b98d0`.
- The meta-object string table contains UART and BLE methods, including `uartDataHandleAvailable`, `uartPackDataFromESC`, `uartCommSendToFtesc`, `lowLevelSendDataToFtesc`, and a method named `tea_encrypt`.
- **Caution:** `tea_encrypt` is confirmed as a meta-object string. Its actual method body and callers have not yet been resolved, so we cannot state that it encrypts UART frames.
- Confirmed `QSerialPort::readyRead()` → `uartDataHandleAvailable()`, UART byte-array forwarding connections, firmware-version/configuration acknowledgement callbacks and BLE callbacks in the façade constructor.
- Added [the detailed Qt meta-object report](QT_METAOBJECT.md) and [artifact inventory with SHA-256 hashes](ARTIFACT_INVENTORY.md).

### Current estimate

- **Overall project progress: 33%** (milestone estimate).
- Qt/QML architecture and class ownership: 90%.
- UART/Qt event and meta-object mapping: 75%.
- UART implementation analysis: 32%.
- Frame format/opcodes/checksum: 5%.
- Independent parser/client and hardware validation: 0%.

## Next actions

1. Resolve the FtescLowLevelFace meta-object dispatch IDs and method bodies.
2. Trace `uartDataHandleAvailable` to the byte-buffer accumulation and dispatch logic.
3. Trace `uartPackDataFromESC`, `sendDataToESC`, `lowLevelSendDataToFtesc` and `uartCommSendToFtesc`.
4. Determine frame boundaries, lengths, opcodes, payload types and checksum.
5. Verify whether `tea_encrypt` is called from a communication path.
6. Compare confirmed protocol details with VESC Tool only after the Flipsky implementation is understood.
7. Build offline parser tests before any physical ESC interaction.


## 2026-11-22 — Outer frame, CRC and offline tests

- Traced receive flow from \`uartDataHandleAvailable\` at \`0x00481030\` into \`uartPackDataHandle\` at \`0x0049CA30\`, then to outer parser \`0x0049C830\` (call site \`0x0049CC8D\`).
- Recovered short frame \`AA + LEN8 + PAYLOAD + CRC16_BE + DD\` and extended frame \`BB + LEN16_BE + PAYLOAD + CRC16_BE + DD\`.
- Confirmed sender selects AA for lengths 1–255 and BB above 255; receiver rejects empty short payloads and extended lengths <=254.
- Compared both 256-byte lookup tables with generated split CRC-16/MODBUS tables. Parameters: reflected polynomial A001, init FFFF, xorout 0000; CRC covers payload only and is serialized big-endian. Check vector 123456789 → 4B37.
- Confirmed default maximum-payload field 0x2710 (10,000) at \`0x0049C460\`.
- Caller at \`0x0049CA30\` recognises parser result -2 (incomplete), -1 (invalid) and positive consumed length. On -1 it advances one byte; on success it advances by the frame length and repeats.
- Added \`scripts/ftesc_frame.py\`, \`tests/test_ftesc_frame.py\`, [WIRE_FRAME_FORMAT.md](WIRE_FRAME_FORMAT.md), [RECEIVE_BUFFER_STATE.md](RECEIVE_BUFFER_STATE.md) and updated [ANALYSIS_CHECKPOINT.md](ANALYSIS_CHECKPOINT.md).
- Ran the repository's Python unit tests on REA: **13 passed, 0 failed**.

### Current estimate
- **Overall progress: 40%**.
- Outer frame and CRC: 100%.
- Receive-buffer/resynchronization: 70%.
- Offline frame codec/tests: 100%.
- Inner command IDs and payload layouts: 8%.
- Hardware validation: 0%.

## Next work
1. Map inner command IDs to named acknowledgement handlers without confusing generic Qt/QVariant type dispatch with ESC command IDs.
2. Trace outgoing \`ftescObtain*\` builders through payload construction into the outer frame builder.
3. Inspect exact incomplete-frame carryover across separate readyRead callbacks and all buffer reset conditions.
4. Continue TEA call-site analysis; ordinary UART encryption remains unproven.


## 2026-11-22 — V1.6 official protocol and C reference added

- Read the official V1.6 English UART protocol PDF (23 pages, issue date 2025-12-09), its Chinese counterpart, the V1.4 English UART protocol PDF and the V1.6 90-page user manual from Nextcloud.
- Preserved the 12,314-byte ECU-side sample C source in reference/ftesc_v1.4_1.5_1.6_uart_handle.c. It is a sample ECU implementation, not Flipsky ESC Tool application source or ESC firmware source.
- Added docs/FTESC_UART_PROTOCOL_V1.6.md with command IDs, frame format, CRC, integer endianness, telemetry layouts, CAN forwarding, keepalive and periodic telemetry.
- Added docs/V1_4_TO_V1_6_PROTOCOL_CHANGES.md. Confirmed that CMD 02 moves the current-request field from D0-D1 to D2-D3, CMD 00 gains an automatic telemetry extension, and V1.6 adds the PAS-mode alias for CMD 02.
- Added docs/V1_7_BINARY_CROSS_REFERENCE.md. Private V1.7 framing/CRC and endian helpers agree with the public V1.6 protocol; numeric command-to-Qt-handler mapping remains open.
- Added docs/V1.6_MANUAL_NOTES.md and docs/NEXTCLOUD_SOURCE_INVENTORY.md.
- Added scripts/ftesc_protocol.py and tests/test_ftesc_protocol.py. Combined REA test result: **26 passed, 0 failed**.
- Overall project estimate updated to **46%**.

### Remaining high-value tasks

1. Trace V1.7 GUI/facade request builders to the outer frame builder.
2. Recover numeric command-to-acknowledgement dispatch in V1.7.
3. Confirm the V1.7 CMD 02 data offsets against the V1.4/V1.6 change.
4. Stage a V1.6 Windows executable on REA and perform a binary-to-binary comparison.
5. Inspect BLE transport separately from UART.


## 2026-11-22 — V1.7 Qt API string map

- Inspected the V1.7 .rdata Qt string/meta-object region around VAs 0x00F23A00-0x00F23FA5.
- Identified high-level methods including ftescControlDuty, ftescControlCurrent, ftescControlBrakeCurrent, ftescControlIdCurrent, ftescControlSpeed, ftescControlPosition, ftescGetAutoRealtimeData, ftescObtainIdOverCan, ftescIdentifyMotorOverCan, ftescObtainFwVerSlot, ftescEraseFirmware, ftescWriteFirmware, ftescJPMBootMode, ftescObtainUuid and writeMcuEncrypt.
- Confirmed that the high-level façade string group and the separate uartPackData meta-object string group are distinct.
- Added docs/V1_7_QT_API_STRING_MAP.md with explicit confidence labels: names are evidence of API surface, but numeric opcodes are not proven until call paths and emitted bytes are traced.
- Updated V1.7 command-ID/payload cross-reference workstream to 20%.
- Re-evaluated overall progress to **48%**.


## 2026-11-22 — V1.7 receive-path deep dive and streaming decoder

- Reopened the V1.7 executable in REA/Ghidra 12.2; SHA-256 again matched `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`.
- Decompiled `0x0049C830` (single-frame parser), `0x0049CA30` (receive stream handler), `0x0049C5C0` (frame builder) and `0x0049C7A0` (CRC helper).
- Confirmed the parser's tri-state result: positive consumed frame size, -1 invalid candidate, -2 incomplete candidate plus a missing-byte count.
- Mapped receive-state fields by observed use: parse cursor at +0x14, used length at +0x18, incomplete-byte countdown at +0x1C, maximum payload at +0x20, capacity/allocation bound at +0x24 and buffer pointer at +0x28. These are descriptive labels, not recovered C++ member names.
- New finding: the handler appends serial bytes incrementally and uses the parser's missing-byte count as a countdown, avoiding a full parser call on every byte of a long incomplete frame.
- Confirmed one-byte resynchronization after an invalid candidate, full-frame consumption after a valid candidate, repeated parsing of concatenated frames, and compaction of the unconsumed suffix when space is needed.
- Added [RECEIVE_PATH_DEEP_DIVE.md](RECEIVE_PATH_DEEP_DIVE.md) with pseudocode and explicit caveats.
- Added `scripts/ftesc_stream.py` and `tests/test_ftesc_stream.py`. The stream decoder handles split frames, concatenated frames, leading noise, bad CRC/terminator recovery and reset.
- A first test run exposed a Python `BufferError`: the frame decoder held a memoryview of the mutable bytearray while the recovery path resized it. The implementation was corrected to pass an immutable bytes snapshot into the existing frame decoder.
- Re-cloned the public GitHub repository on REA and ran the exact published tree: **36 tests passed, 0 failed** (26 frame/protocol tests plus 10 stream tests).
- Overall project estimate updated from **48% to 50%**. Receive-buffer/resynchronization analysis rises to 90%; V1.7 command-ID mapping remains the main unresolved static-analysis milestone.
- No ESC hardware was connected; no serial or BLE data was transmitted.

### Next work
1. Map the FtescLowLevelFace Qt meta-object dispatch indexes to method names and native bodies.
2. Trace `ftescControlDuty`, `ftescControlCurrent`, `ftescGetRealtimeDataOnce` and the `ftescObtain*` methods into their actual payload bytes.
3. Correlate response command IDs with acknowledgement handlers.
4. Continue CAN-forwarding and firmware-update call graphs.
5. Compare V1.6 Windows executable(s) against V1.7 once staged locally.


## 2026-11-22 — Qt meta-call dispatch and first V1.7 response command map

- Decoded the Qt 5 revision-8 meta-object data at `0x00F20D60`: 64 method entries, method-table offset 14 words; decoded each string index from the `QByteArrayData` table at `0x00F215C0`.
- Decompiled static meta-call dispatcher `0x004B98D0` and mapped all 64 indexes to names and native dispatch targets. The first 12 are signal activation cases; slots 12–24 include serial receive, timer, UART send/receive, firmware-version callback, TEA methods and BLE receive/disconnect.
- Added [QT_METACALL_DISPATCH_MAP.md](QT_METACALL_DISPATCH_MAP.md).
- Resolved the TEA methods: index 19 `tea_encrypt` → `0x00481B30`, a 32-round TEA block transform; index 20 `encrypt` → `0x00481BC0`, zero-padding to an 8-byte boundary and encrypting each block.
- Confirmed that `firmwareUpdatePro` at `0x00486570` calls the buffer encryption wrapper at `0x00486C1F`. This proves TEA is used by the firmware-update path, not that ordinary UART telemetry/control packets are encrypted. No key material was copied to GitHub.
- Decompiled response dispatcher `0x004997A0`; it reads the command byte through `0x0049D370` and switches across the observed response command cases.
- Mapped `0x00` telemetry, `0x11` firmware identity, `0x1A` periodic telemetry acknowledgement and `0x1E` ESC-ID enumeration to their V1.6 semantic counterparts with high confidence.
- The V1.7 `0x00` parser reads a 44-byte DATA response: base telemetry through encoder angle, three additional 32-bit values converted from micro-radians to degrees, and PAS RPM. This matches V1.6's 45-byte INFO auto-telemetry response; V1.6 calls the middle 12 bytes reserved, while V1.7 interprets them as angular values. Their semantic names remain unknown.
- Added [V1_7_RESPONSE_DISPATCH_MAP.md](V1_7_RESPONSE_DISPATCH_MAP.md), with all observed command cases and confidence labels.
- Overall estimate updated from **50% to 54%**. The FtescLowLevelFace Qt meta-call mapping is complete; the broader outbound command builders and several custom response IDs remain open.
- No hardware connected and no serial/BLE commands transmitted.

### Next work
1. Trace the separate high-level control API methods into their outgoing INFO payloads.
2. Resolve setup response IDs 0x1B, 0x1C and 0x3A–0x3D, including marker `0x54464346`.
3. Trace CAN forwarding CMD 0x10 and its nested slave response.
4. Identify BLE framing and its relationship to the UART frame helper.
5. Stage a V1.6 Windows executable for binary comparison.


## 2026-11-22 — UartComm meta-object and outbound command map

- Discovered the second major static meta-object at `0x0051F248`, identified as `UartComm`, with string-data at `0x00F232A0`, meta-data at `0x00F22B40`, and static meta-call at `0x004BC2B0`.
- Decoded all **58 Qt methods**: 21 signals and 37 slots/invokable methods. The `uartPackHandle` slot (index 21) dispatches directly to the response parser at `0x004997A0`.
- Mapped high-level outbound request methods to native implementations, including six motor-control methods, telemetry setup, firmware version/erase/write/boot-mode, UUID, setup read/write, PPM/ADC, IMU calibration, motor identification over CAN and ESC-ID enumeration.
- Confirmed request command bytes by following direct static-meta-call cases to the method bodies and inspecting the immediate values written to the byte-append helper:
  - duty 0x03 (scale 100,000); current 0x04 (1,000); brake current 0x06 (1,000);
  - D-axis current 0x25 (1,000); position 0x26 (1,000); speed 0x27 (1);
  - firmware version 0x11; boot mode 0x13; erase 0x16; write 0x18;
  - periodic telemetry 0x1A; motor-signal setup read/write 0x1C/0x1B;
  - motor setup write/read 0x07/0x09; signal setup read 0x0A;
  - TopFlow setup write/read/default-read 0x3A/0x3B/0x3C;
  - reset/setup 0x1D; UUID 0x21; MCU encryption-related write 0x22; reboot 0x23;
  - PPM/ADC reads 0x0D/0x0E; IMU calibration 0x29; motor identify over CAN 0x0F; ESC ID over CAN 0x01.
- Confirmed control values are scaled, rounded and appended as 32-bit big-endian signed integers. The periodic telemetry request is CMD 0x1A + one enable byte + a 16-bit big-endian interval.
- Confirmed firmware block write CMD 0x18 applies a bytewise XOR transform beginning with 0xD0 and using a table at `0x00530F61`; the separate firmware orchestration calls the TEA buffer wrapper. No key material is published.
- Mapped setup serialization markers: `0xD2C6EF10`, `0x4879187D`, `0x54464346`. Their semantic names remain unknown.
- Added [V1_7_REQUEST_DISPATCH_MAP.md](V1_7_REQUEST_DISPATCH_MAP.md), including method-index mapping, command bytes, payload layouts and confidence.
- Overall estimate updated from **54% to 58%**. Outbound request/command cross-reference rises to 65%; full setup schemas, CAN forwarding and one-shot CMD 0x02 remain open.
- No ESC hardware connected and no serial/BLE commands transmitted.

### Next work
1. Trace the CMD 0x02 one-shot telemetry/control request path and relate it to `ftescGetRealtimeDataOnce`.
2. Recover complete setup serialization schemas for motor, motor-signal and TopFlow writes.
3. Map acknowledgement callback wrappers to their exact Qt signal indexes.
4. Trace CAN forwarding and BLE transport.
5. Compare V1.6 Windows binary with V1.7.


## 2026-11-22 — Response callbacks resolved to exact Qt signals

- Inspected the native signal-activation wrappers called by the `0x004997A0` response dispatcher.
- Confirmed each wrapper passes the UartComm meta-object pointer `0x0051F248` and a literal Qt signal index to the Qt activation helper.
- Resolved exact response-to-signal mapping: 0x00→signal13 realtime data; 0x01/0x1E→signal19 ESC ID list; 0x0D→signal16 PPM; 0x0E→signal17 ADC; 0x0F→signal18 motor identification; 0x11→signals3/5 firmware identity; 0x14→signal14 terminal print; 0x16→signal4 erase ack; 0x18→signal6 firmware block ack; 0x1A→signal11 auto-realtime ack; 0x1B→signal7 motor-signal read; 0x1C→signal8 motor-signal secret-key check; 0x1D/0x3A/0x3D→signal9 TopFlow setup read; 0x21→signal1 UUID; 0x22→signal2 encrypt write success; 0x24→signal15 samples print; 0x29→signal20 IMU calibration; 0x3B/0x3C→signal10 TopFlow secret-key check.
- The signal indexes were cross-checked against the decoded UartComm meta-object table. The only signal not yet tied to these dispatcher cases is index12 `ftescSignalReadAckToRtData(QString,bool)`, which is connected through a separate application-level path.
- Updated [V1_7_RESPONSE_DISPATCH_MAP.md](V1_7_RESPONSE_DISPATCH_MAP.md) with exact callback/signal evidence.
- Overall estimate updated from **58% to 60%**. Response callback mapping is now substantially complete; request payload schemas and CAN/BLE paths remain open.
- No hardware interaction or command transmission.
