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


## 2026-11-22 — Typed setup-value serializer recovered and implemented

- Decompiled `FUN_004A0790`, `FUN_004A0B00`, `FUN_0049D080`, `FUN_0049D150`, `FUN_0049D1E0`, `FUN_0049D270`, `FUN_0049CF00`, `FUN_0049CE50` and `FUN_0049CFB0`.
- Confirmed setup-write block structure: 32-bit big-endian marker followed by ordered typed values from a vector-like collection.
- Parameter IDs are used to look up metadata but are not appended by the recovered per-value serializer. The helper emits values in the collection's existing order.
- Correlated the outer discriminator with XML `valType`, the inner transmit discriminator with `valueTET`, and the scaled floating multiplier with `evalScl`.
- Recovered primitive serialization: scaled signed 16/32-bit big-endian values, IEEE-754 float32 big-endian, raw byte, unsigned/signed 16-bit, unsigned/signed 32-bit.
- Catalog distribution across 736 profile rows includes 469 `(valType=1,valueTET=9)` float32 values, 60 `(1,7)` scaled int16 values, and the other integer/byte families documented in [SETUP_VALUE_SERIALIZER.md](SETUP_VALUE_SERIALIZER.md).
- The XML includes `(1,0)` and `(2,0)` combinations for which no native transmit branch was found; the offline serializer rejects them.
- Implemented `scripts/ftesc_setup_serializer.py` and `tests/test_ftesc_setup_serializer.py`. The block builder is offline only and emits marker + values in supplied order.
- Fresh public GitHub clone tested on REA: **46 tests passed, 0 failed**; `compileall` succeeded.
- Added [SETUP_VALUE_SERIALIZER.md](SETUP_VALUE_SERIALIZER.md).
- Overall estimate updated from **60% to 62%**. Primitive setup serialization is now implemented; full per-profile value selection/order and all marker meanings remain open.
- No ESC hardware interaction or data transmission.


## 2026-11-22 — Transport pipeline linked end to end

- Identified four adjacent Qt static meta-objects and class names: FtescLowLevelFace, ToolLib, UartComm and uartPackData.
- Decoded the 4-method `uartPackData` meta-object: signal 0 `sendDataToESC`, signal 1 `uartPackDataFromESC`, slot 2 `uartPackDataHandle` → `FUN_0049CA30`, slot 3 timer → `FUN_0049C800`.
- Confirmed `FUN_004BDB20` emits uartPackData signal index 0 and `FUN_004BDB60` emits signal index 1 by reading the meta-object pointer and literal signal-index immediates in machine code.
- Confirmed `FUN_0049C5C0` builds the AA/BB/CRC/DD outer frame then calls `FUN_004BDB20`.
- Confirmed `FUN_00495910` logs the unframed INFO command and payload, then calls `FUN_004BBC20`, which emits UartComm signal index 0 `sendDataToESC`.
- Mapped FtescLowLevelFace methods: `uartCommSendToFtesc` index17 → `FUN_004819C0` → frame builder; `lowLevelSendDataToFtesc` index15 → `FUN_00481850` → serial write function pointer; `uartDataHandleAvailable` index13 → `FUN_00481030` → serial read and stream handler; `uartPackDataFromESC` index16 → `FUN_00481930` → response dispatcher.
- Confirmed UartPackData stream handler emits each validated INFO payload via signal index1; the response parser then emits typed UartComm signals.
- Added [TRANSPORT_PIPELINE.md](TRANSPORT_PIPELINE.md). The legacy connect routine at `0x00483B90` has old-style connect signatures, but its full sender/receiver argument order remains explicitly qualified.
- Added V1.7 angular extension parser `parse_realtime_data_00_v17_angular_extension`; it decodes the three 32-bit signed micro-radian fields as degrees.
- Fresh public GitHub clone tested on REA: **48 tests passed, 0 failed**; `compileall` succeeded.
- Overall estimate updated from **62% to 64%**. The main UART send/receive pipeline is now linked; BLE, CAN and full setup profile ordering remain open.
- No hardware interaction or traffic transmitted.


## 2026-11-22 — Firmware authorization preflight traced

- Decompiled the `firmwareUpdatePro` orchestrator at `0x00486570` beyond the TEA call site.
- Confirmed the preflight requests the device UUID using CMD 0x21, waits for UartComm signal index 1 `ftescGetUuidAck` with a 2,000 ms local timeout, then performs a TEA buffer transform over a 16-byte local buffer using the device-returned UUID pointer.
- The transformed 16-byte result is sent with `writeMcuEncrypt`, CMD 0x22; the orchestrator then waits up to 2,000 ms for signal index 2 `writeEncryptSuccess`.
- The local buffer is populated with the fixed ASCII sequence `0123456789abcdef` immediately before the TEA call. No UUID/key material is copied into the repository.
- Confirmed separate firmware commands: version CMD 0x11, boot mode CMD 0x13, erase CMD 0x16, block write CMD 0x18. The CMD 0x18 path applies a separate bytewise XOR transform.
- Decompiled firmware validator `0x00485130`: checks a leading `0xE9` byte and structured segment/length/checksum-related conditions. Exact image format not named.
- The validator contains a `0x30F98` byte size bound; a smaller UI warning remains to be reconciled.
- Added [FIRMWARE_UPDATE_FLOW.md](FIRMWARE_UPDATE_FLOW.md). Full block sequence, retries, bootloader transitions and image-format specification remain open.
- Added timer details to [TRANSPORT_PIPELINE.md](TRANSPORT_PIPELINE.md): parser reset timer, TopFlow timeout signal and ID-list timeout signal.
- Overall estimate updated from **64% to 66%**. Firmware authorization preflight rises to 85%; full flashing state machine remains unfinished.
- No firmware was flashed and no ESC command was sent.


## 2026-11-22 — BLE shares the UART frame layer

- Mapped UartComm `bleDataRx(QByteArray)` (meta-object index 24, native `0x004828D0`) to the same stream handler `FUN_0049CA30` used by UART.
- The low-level send slot checks a BLE-connected flag via `FUN_00401680` and invokes `FUN_004050C0` when BLE is active.
- `FUN_004050C0` slices the already-framed byte array into 20-byte chunks (0, 20, 40, …), invokes an indirect BLE-write function for each chunk and waits for asynchronous completion before the next.
- The PE import set contains Qt Bluetooth APIs including `QLowEnergyService::writeCharacteristic`, service discovery, characteristic-change signals and controller connection.
- Binary diagnostics confirm distinct BLE TX and RX characteristic lookup paths.
- Conclusion: BLE RX definitely feeds the same AA/BB stream parser; BLE TX strongly indicates the same framed packet is sent in 20-byte GATT writes. Exact characteristic UUIDs and write mode remain unresolved.
- Updated [TRANSPORT_PIPELINE.md](TRANSPORT_PIPELINE.md).
- Overall estimate updated from **66% to 68%**. BLE transport framing rises to 60%; service/characteristic identification and runtime validation remain open.
- No BLE connection or characteristic write was performed.


## 2026-11-22 — Independent UART implementation cross-check and V1.7 telemetry extension

- Inspected the public third-party repository `adamivie/flipsky-ft85bd` at pinned commit `49989ac0cde531a68799284d1de9efdd7ba14c7f`, including its Python and Arduino frame/telemetry implementations.
- Confirmed the common short-frame envelope against the V1.7 binary: AA, one-byte INFO length, CMD+DATA payload, CRC-16/MODBUS, high-byte-first CRC, DD terminator.
- Reproduced its example INFO command 0x11 frame exactly: `AA 01 11 4C 7F DD`. Added a regression test for that byte vector.
- Reconfirmed standard CRC check vector `123456789 → 0x4B37`.
- Compared common 28-byte telemetry field order and scales. The external V1.4 driver parses the base layout and calls out a 16-byte extension; V1.7 code decodes offsets 28/32/36 as signed micro-radian values converted to degrees and offset 40 as signed PAS RPM.
- Added `RealtimeDataV17Extension` and `parse_realtime_data_00_v17_extension`, plus tests for positive, negative, zero, PAS RPM and wrong command.
- Initial test run found a fixture escaping error; fixed the fixture and reran from a fresh public GitHub clone.
- Final result on REA: **51 tests passed, 0 failures**; `compileall` succeeded.
- Added [EXTERNAL_IMPLEMENTATION_CROSSCHECK.md](EXTERNAL_IMPLEMENTATION_CROSSCHECK.md). No third-party implementation source was copied into this repository.
- The third-party README's claims of FT85BD hardware testing and V1.4 compatibility are attributed to that project's author, not independently verified here.
- Overall estimate updated from **68% to 70%**. V1.7 telemetry extension decoder and independent short-frame cross-check are now implemented; extended-frame cross-model coverage, CAN, command schemas, firmware update and hardware remain open.
- No ESC was connected and no bytes were transmitted to hardware.


## 2026-11-22 — V1.7 CAN target selection state traced

- Mapped UartComm CAN-forward state: byte at object +0x0C and selected target ID at +0x10.
- Decoded setter `FUN_004954D0(enable,target)` and accessors `FUN_00495510` / `FUN_00495520`.
- UI target selection at `0x0048CE90` validates IDs below 255, sets target state and requests motor-signal setup via CMD 0x1C.
- Target-change path at `0x0048D740` updates state and repeats the setup read when the selected target changes.
- UI maintenance at `0x004890C0` clears CAN state and calls `0x004992F0`; that method builds CMD 0x01, sets a pending counter to 200 and sends it.
- Multi-target iteration at `0x00493B80` temporarily selects candidate IDs, requests CMD 0x1C setup data, then restores previous target state.
- TopFlow read at `0x004972F0` sends CMD 0x3B and uses a separate pending counter.
- `FUN_00495910` logs CAN flag/ID and payload but its body does not rewrite the payload. The exact point where CMD 0x10 + target ID wrapping is inserted remains unresolved.
- Added [CAN_FORWARDING_STATE.md](CAN_FORWARDING_STATE.md).
- Overall estimate updated from **70% to 71%**. CAN target UI/state is now mapped to 40%; wire envelope and slave response routing remain open.
- No CAN/UART traffic was transmitted.


## 2026-11-22 — Official FTESC CAN V1.4 protocol and offline telemetry decoder

- Read the user's Nextcloud copy of `FLIPSKY FTESC CAN Protocol V1.4 English.pdf`, document FT-CM-CAN-20250423-04, 22 pages, issue date 2025-04-23.
- Extracted direct CAN format: 29-bit extended identifiers, ESC ID in bits 8–15, command in bits 0–7, fixed/reserved prefix, big-endian data.
- Recorded CAN command namespace separately from UART INFO commands; direct CAN 0x00 means current-with-gear, while UART 0x00 is telemetry.
- Extracted CRC-bearing command ranges and no-CRC command family; periodic telemetry 0x0B, 0x0C and 0x0D are documented as automatically emitted every 10 ms.
- Added `scripts/ftesc_can.py`: identifier decoder/encoder, generic frame parser, CRC validation, signed I24 decoding and read-only telemetry decoders for current, eRPM/duty, temperature and voltage.
- Added `tests/test_ftesc_can.py`: 9 tests covering identifier bits, invalid prefix/width, signed current, eRPM, duty, temperature, voltage, bad CRC and malformed length.
- Added [FTESC_CAN_PROTOCOL_V1.4.md](FTESC_CAN_PROTOCOL_V1.4.md); clarified the direct CAN layer in [CAN_FORWARDING_STATE.md](CAN_FORWARDING_STATE.md).
- Fresh public GitHub clone: **60 tests passed, 0 failed**; `compileall` succeeded.
- Overall estimate updated from **71% to 73%**. Direct CAN V1.4 telemetry decoder is complete for the three periodic messages; V1.7 UART CMD 0x10 wrapper and slave response routing remain 40%.
- No CAN interface opened and no frames transmitted.


## 2026-11-22 — V1.7 CMD 0x02 support gap documented

- Compared the public V1.6 CMD 0x02 specification (14 DATA bytes, current request at offsets 2–3 in V1.6) with the mapped V1.7 request and response dispatchers.
- The V1.7 response switch at `0x004997A0` has no CMD 0x02 case.
- The decoded UartComm request methods do not include a direct CMD 0x02 builder.
- UartComm signal index 13 `ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA)` exists and is connected in Qt metadata, but it is a signal and does not prove an outbound request builder.
- Added [V1_7_ONE_SHOT_CMD_02_STATUS.md](V1_7_ONE_SHOT_CMD_02_STATUS.md) with exact negative evidence and next static-analysis targets.
- Overall estimate remains **73%**; this is an identified unresolved feature gap, not a completed protocol path.
- No command was sent.


## 2026-11-22 — V1.7 firmware erase/write pipeline recovered

- Corrected a prior report classification: `FUN_00485130` is the erase-and-block-write orchestrator, not a firmware image validator. The previously claimed `0xE9` image-magic check is withdrawn; it is not present in the traced update path.
- Traced `firmwareUpdatePro` (`0x00486570`) through UUID/TEA preflight and into the flash orchestrator.
- Confirmed native file-size guard `0x30F98` bytes (200,600) and separate UI warning “150Kbyte”; mismatch documented.
- Confirmed erase request CMD 0x16 contains 32-bit big-endian image size and waits for `ftescFirmwareEraseRespenseFlag`.
- Confirmed flash loop chunks image into at most 0xF0 (240) bytes, sends CMD 0x18, waits up to 2,000 ms and retries each block up to 3 times on timeout.
- Confirmed per-block XOR transform resets each chunk: first byte mask 0xD0; remaining bytes use the 239-byte table at VA 0x00530F61 from index 0. The table was recovered and placed in the offline codec.
- Confirmed CMD 0x18 response signal `ftescFirmwareWriteBlockSuccessFalg`.
- Confirmed updater computes whole-image CRC16 and builds a size+CRC buffer; its downstream consumer is not yet resolved, so the codec does not claim it is transmitted.
- Added `scripts/ftesc_firmware.py` and `tests/test_ftesc_firmware.py` (11 tests); offline frame builder uses the existing UART codec.
- Rewrote [FIRMWARE_UPDATE_FLOW.md](FIRMWARE_UPDATE_FLOW.md) to correct the earlier misclassification and document exact block/retry behavior.
- Fresh public GitHub clone: **71 tests passed, 0 failed**; `compileall` succeeded.
- Overall estimate updated from **73% to 75%**. Firmware update path rises to 90%; image container format, whole-image CRC consumer, exact cross-version table compatibility and runtime behavior remain open.
- No bootloader was entered and no firmware was flashed.


## 2026-11-22 — Exact ValueSeque serialization order recovered

- Restored all compressed source XML and catalogs from the fresh public clone on REA using `scripts/restore_payloads.py`.
- Parsed the `Values` and `ValueSeque` sections of all 13 ValueSetups XML resources.
- Confirmed `ValueSeque` order differs from the `Values` order in all 13 resources; serialization order cannot be inferred from XML element order or sorted IDs.
- Counted 736 Values entries, 721 ValueSeque entries and 15 values omitted from their sequence; zero duplicate sequence entries and zero sequence IDs missing from Values.
- Omitted IDs: `motor_rated_current` (9 resources), `battery_cells_s` (3), `battery_cutoff_v` (3). Their exclusion reason is not assumed.
- Added `scripts/ftesc_profiles.py` to validate and extract order, omission records and source hashes.
- Added `encode_profile_block()` to `scripts/ftesc_setup_serializer.py`; added six tests for sequence order and malformed profile lists.
- Generated and published full ordered CSV/JSON artifacts as gzip+base64 payloads; `scripts/restore_payloads.py` restores them automatically. Added [profile-order-summary.json](../analysis-data/profile-order-summary.json).
- Added [V1_7_PROFILE_SERIALIZATION_ORDER.md](V1_7_PROFILE_SERIALIZATION_ORDER.md) and updated [SETUP_VALUE_SERIALIZER.md](SETUP_VALUE_SERIALIZER.md).
- Fresh public clone: restore 17+ payloads, regenerate 13 profiles (721 ordered values), **77 tests passed, 0 failed**, `compileall` succeeded.
- Overall estimate updated from **75% to 77%**. The ordered setup serializer is 90%; resource selection logic and conditional second-block selection remain open.
- No setup values were transmitted.


## 2026-11-22 — Realtime-data signal tied to CMD 0x00 response

- Analyzed callback wrapper `0x004BC060`: it copies the `FTESC_REALTIME_DATA` structure and activates the corresponding Qt signal.
- Correlated it with UartComm meta-object signal index 13, `ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA)`, called by the CMD 0x00 response branch in `0x004997A0`.
- Updated [V1_7_RESPONSE_DISPATCH_MAP.md](V1_7_RESPONSE_DISPATCH_MAP.md) and [V1_7_ONE_SHOT_CMD_02_STATUS.md](V1_7_ONE_SHOT_CMD_02_STATUS.md).
- Conclusion: this signal is response-side realtime telemetry, not a CMD 0x02 request builder. The actual CMD 0x02 request path remains unresolved.
- Overall estimate remains **77%**.


## 2026-11-22 — Firmware-directory table selection and resource families mapped

- Analyzed `FUN_00488010`: selects `ftesc/1.7/TopFlowSetupValueTable.xml` for one mode, or the MotorSetup + ControlSetup official table paths otherwise.
- Analyzed `FUN_00492570`: scans the `://ftesc` firmware directory, loads MotorSetupValueTable_official.xml, ControlSetupValueTable.xml, TopFlowSetupValueTable.xml and FirmwareVersionInf.xml, then matches two parsed integer selectors.
- The exact meaning of those selectors and the mapping of the 13 compressed resource streams to named files/SKUs remain unresolved.
- Classified the 13 extracted ValueSetups resources by parameter names: 4 control setup (173 values/173 ordered), 6 motor setup (273/261), 3 motor-signal/FOC setup (290/287).
- Updated `scripts/ftesc_profiles.py` to emit the family label; updated full compressed CSV/JSON artifacts and summary.
- Added [V1_7_FIRMWARE_CONFIG_DISCOVERY.md](V1_7_FIRMWARE_CONFIG_DISCOVERY.md) and updated [V1_7_PROFILE_SERIALIZATION_ORDER.md](V1_7_PROFILE_SERIALIZATION_ORDER.md).
- Added 3 classification tests. Fresh public clone: restore payloads, regenerate 13 resource variants/721 ordered entries, **80 tests passed, 0 failed**, `compileall` succeeded.
- Overall estimate updated from **77% to 78%**. Setup serialization rises to 92%; model/SKU selection and TopFlow schema remain open.
- No setup data was sent.


## 2026-11-22 — Firmware config version selector resolved

- Cross-referenced both callers of `FUN_00492570`: startup helper `FUN_0047F530` and main-window constructor `FUN_0048E570`.
- Both pass `(1, 7)`, matching the embedded path `ftesc/1.7`.
- The loader parses two numeric values from `FirmwareVersionInf.xml` and compares them with these parameters. They are firmware major/minor selectors, not hardware model IDs.
- Updated [V1_7_FIRMWARE_CONFIG_DISCOVERY.md](V1_7_FIRMWARE_CONFIG_DISCOVERY.md). The mapping of the 13 ValueSetups resource IDs to actual hardware/SKU variants remains open.
- Overall estimate updated from **78% to 79%**; test suite remains **80 passed, 0 failed**.


## 2026-11-22 — V1.6 C source cross-check

- Read the user's `ftesc_v1.4_1.5_1.6_uart_handle.c` (12,314 bytes) through Nextcloud.
- Confirmed the short/long UART frame markers, length encoding, CRC-16/MODBUS table algorithm, CRC high/low byte order and 0xDD terminator.
- Confirmed V1.6 command enum including 0x00 telemetry, 0x02 control+one-shot telemetry, 0x10 CAN forwarding, 0x19 keepalive, 0x1A auto telemetry, 0x1E ID list, 0x20, 0x25, 0x26 and 0x27.
- Confirmed the C sample sends one-shot realtime command 0x00 and parses the base telemetry layout that V1.7 extends.
- The C enum declares CMD 0x02 and 0x10 but the sample parser implements only response 0x00 and contains no outbound builder for 0x02 or CAN wrapper. This corroborates, but does not close, the V1.7 gaps.
- Added [V1_6_C_REFERENCE_CROSSCHECK.md](V1_6_C_REFERENCE_CROSSCHECK.md); did not copy the source file into the public repo.
- Overall estimate updated from **79% to 80%**; test suite remains **80 passed, 0 failed**.


## 2026-11-22 — V1.7 request payload schemas and offline builders

- Decoded UartComm meta-object index 32: `ftescGetAutoRealtimeData(uint8,uint16)` → `FUN_004993F0` at 0x004993F0; payload is CMD 0x1A, enable byte, uint16 BE interval.
- Mapped scalar control payloads: duty 0x03 ×100,000; current 0x04 ×1,000; brake current 0x06 ×1,000; Id current 0x25 ×1,000; position 0x26 ×1,000; speed 0x27 ×1.
- Mapped setup write markers: CMD 0x07 + D2C6EF10; CMD 0x1B + D2C6EF10 and optional 4879187D second block; CMD 0x3A + 54464346.
- Mapped reset overloads: TopFlow reset CMD 0x1D with no DATA; motor-signal reset/reboot CMD 0x1D with one byte.
- Mapped IMU calibration CMD 0x29 with signed int32 BE scaled ×1,000.
- Added `scripts/ftesc_requests.py` with offline-only INFO payload builders and `tests/test_ftesc_requests.py` (9 tests).
- Added [V1_7_REQUEST_PAYLOAD_SCHEMAS.md](V1_7_REQUEST_PAYLOAD_SCHEMAS.md) and linked it from [V1_7_REQUEST_DISPATCH_MAP.md](V1_7_REQUEST_DISPATCH_MAP.md).
- Fresh public clone: payload restoration succeeded, **89 tests passed, 0 failed**, `compileall` succeeded.
- Overall estimate updated from **80% to 82%**. Request payload builders are 85%; CMD 0x0F, CMD 0x02, CAN wrapper 0x10 and TopFlow schema remain open.
- No request was transmitted.


## 2026-11-22 — CMD 0x0F field order and native rounding verified

- Disassembled `FUN_00499180` instruction by instruction.
- Confirmed payload order: CMD 0x0F, arg2 byte, low byte of arg1, signed int16 arg4, signed int16 arg3×100, arg5 byte.
- Added `build_identify_motor_over_can_info()` using generic argument names because semantic labels/units are not identified.
- Disassembled `FUN_0049D150` (signed int32 scaling) and `FUN_0049D1E0` (signed int16 scaling): both use a 0.5 epsilon, direction-dependent x87 rounding mode and truncate-to-integer conversion, implementing round-half-away-from-zero.
- Verified the epsilon constant at VA `0x005312C0` is float32 0.5.
- Added tests for CMD 0x0F byte order and positive/negative half ties. Updated request schema/dispatch docs.
- Fresh public clone: **91 tests passed, 0 failed**, `compileall` succeeded.
- Overall estimate updated from **82% to 83%**. CMD 0x0F byte layout is resolved; semantic field labels and UART CMD 0x10 wrapping remain open.
- No motor-identification command was sent.


## 2026-11-22 — V1.7 response decoders expanded

- Decompiled response dispatcher `0x004997A0` and helper `0x0049D510` in detail.
- Confirmed CMD 0x0D: one signed int32 scaled by 1,000,000.
- Corrected an earlier note: CMD 0x0E reads **six** signed int32 values, scales [1e6, 1e6, 1, 1, 1, 1e6], and emits the six-argument ADC signal.
- Confirmed CMD 0x29 reads nine signed int32 values, each scaled by 1,000,000.
- Confirmed CMD 0x16, 0x18 and 0x22 each read one byte as boolean; CMD 0x1A is a no-DATA acknowledgement.
- Extended ESC ID vector parser to accept both CMD 0x01 and 0x1E response paths, which share the same Qt callback.
- Added `scripts/ftesc_responses.py` and `tests/test_ftesc_responses.py` (7 tests); added one ID-list test.
- Updated [V1_7_RESPONSE_DISPATCH_MAP.md](V1_7_RESPONSE_DISPATCH_MAP.md) with corrected six-value ADC layout and new decoders.
- Fresh public clone: payload restoration succeeded, **99 tests passed, 0 failed**, `compileall` succeeded.
- Overall estimate updated from **83% to 84%**. Basic numeric/boolean responses are 70%; firmware version, variable strings, setup payloads and UUID details remain open.
- No response was captured from hardware.


## 2026-11-22 — UUID response decoder added

- Traced CMD 0x21 response branch: it copies remaining DATA into a QByteArray and emits the UUID acknowledgement signal.
- The firmware-update TEA preflight consumes a 16-byte key, but the response dispatcher does not visibly enforce the 16-byte length.
- Added `parse_uuid_response()` preserving raw bytes and a test for a 16-byte key.
- Updated [V1_7_RESPONSE_DISPATCH_MAP.md](V1_7_RESPONSE_DISPATCH_MAP.md) and [FIRMWARE_UPDATE_FLOW.md](FIRMWARE_UPDATE_FLOW.md).
- Fresh public clone: **100 tests passed, 0 failed**, `compileall` succeeded.
- Overall estimate updated from **84% to 85%**. UUID raw response is covered; firmware-version and variable-string responses remain open.
- No UUID was requested from hardware.


## 2026-11-22 — Native ValueSetup response decoder implemented

- Decompiled `FUN_004A10C0`: reads a big-endian 32-bit marker, validates it, then iterates the ValueSetup vector in order and calls `FUN_004A0B70`.
- Decompiled `FUN_004A0B70`: resolves metadata via `FUN_004EBE20` and decodes according to `valType`, `valueTET` and `evalScl`.
- Mapped read types: float scaled signed16/32, IEEE float32, unsigned/signed byte, unsigned/signed16, unsigned/signed32, and signed byte for outer types 4/6/7.
- Confirmed `Invalid SecretKey` is the fixed marker-mismatch error, separate from UUID/TEA firmware authorization.
- Added `decode_profile_block()` and `DecodedSetupBlock` with a `next_offset` for parsing the optional second CMD 0x1B block.
- Refined signed-byte encoding for TET2 and outer valTypes 4/6/7.
- Added 4 tests for all supported decode types, sequential marker blocks, marker mismatch and truncation.
- Added [V1_7_SETUP_RESPONSE_DECODER.md](V1_7_SETUP_RESPONSE_DECODER.md); updated [SETUP_VALUE_SERIALIZER.md](SETUP_VALUE_SERIALIZER.md).
- Fresh public clone: **104 tests passed, 0 failed**, `compileall` succeeded.
- Overall estimate updated from **85% to 87%**. Motor/signal setup request/response codecs are now 95%; TopFlow schema and profile/SKU selection remain open.
- No setup response was captured from hardware.


## 2026-11-22 — CI and public repository reproducibility

- Added `.github/workflows/offline-checks.yml` to restore gzip/base64 artifacts, regenerate the parameter catalog and ValueSeque profiles, compare generated outputs byte-for-byte, run all unit tests and compile Python sources.
- The first local workflow-equivalent run exposed stale parameter catalog payloads due to HTML whitespace normalization. Regenerated the compressed CSV, JSON and ID catalog payloads from the current script and published them.
- Re-ran the entire sequence on REA: **all catalog/profile cmp checks passed**, 104 unit tests passed, and `compileall` passed.
- Confirmed GitHub repository `Estcool9/flipsky-esc-protocol-analysis` is public, default branch `main`, with admin/push permission.
- Added official Flipsky FTESC Gateway product-page context: USB passthrough to address/identify/configure a specific ESC by CAN ID, common CAN baud and unique IDs. This supports the use case but does not reveal CMD 0x10 wire framing.
- Added official FT Series V1.6 update guide cross-check: bootloader, reconnect, flash; dual-drive master and slave updated independently over USB.
- The linked Gateway V1.6 manual PDF could not be retrieved by the browser; this limitation is recorded in [EXTERNAL_REFERENCES.md](EXTERNAL_REFERENCES.md).
- Overall estimate updated from **87% to 88%**. Reproducibility/CI rises to 90%; exact CAN wrapper, TopFlow schema, model/resource mapping and hardware validation remain open.


## 2026-11-22 — Firmware-version and variable-text response decoders

- Revisited response dispatcher `0x004997A0` case 0x11: reads three leading bytes, converts the following byte array to QString, then reads a trailing byte; emits firmware-version structure and separate firmware-type signal.
- Added `parse_firmware_version_response()` preserving major, minor, type byte, raw label bytes, UTF-8 label and suffix byte without guessing suffix semantics.
- CMD 0x0F reads a QString-like label followed by a boolean status; added `parse_motor_identify_response()`.
- CMD 0x14 terminal print and CMD 0x24 samples print both convert response DATA to QString; added `parse_text_response()`.
- Added three tests and updated [V1_7_RESPONSE_DISPATCH_MAP.md](V1_7_RESPONSE_DISPATCH_MAP.md).
- Fresh public clone: **107 tests passed, 0 failed**, `compileall` succeeded.
- Overall estimate updated from **88% to 89%**. Variable-text response paths are now 90%; the CMD 0x11 string boundary/encoding and suffix semantics remain unvalidated without a live capture.
- No hardware response was captured.


## 2026-11-22 — Setup response signals and high-level decoders

- Read Qt signal wrapper machine code and decoded the UartComm meta-object indexes:
  - index 7 `ftescMotorSignalReadAck(QString,bool)`;
  - index 8 `ftescMotorSignalSecretKeyCheckAck(int)`;
  - index 9 `ftescTopFlowSetupReadAck(QString,bool)`;
  - index 10 `ftescTopFlowSecretKeyCheckAck(int)`.
- Corrected response mapping: CMD 0x1B no-DATA status → index7; CMD 0x1C two marker blocks → indexes8 and7; CMD 0x1D/0x3A/0x3D no-DATA status → index9; CMD 0x3B/0x3C TopFlow marker block → indexes10 and9.
- CMD 0x1C checks both markers (0xD2C6EF10 and 0x4879187D) and expected vs actual payload length; emits secret-key status 0 on success, -1 on failure.
- CMD 0x3B/0x3C checks marker 0x54464346 and payload length; emits TopFlow secret-key status 0 or -1.
- Added `parse_setup_write_ack()`, `parse_motor_signal_setup_response()` and generic `parse_topflow_setup_response()`.
- Added three tests for two-block motor-signal response, generic TopFlow response and no-DATA ACKs.
- Updated [V1_7_RESPONSE_DISPATCH_MAP.md](V1_7_RESPONSE_DISPATCH_MAP.md) and [V1_7_SETUP_RESPONSE_DECODER.md](V1_7_SETUP_RESPONSE_DECODER.md).
- Fresh public clone: **110 tests passed, 0 failed**, `compileall` succeeded.
- Overall estimate updated from **89% to 90%**. Motor-signal response decoding is covered; TopFlow metadata, SKU mapping and live validation remain open.
- No hardware traffic was generated.


## 2026-11-22 — Full resource scan and 19-profile ValueSetup catalogue

- The original extractor tested 14 known offsets. A bounded, read-only scan of 3,876 zlib-looking headers found 19 unique, complete XML streams in the V1.7 PE.
- Added six additional unique ValueSetup resources at offsets `0x1F78BA`, `0x1FED4A`, `0x204444`, `0x20CD8C`, `0x20FE7F` and `0x21F2BC`. Offset `0x1FDE78` is a duplicate.
- Added all six offsets to the reproducible extractor and committed the compressed payloads and updated extraction manifest.
- Added `encoder_setup` classification for the new encoder configuration profile.
- Updated the profile generator to report whether XML `Values` order is identical to `ValueSeque` order. Only 1 of 19 profiles match; 18 do not. Serializers must use `ValueSeque`, not XML document order.
- Current catalog: 1,152 rows, 286 distinct XML IDs, 19 profiles, 1,135 sequence entries and 17 omitted metadata entries.
- Families: 7 control, 6 motor, 5 motor-signal/FOC, 1 encoder.
- Published the profile-order CSV/JSON and summary payloads; a fresh clone restored the files from GitHub.
- TopFlow remains missing: the full scan did not find a valid XML root/resource matching the missing TopFlow table path.

## 2026-11-22 — V1.7 native UART transmit chain and CAN wrapper finding

- Decoded the Qt meta-object records for `FtescLowLevelFace`, `UartComm` and `uartPackData`.
- Mapped the normal request path: UartComm request builder → common logger `FUN_00495910` → UartComm signal `sendDataToESC` → FtescLowLevelFace slot `uartCommSendToFtesc` → AA/BB frame builder `FUN_0049C5C0` → uartPackData signal → low-level byte-array writer.
- Found 29 request-method callers of `FUN_00495910`. The common helper logs CAN-forward state, target ID, payload length and bytes, then forwards the original QByteArray without prepending `0x10 | SlaveID | SlaveCMD`.
- Added [V1_7_OUTBOUND_TRANSMIT_CHAIN.md](V1_7_OUTBOUND_TRANSMIT_CHAIN.md) with native addresses, meta-object indexes and REA evidence IDs.
- Updated [CAN_FORWARDING_STATE.md](CAN_FORWARDING_STATE.md). The conclusion is deliberately scoped: no CMD 0x10 prepend in the normal UartComm path observed; an alternate or external gateway path is not ruled out.
- No frame was transmitted and no ESC was connected.

## 2026-11-22 — Flipsky VESC V1.0 PDFs and separate VESC adapter

- Read the four user-supplied PDFs in Nextcloud: English/Chinese UART and CAN V1.0, documents `VESC-CM-UART-20250331-01` and `VESC-CM-CAN-20250331-01`, dated 2025-04-15 and aimed at VESC firmware V3.00+.
- Cross-checked VESC UART markers 02/03/04, end marker 03, CRC table (0x1021, init zero), big-endian trailer and command IDs with pinned VESC Tool source.
- Cross-checked direct CAN ID composition and basic control scales with the C example in the Flipsky document and pinned `vedderb/bldc/comm/comm_can.c`.
- Documented the stale English UART TOC and CAN identifier prose ambiguity in [FLIPSKY_VESC_PROTOCOL_V1.0.md](FLIPSKY_VESC_PROTOCOL_V1.0.md).
- Added separate offline VESC modules `scripts/vesc_uart.py` and `scripts/vesc_can.py`, plus 16 unit tests. The Flipsky VESC GET_VALUES request vector is `02 01 04 40 84 03`.
- Added [PROTOCOL_FAMILY_MATRIX.md](PROTOCOL_FAMILY_MATRIX.md); FTESC and FSESC/VESC remain explicit separate adapters.
- Updated [VESC_COMPARISON.md](VESC_COMPARISON.md) and [EXTERNAL_REFERENCES.md](EXTERNAL_REFERENCES.md), including Flipsky's 20 November 2026 separate-gateway article.

## 2026-11-22 — Reusable REA workflow and clean test run

- Verified REA host toolchain: Ghidra 12.2, Rizin/rz-bin 0.9.1, Python 3.13.5 and OpenJDK 25.
- Added [RE_WORKFLOW.md](RE_WORKFLOW.md) for future binary intake, hash identity, Rizin/Ghidra triage, Qt meta-object mapping, bounded resource extraction, evidence confidence, tests and GitHub hygiene.
- Re-ran the full unit test suite on a fresh GitHub pull on REA: **148 tests passed, 0 failed**; `compileall` succeeded.
- Updated compressed ValueSeque catalog payloads and summary after adding the Values-vs-ValueSeque ordering flag.
- Recalibrated the project-completion metric from earlier offline-only 90–92% figures to **72%** for the full open-source desktop replacement. The weighted scoring model is published in README/STATUS; UI, live transports and hardware validation remain incomplete.
- No physical ESC was connected and no UART/CAN/BLE command or firmware update was transmitted.


## 2026-11-22 — Incremental VESC UART stream decoder

- Added `scripts/vesc_stream.py` with a stateful `VescStreamDecoder` and immutable statistics snapshot.
- Parser handles fragmented and concatenated 02/03/04 frames, noise, invalid CRC/terminators, configurable INFO-size ceiling and byte-wise recovery.
- Added 7 tests in `tests/test_vesc_stream.py` for fragmentation, concatenation, leading noise, CRC recovery, medium/long frames, oversized candidates and reset.
- Corrected test fixtures to use actual byte values and direct imports.
- GitHub commits: decoder `b69ff63dbe657936f50508caa3824f4163e91ca5`; initial tests `89dc55d720cb2eeea0b53c588774cfbefd3e92fa`; test-fixture correction `b07efe968b54c4692ee02f36b767805042bcddc1`.
- Updated README, STATUS and ROADMAP. VESC/FSESC package estimate: 80% → 85%; weighted total: 71.9% → 72.4%, displayed as 72%.
- New tests have not yet been executed; previous REA baseline is 148 passing tests. CI must confirm the new tests before counting them as verified.
- No hardware or transport interface was used.


## 2026-11-22 — V1.7 BLE GATT identifiers and lifecycle mapped

- Continued REA/Ghidra 12.2 analysis on the already-open V1.7 PE32 x86 artifact (SHA-256 `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`).
- Found the Qt `BleUart` object string table and the names `dataRx`, `writeData`, `sendNextPacket`, `addDevice`, plus controller/service signals.
- Decompiled native constructor `FUN_004051C0`: service UUID `0000fff0-0000-1000-8000-00805f9b34fb` at `this+0x28`; TX characteristic `0000fff2-0000-1000-8000-00805f9b34fb` at `this+0x2C`; RX characteristic `0000fff1-0000-1000-8000-00805f9b34fb` at `this+0x30`. These values are observed literals and field assignments, not guesses.
- Mapped `FUN_00402ED0` controller creation and connections for `serviceDiscovered`, discovery completion, error, connected/disconnected, controller state and connection updates.
- Mapped `FUN_004016B0` discovered-service UUID comparison and service-found flag; `FUN_004023D0` service-object creation from the stored UUID and signal registration; `FUN_00401920` service-state handler and explicit TX/RX missing-characteristic error branches.
- Mapped `FUN_00402000` as the callback for `characteristicChanged(QLowEnergyCharacteristic,QByteArray)`; mapped service/controller error and disconnect/logging handlers.
- Located the service-state path's descriptor UUID lookup for `0x2902` (CCCD). The exact descriptor value and write mode are not yet conclusively recovered. Do not hard-code a notification payload from the UUID alone.
- A `70000` literal is passed to a timer-like wrapper in the controller init function; its unit/semantic purpose remains unconfirmed.
- New BLE doc: [BLE_GATT_V1_7_REVERSE_ENGINEERED.md](BLE_GATT_V1_7_REVERSE_ENGINEERED.md). The BLE reverse-engineering sub-workstream moves from 40% to 55%.
- Whole-product weighted score remains **72.4% (displayed 72%)**: static discovery does not implement the desktop app or a live BLE transport.
- REA retained-evidence memory reached its configured capacity during an additional large function-dossier request. That request was not accepted into the retained registry; no prior evidence was intentionally cleared. Export/checkpoint before continuing with another large analysis batch.
- Still open: the complete `writeData` / `sendNextPacket` caller path, `writeCharacteristic` mode, CCCD value, MTU/chunking/reassembly, and passive BLE capture.
- No device scan, BLE connection, characteristic write, UART/CAN transmission, or firmware operation was performed.
- Evidence IDs retained: UUID search `ev_c20b6860d554e3552d2dc6b82cebf19613220d0aa60f1a9439454420eac9ed7c`; BLE string inventory `ev_7835a85225d762c87de7b9860c87cdfb403da27dd47164414c9e8789300ff685`; Qt metadata bytes `ev_b916cb75bc14727e78b83f0b8ff0c6aba0cc33fe8e9e2d2729e558ade7a52b84`; service-state dossier `ev_3feb0512635b349f450a5ea25919bedf24032ad311879124761ef69557d31e5e`; service setup dossier `ev_a8c247ff6f88ad41db5404f895e9dac4e89b515f10c4bc39760c6635077ed985`; controller init dossier `ev_4aeaf50320792a55be39923e9659a5d8b29a4351d13bb721aae8f1806253cb12`; characteristic callback xref `ev_9c95801b699f876f5f04a72012ccdab2c9a91c1aeafbdd3f494b31e38eb6fd9f`; BleUart meta-call decompile `ev_7be243cc6465b5cd705b2bd3c40cdb13db0554d3d45bf7256e1f21315f27ff4f`.


## 2026-11-22 — Full Nextcloud Software intake and REA tooling audit

- Scanned /Projet Perso/Revolt-Engine/Software to depth 5: 92 entries, no tree truncation.
- Identified Flipsky ESC Tool V1.1–V1.7 Windows builds, three separate V1.6 Windows builds dated 2025-10-14, 2026-08-06 and 2026-09-12, a V1.6 macOS DMG, the V1.6 Android BLE APK, V1.5/V1.6 UART C samples, and separate TFT V2.0/V2.1 firmware/update artifacts.
- The V1.6 Android BLE APK is 44,167,894 bytes; it is the highest-value independent BLE cross-check candidate. It has not been staged or analyzed yet.
- Added [NEXTCLOUD_SOFTWARE_INVENTORY.md](NEXTCLOUD_SOFTWARE_INVENTORY.md) with paths, sizes, status and intake priorities.
- Audited current REA provider readiness: Ghidra 12.2 is available and supports this PE32 target. Hopper is missing, IDA is not configured, and Kuna is not configured and does not currently admit PE. ADB, Apktool, JADX/JEB Android tooling, sigrok, Binwalk/Unblob, pwntools, WABT, Wakaru and native macOS utilities are absent or not configured; these are optional and mapped to specific future sub-tasks.
- Added [TOOLING_AUDIT.md](TOOLING_AUDIT.md) with exact environment variables and the tools that are genuinely needed next.
- Largest immediate blocker is not a different decompiler: the V1.6 EXEs and BLE APK must be materialized on the REA analysis host before they can be compared. No source files were modified in Nextcloud.
- No software was installed and no hardware was connected.


## 2026-11-22 — Weighted progress calculation corrected

- Audited the ten work-package weights in README/STATUS instead of carrying forward the earlier displayed score.
- Found the relative weights total **110 points**, not 100. The current weighted contributions total **79.4 points**.
- Correct normalized score: 79.4 / 110 × 100 = **72.1818%**, shown as **72.2% unrounded / 72% rounded**.
- The previous **72.4%** unrounded figure was incorrect because the denominator was treated as 100 despite 110 relative points. Updated README, STATUS, ROADMAP and the BLE report to correct this.
- This correction does not change any workstream's implementation progress. BLE static reverse-engineering coverage is 55%; the desktop UI/live transport package remains 20%.


## 2026-11-22 — BLE byte-array ingress connected to application receiver

- Inspected FtescLowLevelFace constructor assembly at native address 0x00483910.
- Confirmed Qt connection at 0x0048456D: 1bleDataRx(QByteArray) at string address 0x0052DF35 to 2dataRx(QByteArray) at string address 0x0052DF4C.
- This establishes that the BleUart RX byte array is wired to an application-level receiver. It does not yet establish the receiver body, UART parser handoff, or stream buffering behavior.
- BLE reverse-engineering sub-workstream rises 55% to 60%. Whole-product weighted score remains 72.2% unrounded / 72% rounded.
- Updated README/STATUS/ROADMAP/BLE report. No transport interface or device was used.
- Evidence: assembly ev_48b77f16a200f240b408090beb0e346d37a46411cd19201282043055d8cc9e21; signal xref ev_9c95801b699f876f5f04a72012ccdab2c9a91c1aeafbdd3f494b31e38eb6fd9f; slot xref ev_499d842f955f91515d02843ae36178e872668e44098d657a6a0a195b717f9962; string inventory ev_63e64d98826b5c804fe70b6c398031928f0f6295d8c6b7c3d8c17038747f8103.


## 2026-11-22 — BLE shared receive parser and outbound chunk queue

- Rechecked the V1.7 target in REA/Ghidra 12.2; target SHA-256 remains `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`.
- Decompiled native BLE receive callback `FUN_004828D0`, mapped as Qt `bleDataRx` index 24. It forwards the received `QByteArray` to `FUN_0049CA30`, the already recovered incremental AA/BB stream parser used by UART. BLE receive therefore shares the same application frame parser as UART.
- Decompiled shared lower-level send slot `FUN_00481850`: when the BLE-connected predicate `FUN_00401680` is true, it routes the same framed byte array to `FUN_004050C0`.
- Decompiled `FUN_004050C0`: it slices the buffer in successive `0x14`-byte (20-byte) chunks and feeds asynchronous queue pump `FUN_00404E80`.
- `FUN_00404E80` dequeues one fragment, marks the sender busy, and constructs a completion callback to continue the queue. The final Qt GATT write call and write mode remain unresolved.
- Found the mangled `QLowEnergyService::writeCharacteristic(..., WriteMode)` string in the binary, but PE import inspection is partial because descriptor RVA `0xB9F000` has ambiguous/non-contiguous mapping. Do not infer the call boundary or write mode from the symbol string alone.
- BLE static sub-workstream: 60% → 75%. Whole-product progress remains **72.2%** (79.4 / 110 points), because no UI/live transport or hardware validation was added.
- Verified REA Android tools: Apktool 3.0.3 at `/usr/local/bin/apktool`; ADB 34.0.5-debian at `/usr/bin/adb`. No Android device was contacted. User reports JADX 1.5.7 and Temurin JDK 25 installed; the JADX MCP JAR binding remains unverified.
- User authorized temporary Nextcloud checkout for the V1.6 Android APK and three Windows builds. Transfer to REA is still blocked because the only registered Gateway host is a different LXC and cannot reach the REA CT 107 workspace or MCP endpoint. No source file was modified in Nextcloud.
- Updated: [BLE_TRANSPORT_SHARED_PARSER_AND_CHUNKING.md](BLE_TRANSPORT_SHARED_PARSER_AND_CHUNKING.md), [BLE_GATT_V1_7_REVERSE_ENGINEERED.md](BLE_GATT_V1_7_REVERSE_ENGINEERED.md), [TRANSPORT_PIPELINE.md](TRANSPORT_PIPELINE.md), STATUS, ROADMAP, README and TOOLING_AUDIT.
- No BLE scan, pairing, BLE connection, GATT read/write, UART/CAN operation, ESC command or firmware update was performed.
- Evidence: `ev_0b96fa9d9daca6528da735c37d6a4fa85f5cede2be619f08d07cfa494e6da22b`, `ev_0863f4b9c9cbaa26854a9389f1d2d4f01af0cd11963bc5043a68b1b315c57def`, `ev_26f4ad2230070fd6a96d3322a1e2c2fb5985d8d1c5709c228825789f669a36d1`, `ev_14bbb5c07a7e3c24e7f64e40abe36d4c543e0a8939b2ffd966061e649720f728`, `ev_64791b4adf0065ca2f544059fa314ba5862bbfd4c675fb96244f53cd84e50c5e`.


## 2026-11-22 — VESC stream resynchronization and CI green

- Reviewed the newly added VESC stream decoder against GitHub Actions. The first CI run reached 159 tests and isolated one failure: `test_bad_crc_recovers_to_following_frame`. A corrupt short-frame terminator (`0x03`) could be interpreted as a medium-frame start and declare a length spanning the next valid frame.
- Updated `scripts/vesc_stream.py` with a bounded-in-buffer look-ahead for a later candidate, but only resynchronizes when that later candidate's declared length is complete and its CRC and end marker validate. Otherwise the current incomplete input remains buffered.
- The earlier CI obstacle in ordered profile generation was also corrected: the old checked-in `analysis-data/profile-order-summary.json` was a stale derived snapshot. CI now validates the newly generated summary's key totals (19 profiles, 1,135 ordered values, 17 omitted values) while continuing exact file comparisons for the canonical profile CSV/JSON exports. The stale snapshot was removed.
- GitHub Actions run [#156](https://github.com/Estcool9/flipsky-esc-protocol-analysis/actions/runs/45012582295) is green: 25/25 payloads restored, parameter catalog regenerated, profile data regenerated, **159 tests passed, 0 failed**, and `compileall` passed.
- Reproducibility/tests/CI package: 95% → 100%. Weighted project score: **79.9 / 110 = 72.64% ≈ 72.6%**, displayed as 73%. UI/live transport remains 20%; hardware validation remains 0%.
- Commits in this CI correction: workflow change `b32a9803dbb250211566fdac5c29ccb0a4859079`, stale summary removal `e12fe4bb43ac84d9b309857ad60f0db39dc12136`, stream recovery `1e11a0d86585e58c64cfa7f89e32df17a2414b05`.
- No hardware, BLE, UART or CAN transport was used.


## 2026-11-22 — Candidate BLE GATT write call site

- Examined the assembly of asynchronous BLE queue pump `FUN_00404E80`.
- At call site `0x00404FEC`, ECX holds the BLE service object; three stack arguments are prepared: a characteristic-like object, the queued `QByteArray`, and integer `1`.
- `resolve_native_call_targets` resolves the computed call reference to `0x00B5A1D0`. This address lies inside the protected Enigma region; its decompilation warns of bad instruction data and is not semantically reliable.
- The argument shape and the mangled `QLowEnergyService::writeCharacteristic(..., WriteMode)` string are a strong match, but the call target cannot yet be mapped conclusively to that Qt method. The observed third argument `1` is therefore not interpreted as either write mode.
- BLE static sub-workstream: 75% → 80%. Overall score unchanged at **72.6%** (79.9 / 110). Evidence IDs: `ev_c6c574f4a7ccf94925be53eafce0df3c280bdcd98d789a023f7cbfe863da9949`, `ev_090dc82edec65beddd376fa5846a60d42657cb3321d854ee86984a3165050b51`, `ev_7a13690a90241ef5b49b36e0b1b571472b9aa6f90edb1f4d180a109a5eaaf10b`.


## 2026-11-22 — V1.6 Android BLE native analysis and Windows marker comparison

- Renewed the user's authorized temporary Nextcloud checkouts and transferred four artifacts read-only through Gateway SSH to CT 107. Verified source and destination SHA-256:
  - Android APK: `26404ff6467971ff7c0fedbe1f326c6b0ccb5722571b7309d9913818960b4d7e`.
  - Windows V1.6 2026-09-12: `051d57a776782ae8daaeaa45179f9b568f7e89b4a78ab8dd8e558ecd3e53b968`.
  - Windows V1.6 2026-08-06: `94cfd851a5ccce38b8c42c9f154128e10fa2906ce9efc9cddfa39c4a00361a03`.
  - Windows V1.6 2025-10-14: `1dc93bd84f4dab1a3ee7b3946fa0522c78fc870227523d8d5fe6d6e187ea2b07`.
- APK inventory completed: 149 occurrences / 148 unique nodes, no integrity contradictions. Extracted and hash-verified Flipsky ARM64 and ARMv7 application libraries, Qt5Bluetooth libraries for both ABIs, and Android `.rcc` bundle.
- JADX headless MCP 0.7.1 decompiled Qt Android `QtBluetoothLE` methods. `writeCharacteristic(handle, bytes, type)` maps type 1 → Android `WRITE_TYPE_DEFAULT`, type 2 → `WRITE_TYPE_NO_RESPONSE`, default → `WRITE_TYPE_SIGNED`. The backend schedules serialized I/O with a 3-second timeout, requests MTU 512 and falls back to 23, and checks CCCD first-byte notify/indicate bits. These are bridge semantics, not proof of Flipsky app-selected values.
- Rizin native symbol inventory identifies the Flipsky Android ARM64 BLE layer: `BleUart::startScan`, `startConnect`, `writeData`, `sendNextPacket`, `updateData`, `dataRx`, `serviceStateChanged`, `confirmedDescriptorWrite`. It also identifies FTESC application methods for low-level send, UART framing, boot mode, firmware write/update/status, CAN firmware identity and setup value tables.
- Targeted Windows PE32 marker scans found the same Flipsky/BLE markers in all three V1.6 builds and V1.7: `BleUart`, `FtescLowLevelFace`, `frameFwUpdate`, `UartComm`, `ftescValueTable`, `bleDataRx`, `uartPackDataFromESC`, and mangled Qt `writeCharacteristic`. V1.6 2025-10-14 additionally surfaced a Qt Win32 private writeCharacteristic symbol in the targeted scan; record as a string-level delta only.
- Windows PE import inspection remains partial because Enigma/virtual-span mapping makes import descriptor ranges ambiguous; no inference of empty imports is permitted. Ghidra targeted decompilation of large ARM64 app library timed out; Rizin symbol inventory remains available.
- BLE static sub-workstream: 80% → 85%; V1.6 EXE comparison sub-workstream: 0% → 25% (marker-level only). Whole-product score remains **72.6%** (79.9 / 110); no live transport, UI or hardware validation was added.
- Open WebUI/Qwen recommendation recorded: Qwen3.8-27B as first planner trial, Qwen3.6-35B-A3B as alternative, Qwen3.5-9B as restricted evidence/report helper; see [LOCAL_QWEN_OPENWEBUI_AGENT_ARCHITECTURE.md](LOCAL_QWEN_OPENWEBUI_AGENT_ARCHITECTURE.md). No Open WebUI, Ollama, Gateway credential or MCP server configuration was changed.
- Detailed Android report: [ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md](ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md).
- Safety: no APK/EXE executed, no Android device contacted, no BLE scan/pair/connect/GATT read/write, no UART/CAN transmission, no ESC command, and no firmware operation. Nextcloud originals unchanged.


## 2026-11-22 — Exact Android V1.6 BLE transport semantics and shared RX parser

- Continued static analysis of the extracted ARM64 native application library:
  `/data/analysis/extracted/v1.6_ble_native/lib/arm64-v8a/libFilpsky_ESC_Tool_V1.6_20251014_arm64-v8a.so`, SHA-256 `7fba6a69f3719b70dfb7eee87c97e41aad2d8f48d1feec7058a0e5975a5ea2fc`.
- `BleUart::writeData` at `0x000FE09C`: instruction `0x000FE0BC` sets chunk stride `0x14` (20); the loop calls `QByteArray::mid(int,int)` at `0x000FE10C` and advances the byte offset by 20 at `0x000FE138`.
- `BleUart::sendNextPacket` at `0x000FE1A8`: resolves the characteristic, loads constant 1 at `0x000FE2A8`, moves it into `w3` at `0x000FE2C0`, and directly calls `QLowEnergyService::writeCharacteristic` at `0x000FE2C4`. Qt 5.15 C++ enum value 1 is `WriteWithoutResponse`. This is direct V1.6 Android application code, not only the Java backend.
- `BleUart::serviceStateChanged` at `0x000FF648`: looks up descriptor UUID `0x2902`, uses string literal `0100` at VA `0x002851C9`, converts via `QByteArray::fromHex` and passes the bytes to `QLowEnergyService::writeDescriptor`. The app writes bytes `01 00`, CCCD value 0x0001, enabling notifications (bit 0), not indications (bit 1).
- `BleUart::updateData` at `0x000FFB8C` calls PLT `0x000EFE60`; ELF relocation at GOT `0x00881578` resolves it to `BleUart::dataRx(QByteArray)`. The signal thunk at `0x0025ACD8` calls `QMetaObject::activate`.
- `FtescLowLevelFace::bleDataRx(QByteArray)` at `0x00234730`: PLT `0x000EA080` resolves by GOT `0x0087E688` to `QByteArray::QByteArray(QByteArray const&)`; PLT `0x000E81C0` resolves by GOT `0x0087D728` to `uartPackData::uartPackDataHandle(QByteArray)`. Thus the app-level BLE receive slot feeds the same FTESC stream parser, not a separate BLE decoder.
- Qt metadata strings `2dataRx(QByteArray)` and `1bleDataRx(QByteArray)` are present; the exact constructor-level `QObject::connect` call site between the signal and slot remains unresolved. Record the event emission and slot implementation as separate proven observations.
- Android/BLE static sub-workstream: 85% → 90%. The Windows V1.7 indirect write call remains protected and not conclusively tied to the Qt symbol; the Android V1.6 result is a strong cross-platform reference, not a substitute for that Windows call edge.
- Whole-product weighted score unchanged at **72.6%** (79.9 / 110). Negotiated ATT MTU, live outcomes, retries/reconnect and hardware validation remain open.
- Updated [ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md](ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md), [BLE_GATT_V1_7_REVERSE_ENGINEERED.md](BLE_GATT_V1_7_REVERSE_ENGINEERED.md), [BLE_TRANSPORT_SHARED_PARSER_AND_CHUNKING.md](BLE_TRANSPORT_SHARED_PARSER_AND_CHUNKING.md), STATUS and ROADMAP.
- No APK/EXE execution, ADB handset access, BLE scan/connection/GATT operation, UART/CAN transmission or ESC command was performed.


## 2026-11-22 — ARMv7 Android V1.6 BLE cross-ABI verification

- Analyzed `/data/analysis/extracted/v1.6_ble_native/lib/armeabi-v7a/libFilpsky_ESC_Tool_V1.6_20251014_armeabi-v7a.so`, SHA-256 `8ba92821d1310762ae582a9cbb07918e7e1d416238ac8110be6a04063d8b0562`, using targeted Rizin 0.9.1 disassembly and ELF relocation inspection.
- `BleUart::writeData` at `0x000C6FAC` loads `0x14` at `0x000C6FD0`, and calls `QByteArray::mid` at `0x000C701C` in the loop: 20-byte application chunks.
- `BleUart::sendNextPacket` at `0x000C70BC` loads 1 at `0x000C71C8`, stores the WriteMode argument, places it in the stack argument slot at `0x000C71E0`, and directly calls `QLowEnergyService::writeCharacteristic(..., WriteMode)` at `0x000C71F0`. Qt 5.15 enum value 1 = `WriteWithoutResponse`.
- `BleUart::serviceStateChanged` at `0x000C8694` uses CCCD UUID `0x2902` (`0x000C8950`), calls `QByteArray::fromHex` (`0x000C89FC`) and `QLowEnergyService::writeDescriptor` (`0x000C8A10`). The ARMv7 image contains a unique `0100` literal at VA `0x0026F7D9`; Rizin did not recover a direct cross-reference from that literal to this method, so the exact ARMv7 CCCD bytes are a strong match to the ARM64-proven `01 00`, but this one literal-to-call edge remains unproven.
- `BleUart::updateData` at `0x000C8C38` and `BleUart::dataRx` signal thunk at `0x0022AF34` establish the receive event path. `FtescLowLevelFace::bleDataRx` at `0x00202DC8` calls PLT `0x000B159C` via GOT `0x00809294` (`QByteArray` copy constructor), then PLT `0x000C0194` via GOT `0x0080E13C` (`uartPackData::uartPackDataHandle(QByteArray)`). This independently confirms that ARMv7 BLE RX uses the common FTESC stream parser.
- Cross-ABI conclusion: ARM64 and ARMv7 confirm identical application-level 20-byte chunks, direct Qt WriteWithoutResponse and common RX parser. ARM64 independently provides the direct CCCD `0100` literal-to-write proof; ARMv7 matches the same method/literal but direct xref was not recovered.
- Android/BLE static sub-workstream: 90% → 95%. Qt signal/slot connection edge, negotiated ATT MTU, runtime queue/notification behavior, and Windows V1.7 protected call target remain unresolved. Whole-product weighted score unchanged at **72.6%** (79.9 / 110).
- Updated [ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md](ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md), STATUS and ROADMAP.
- No Android device, BLE, GATT, UART, CAN or ESC operation was performed.


## 2026-11-22 — Android V1.6 application QML, ValueSetup and firmware resource recovery

- Parsed application-owned Qt RCC v3 tables embedded in ARM64 app `.so`, rather than relying on the generic APK Qt RCC bundle. Initializers and static table locations:
  - `qInitResources_qml` @ `0x00259F5C`: tree `0x00296F6D`, names `0x002971EB`, data `0x002976E5`.
  - `qInitResources_ftesc` @ `0x0025A088`: tree `0x002ACA6F`, names `0x002ACD45`, data `0x002ACED3`.
  - `qInitResources_ftescFw` @ `0x0025A1B4`: tree `0x002D473F`, names `0x002D4A2B`, data `0x002D4C49`.
  - `qInitResources_ftescIcon` @ `0x0025A2A4`: tree `0x007BC3CD`, names `0x007BC585`, data `0x007BC7F7`.
- Extracted 116 resource tree nodes: 28 QML files, 24 XML profile/version resources, 31 firmware file entries, 18 icons; 101 files total and zero extraction errors. All outputs remain under `/data/analysis/extracted/v1.6_ble_embedded_resources/`; no raw source resources were copied to GitHub.
- QML imports application modules `Flipsky.ftesc.FtescLowLevelFace`, `ToolLib`, `uartcomm`, `valuesetups`, `bleuart`. Main window owns UartComm and three ValueSetups objects for motor, signal and firmware metadata; BleConnectScreen uses the native BleUart object.
- On startup the UI scans BLE and can retry the last address up to five times. On connection it requests firmware identity and ESC ID; successful ID ACK triggers motor setup read, 500 ms wait, signal setup read, another 500 ms wait. Custom motor/signal XML load/save is available.
- QML screen resources cover home, BLE scan/connect, real-time telemetry/charts, motor settings/identification, signal setup and UART/PPM/ADC/PAS calibration, CAN master/slave, and firmware update.
- `ValueSetters.qml` maps ValueSetup type tests to ValueSetupDouble, ValueSetupInt, ValueSetupListEnum, ValueSetupListEnumLong and ValueSetupListEnumShort.
- FTESC control tables: version 1.0 24/24 Values/ValueSeque, 1.1 24/24, 1.2 26/26, 1.3 36/36, 1.4 46/46, 1.5 67/67, 1.6 69/69. V1.6 type code distribution 1=36, 2=8, 4=19, 6=3, 7=3.
- V1.6 official motor table: 94 Values / 93 ValueSeque; only `motor_rated_current` is metadata-only and excluded from wire order. Earlier legacy motor tables omit `battery_cells_s`, `motor_rated_current`, `battery_cutoff_v` from sequence; all serializer implementations must honor `ValueSeque`, not XML order or all metadata keys. Separate TopFlow V1.7 XML remains unresolved and must not be substituted with this FTESC data.
- Firmware RCC group has 31 names but 17 unique SHA-256 blobs; all 17 unique images are 165,880 bytes. Each first word points into SRAM (mostly `0x20011F40`, one `0x20012EE8`), and each reset vector is `0x08009019` (Thumb). This is consistent with a raw Cortex-M vector table around flash base `0x08009000`, but exact MCU, map, encryption/authentication are not established.
- Firmware QML lists bundled images using `qmlfirmwareList()`; `qmlfirmwareData(QString)` reads a selected file with QFile. `firmwareWriteToFtesc` calls `eraseFirmware` before its write path. QML limits custom BIN files to 150 Kbyte, restricts updates to a master ESC, warns bootloader entry clears settings, and exposes errors: -1 BLE disconnected, -2 not bootloader, -3 invalid file, -4 open failure, -5 oversized custom BIN, -6 UUID timeout, -7 encrypted-data write timeout, -8 update failure. The custom BIN size limit is not assumed to apply to the separate bundled image path.
- Firmware authorization, erase/write block codec, integrity, encryption, recovery and exact model-image mapping remain unresolved. No firmware code was executed or transferred to hardware.
- Android static UI/resource sub-workstream: 0% → 80%. Overall score remains **72.6%** (79.9 / 110); no desktop UI implementation or live hardware validation is claimed.
- Detailed report: [ANDROID_V1_6_QML_VALUESETUPS_AND_FIRMWARE_RESOURCES.md](ANDROID_V1_6_QML_VALUESETUPS_AND_FIRMWARE_RESOURCES.md).
- No APK/native execution, Android device query, BLE/GATT operation, UART/CAN transmission or ESC command occurred.


## 2026-11-22 — V1.6 ValueSetup metadata compatibility check

- Compared source-embedded FTESC V1.6 ControlSetup/MotorSetup official XML with the current offline setup serializer's supported type branches.
- All 69 control and 93 serialized motor records have valid required `valType` and `valueTET` combinations; no unsupported pair or missing scaling metadata was found in the serialized records.
- Control pair counts: `(2,1)=7, (4,1)=19, (1,9)=33, (2,3)=1, (1,7)=3, (6,1)=3, (7,1)=3`.
- Motor official pair counts: `(4,1)=9, (1,9)=61, (2,5)=1, (1,7)=13, (2,1)=9`.
- The Values XML child order differs from ValueSeque in both profiles. The serializer must use ValueSeque; Values order is not a substitute. This independently validates the current vector-order approach and the metadata-only omission for `motor_rated_current`.
- Whole-product progress remains **72.6%**; setup serializer work package remains 95% pending TopFlow metadata and live protocol validation.


## 2026-11-22 — Native ValueSeque parser, primitive codec and firmware flow decompilation

- Target: Android V1.6 ARM64 app library SHA-256 7fba6a69f3719b70dfb7eee87c97e41aad2d8f48d1feec7058a0e5975a5ea2fc; source APK SHA-256 26404ff6467971ff7c0fedbe1f326c6b0ccb5722571b7309d9913818960b4d7e.
- Decompiled ValueSetups::configValueStreamXml at 0x002539E8. It explicitly compares ValueSeque literal 0x00296BAA, then seque child literal 0x00296BB5; reads element text at 0x00254D08 and appends to QList<QString> at ValueSetups+0x28 via PLT 0x000F9C20, GOT 0x00886458. The later Clustering branch uses a separate list at +0x30 and incValueCluster; it is not the wire-order source.
- Native valueArralize at 0x0025324C appends the supplied U32 marker then traverses the QList by index and calls obtainValuesArray. valueDeArralize at 0x002532F8 reads/validates the marker before traversing the same QList and calling setValuesArray.
- Mapped all native ValueByteArr primitive compose/decompose methods for I8/U8/I16/U16/I32/U32/D16/D32/DA32. Integer fields use big-endian byte order; D16 and D32 are signed scaled integers; DA32 is IEEE-754 binary32. ValueSetup metadata fields include outer type +0x00, current int +0x20, TET +0x58, scale +0x60.
- Native rounding helper 0x24DEBC confirms nearest, ties away from zero, including negatives. Python _round_away_from_zero already matches; added regression tests for negative TET7 and TET8 halfways and negative-zero binary32, plus missing decoded type6/type7 assertions.
- Firmware functions recovered: encrypt @ 0x233048, tea_encrypt @ 0x232F08, firmwareUpdatePro @ 0x23316C, firmwareWriteToFtesc @ 0x2310B4, eraseFirmware @ 0x230BF0, UartComm::writeMcuEncrypt @ 0x24AFE0, UartComm::ftescEraseFirmware @ 0x24A558, UartComm::ftescWriteFirmware @ 0x24A640, block helper @ 0x231628.
- Android firmware preflight calls 32-round TEA over a 16-byte input with embedded 128-bit key material (not published), then passes it to UartComm::writeMcuEncrypt. That method creates a request with prefix/type 0x22 and sends it through uartSendDataToFtesc. It waits up to 2,000 ms for ftescMotorSignalSecretKeyCheckAck(int); ValueSecretKeyCheckedSlot sets secret-valid only for ACK integer 0. The V1.6 UI includes a distinct Invalid SecretKey failure message.
- Separate erase path builds 0x16, waits for ftescFirmwareEraseRespenseFlag(bool) up to 20,000 ms, returns timeout -10 on expiry.
- Separate write path builds 0x18, applies a repeating 256-byte XOR lookup transform (table values not published), chunks source to max 240 bytes and calls a block helper. Helper attempts at most 3 times; response -10 retries; exhaustion returns -20. Block response wait uses a 2,000 ms timeout and signal ftescFirmwareWriteBlockSuccessFalg(bool).
- These are Android V1.6 static observations. Windows V1.7 UUID/TEA evidence is version-specific; no assumption is made that its key provision and wire envelope match Android V1.6.
- Firmware static reverse-engineering substream recorded at 75%; the weighted firmware package remains 55% pending full schema, device-side acceptance, model/key mapping, integrity/recovery and hardware testing. Whole-product score unchanged at 72.6% (79.9 / 110).
- GitHub Actions [run #199](https://github.com/Estcool9/flipsky-esc-protocol-analysis/actions/runs/45022553516) passed 162 tests, 0 failures; catalog/profile restore/regeneration and compileall passed. Follow-on report commit [run #200](https://github.com/Estcool9/flipsky-esc-protocol-analysis/actions/runs/45022704143) also succeeded.
- Detailed report: [ANDROID_V1_6_NATIVE_VALUESETUP_FIRMWARE_CODEC.md](ANDROID_V1_6_NATIVE_VALUESETUP_FIRMWARE_CODEC.md).
- No APK execution, handset access, BLE/GATT, UART/CAN, ESC command, bootloader or firmware-flash operation was performed.


## 2026-11-22 — Reprise Gateway / infrastructure helper

- Vérifié via Gateway que le serveur Open Terminal `LXC-openterminal-192.168.10.53` est `ready`, Linux, compte SSH `root`, port 7845 ; l'identité SSH gérée est active et vérifiée (empreinte publique seulement).
- Consulté les capacités hôte : Debian 13 amd64, kernel 6.14.11-4-pve, LXC, session root ; aucun changement système effectué.
- Inventorié `/` puis `/root` en lecture seule, sans suivre les liens symboliques.
- Lu `/root/infrastructure-helper-skill.md` (SHA-256 `fe43566ffb397cb45f7a08fb54c3742b4f98e94710087cc58119094ac439b69b`). Le helper identifie le CT REA 107 à `192.168.10.107:22`, SSH public-key only, service `rea-mcp`, MCP `:8765` réservé à MCPHub. Connexion SSH prescrite : `ssh -o BatchMode=yes -o ConnectTimeout=5 root@192.168.10.107 'hostname; systemctl is-active rea-mcp'`.
- Prochaine action : exécuter uniquement cette vérification SSH passive, puis réutiliser REA pour analyser les fonctions existantes. Aucun binaire Flipsky, firmware ou ESC n'a été exécuté/commandé.

- Vérification SSH depuis Open Terminal vers CT107 réussie : `hostname=rea-mcp`, `systemctl is-active rea-mcp=active`, exit code 0. La connexion a utilisé la clé SSH existante en mode BatchMode ; aucun secret n'a été lu ni transmis.

- Réactivé la session REA MCP après un timeout transitoire ; `binary_session` confirme REA 6.10.1 et Ghidra 12.2 disponibles. Session Ghidra courante : PE x86 V1.6 daté 2026-09-12, SHA-256 `051d57a776782ae8daaeaa45179f9b568f7e89b4a78ab8dd8e558ecd3e53b968`, chemin REA `/data/analysis/pe/v1.6_20260912/Flipsky_ESC_Tool_V1.6_20260912.exe`. L'analyse est checkpointée par REA ; aucune modification manuelle de projet n'a été faite. L'inventaire Evidence conservé comporte 224 enregistrements et 62 liens directs, sans liens manquants.

- Découverte CLI REA : `rea` 6.10.1 est installé sur CT107 ; commandes `function`, `search`, `instructions` permettent des requêtes Ghidra sur un chemin local sans exécuter la cible. Première requête de chaînes V1.6 refusée proprement par REA avec `UNSUPPORTED_OUTPUT_COMBINATION` (token-limit non compatible avec JSON structuré) ; aucun résultat interprété, aucun artefact modifié. Requête à relancer sans fenêtre de tokens.

- Diagnostic CLI REA : `rea doctor` confirme que l'instance REA MCP et le CLI lancé via SSH ont des environnements distincts. Ghidra 12.2 est installé à `/opt/ghidra_12.2_PUBLIC`, mais `GHIDRA_INSTALL_DIR` n'est pas exporté dans le CLI. Aucun réglage permanent/service n'a été modifié.
- Relancé Ghidra CLI avec `GHIDRA_INSTALL_DIR=/opt/ghidra_12.2_PUBLIC` uniquement pour le processus. La recherche statique sur le PE Windows V1.6 (SHA-256 `051d57a776782ae8daaeaa45179f9b568f7e89b4a78ab8dd8e558ecd3e53b968`) a réussi (Evidence REA `ev_b7dc4354f176f2ada1f33bbab669f691357c0a18766d9fff96493ed685d24ca3`).
- Nouveaux marqueurs observés dans la table de chaînes Ghidra : BLE UART (`0x51a04c`, `0x51a200`), UI firmware/bootloader (`0x51a7af`, `0x51ab62`), contrainte firmware 150 KiB (`0x51b38c`), consignes master/slave et reconnexion (`0x51b084`, `0x5276c8`), symboles Qt/meta-object FTESC (`0xc1f1ea` `ftescEraseFirmware`, `0xc1f204` `ftescWriteFirmware`, `0xc1f217` `ftescJPMBootMode`, `0xc1f630` `uartPackData`, `0xc1f65d` `uartPackDataFromESC`, `0xc1f678` `uartPackDataHandle`, `0xc1f3fc` `ftescIdentifyMotorOverCan`, `0xc1f482` `setCanForwardSendFlag`). Imports Qt indiquent `QLowEnergyService::writeCharacteristic` à `0xc547c2` et QSerialPort à partir de `0xc59016`. Ces chaînes/symboles guident les xrefs mais ne prouvent pas seuls les comportements des fonctions.
- Une première tentative sans `GHIDRA_INSTALL_DIR` a échoué avant analyse (`provider_unavailable`); une tentative avec la variable de session a ensuite réussi. Aucun binaire n'a été exécuté.

- Découvert les syntaxes CLI REA `inspect-native-instruction <path> <address>` et `procedure-references <path> <procedure> --direction incoming|outgoing`. Ces commandes sont disponibles sans exécution de la cible et permettront de remonter des métadonnées Qt vers les fonctions propriétaires.

- Sur V1.6, REA/Ghidra `inspect-native-instruction` a confirmé que `0xc1f1ea` est une donnée `/string` de 19 octets (texte `ftescEraseFirmware`), pas une fonction. Ghidra ne rapporte aucun xref actionnable vers cette adresse dans cette analyse ; ce résultat vide ne prouve pas l'absence de référence (limitation REA documentée). Il faut poursuivre par recherche de références dans les tables Qt/meta-object ou analyse d'assembleur des méthodes.

- Recherche Ghidra de procédures V1.6 sur `ftesc|uartPack|BleUart|CanForward|Firmware` : inventaire complet retourné vide (`ev_c86c44a906bf72303faa65ed11e0a7edb1fd6505befda9cd1fb98e07ae4e5b45`). Les chaînes Qt observées ne sont donc pas des noms de fonctions Ghidra. Prochaine étape de corrélation : références statiques Rizin autour des données Qt.

- Recoupement Rizin 0.9.1 sur le PE Windows V1.6 : `axt` vers les chaînes Qt ciblées a trouvé un seul accès concret dans la sortie : `0x4b74bc` référence la chaîne `uartPackData` via un chargement de donnée. Aucun xref Rizin n'a été affiché pour les autres adresses ciblées (résultat limité par l'analyse et l'avertissement Rizin de zone de chaînes > 10 MiB sautée). Il faut inspecter le bloc/fonction autour de `0x4b74bc` avant de conclure sur la sérialisation.

- Inspection Rizin du xref `0x4b74bc` : fonction auto-nommée `fcn.004b74bc` contient un chargement de `0xc1f630` (`uartPackData`), un appel à `fcn.004bc0dc` puis un saut indirect via `[0xc53474]`. Il s'agit d'un stub/chemin de dispatch à qualifier ; ce n'est pas encore le codec UART lui-même. Analyse Ghidra de cette adresse à suivre.

- Tentative décompilation Ghidra de `0x4b74bc` refusée : ce point Rizin est un bloc/stub à l'intérieur du flot, pas une entrée de fonction Ghidra. REA renvoie `procedure_not_found` et rappelle que les seeds Ghidra doivent être explicitement configurés dans un nouveau processus pour les handlers non atteints par l'auto-analyse. Aucun seed n'a été ajouté ; la cible reste intacte. Prochaine étape : inventaire Ghidra complet des procédures puis sélectionner une entrée réellement observée.

- Tentative de recherche globale des procédures avec `rea search --detail summary` refusée par le CLI (`Unknown flag: --detail` sur cette commande). La syntaxe summary/evidence_output est spécifique à d'autres opérations. Aucun fichier `/tmp/flipsky-v16-procedures.json` n'a été créé ; recherche non comptée comme résultat.

- Décompilation Ghidra V1.6 de `0x4bc0dc` réussie (Evidence `ev_2c71b965f6ceb1c828c445a60198293a7dc7697873f3c50541793632064cf231`) : fonction 6 octets `JMP dword ptr [0x00c53180]`, pseudo-code `(*_DAT_00c53180)(); return;`. Ghidra observe 46 sources d'appel dans les références entrantes, mais indique que l'inventaire callers reste partiel pour les appels calculés. Ce n'est qu'un thunk/dispatch indirect générique, pas le traitement UART. La chaîne `uartPackData` est chargée par le stub Rizin `0x4b74bc`, lequel n'est pas une entrée de fonction reconnue par Ghidra.

- Recherche identique Ghidra sur Windows V1.7 (SHA-256 `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`) réussie, Evidence `ev_516d45d45d3512ce3738c2818929fdd005070a58b5be317fc4e752c347c85a3a`. Les marqueurs V1.6 réapparaissent : `BLE UART service found!`, `ftescEraseFirmware`, `ftescWriteFirmware`, `ftescJPMBootMode`, `ftescIdentifyMotorOverCan`, `setCanForwardSendFlag`, `uartPackData`, `uartPackDataFromESC`, `uartPackDataHandle`, limite firmware 150 Kbyte et avertissements master/slave. V1.7 expose aussi les chaînes `Bootloader`, `isBootloader:`, `Switch to Firmware Update: bootloader target selected:` et `Warning: Bootloader CAN ID` dans cette recherche. Les imports Qt `QLowEnergyService::writeCharacteristic` sont présents dans les deux builds (V1.6 `0xc547c2`, V1.7 `0xf5a1d2`).

- Recoupement Rizin V1.7 : le stub qui charge `uartPackData` est à `0x4bdd7c` (contre `0x4b74bc` en V1.6). Le motif assembleur est structurellement identique : stocke l'adresse de la chaîne, prépare les arguments, appelle un thunk (V1.7 `0x4c299c`, V1.6 `0x4bc0dc`), teste le résultat, puis saute via un pointeur global (V1.7 `[0xf59320]`, V1.6 `[0xc53474]`). Cela suggère une table de dispatch/métadonnées Qt déplacée entre builds ; ne prouve pas le codec ni le sens de la trame.

- Comparaison Ghidra ciblée exécutée sur les deux autres PE Windows V1.6 : 2025-10-14 (SHA-256 `1dc93bd84f4dab1a3ee7b3946fa0522c78fc870227523d8d5fe6d6e187ea2b07`, Evidence `ev_11a0a4201fc8bea258cdf0bcad2f673335fff8791974ba55b2015ee4bd064560`) et 2026-08-06 (SHA-256 `94cfd851a5ccce38b8c42c9f154128e10fa2906ce9efc9cddfa39c4a00361a03`, Evidence `ev_9fd2415bc833f0f477996603edce21c999c80aaa528fb8fa74252e7aef7c20f5`). Les deux confirment le même ensemble de marqueurs BLE UART, erase/write/bootloader, CAN, uartPackData, limite firmware 150 Kbyte et import Qt writeCharacteristic.
- Créé `docs/WINDOWS_V1_6_V1_7_STATIC_COMPARISON.md` (commit `cf538691b689945d96544ff8d092e66a6e7bd7cc`) : matrice des quatre hashes et adresses, références REA, comparaison Rizin des stubs uartPackData, comparaison des labels bootloader et limites. Les deux thunks Ghidra sont des sauts indirects génériques, pas le codec. Le score global reste 72.6% : aucun milestone fonctionnel pondéré (transport live, firmware recovery, UI ou hardware) n'est achevé par cette seule cartographie statique.

- Actualisé `docs/STATUS.md` (commit `e121fc759dbe05d79e2707b5f293dfde46becc79`) : supprimé l'affirmation obsolète que les PE V1.6 n'étaient pas sur REA, ajouté les résultats marker-level et maintenu le score 72.6%.
- Actualisé `docs/V1_7_BINARY_CROSS_REFERENCE.md` (commit `1baf8ac3b6d661759667216c37e45464b46bd4ab`) : inventaire REA corrigé, lien vers la comparaison et étapes restantes reformulées vers le diff fonctionnel.

- Actualisé `docs/ROADMAP.md` (commit `68f1c61b2e2dbe8be63803c75d7dceacd68a8b95`) : nouvelle étape cochée pour la recherche de marqueurs sur les quatre PE et les stubs Qt, avec tâches restantes explicites pour le vrai chemin fonctionnel.

- GitHub Actions run #225 (`45040895498`, head `68f1c61b2e2dbe8be63803c75d7dceacd68a8b95`) vérifiée via l'API et les logs du job `verify` : **162 tests passed, 0 failed** ; restauration des artefacts, régénération du catalogue de paramètres, régénération des profils ordonnés et `python -m compileall -q scripts tests` ont réussi.
- Actualisé `docs/STATUS.md` (commit `daf1b3db9ef112aac3fef4af1ca8806a420882ba`) : les sept tests VESC stream sont maintenant inclus dans le décompte CI confirmé; lien vers le run #225 ajouté.

- Décompilé les fonctions V1.6 Windows de chemin UART autour du dispatcher Qt : `FUN_004b7260` (Evidence `ev_81d7212d663c453221da0aa30f42738d3e5f7976efdc35e704fdb143ee5d07f3`) et `FUN_004b72a0` (Evidence `ev_c8e7b0de7c9d0ac506a25a5738b6dfad9c6d19adc72e493c093df8ca05c0f7b3`) sont des wrappers indirects sur `PTR_FUN_00c53344` utilisant la table à `0x00519260`; le rôle interne exact reste à qualifier, donc pas de nom métier attribué.
- Décompilé `FUN_00496010` (Evidence non tronquée dans REA, fichier V1.6 SHA ci-dessus) : construit l'enveloppe UART AA pour longueur INFO < 256, BB avec longueur big-endian sur deux octets pour 256..65535, calcule CRC-16/MODBUS via les tables `0x0052a760` / `0x0052a660`, puis écrit CRC et terminateur `0xDD`. Le code montre que le CRC est calculé sur les octets INFO; le code de plus de 65535 octets n'est pas validé comme cas supporté.
- Décompilé `FUN_00496480` : chemin de réception incrémental, accumule les octets reçus dans un buffer objet et appelle `FUN_00496280` pour analyser les candidats; garde un index/état et gère le compactage du buffer, la resynchronisation et le reliquat. L'analyse du sous-parseur `FUN_00496280` est la prochaine action. Ces fonctions corroborent le même design de trame et parser que le V1.7.

- Décompilé le sous-parseur V1.6 Windows `FUN_00496280` (PE 2026-09-12, Ghidra 12.2) : détecte `0xAA` (longueur INFO sur 1 octet) et `0xBB` (longueur INFO sur 2 octets big-endian), distingue `-2` = entrée incomplète et `-1` = candidat invalide, applique la limite de longueur `this+0x20`, vérifie le terminateur `0xDD`, recalcule CRC-16/MODBUS sur INFO seule et compare le CRC wire big-endian, retourne la taille totale de trame et remet le payload validé au wrapper. AA longueur nulle et BB longueur < 255 sont rejetés. Evidence produite par REA lors de cette analyse (sortie pseudocode/assembleur filtrée).
- Précision du stream parser `FUN_00496480` : accumule les fragments, compacte le buffer quand nécessaire, appelle `FUN_00496280`, conserve les octets incomplets pour le fragment suivant, avance d'un octet après un candidat invalide et retire/dispatch le payload lorsque la trame est validée.

- Recherche de chaînes Qt sur le PE V1.6 2026-09-12 (Evidence `ev_85f5bb1fa1565010d31837ebe9c5cd707b06c944f66262f70b7aa7117e768bbe`) : confirme la classe `Flipsky.ftesc.FtescLowLevelFace`, les méthodes `uartDataHandleAvailable()`, `readyRead()`, `uartPackDataFromESC(QByteArray&)`, `uartCommSendToFtesc(QByteArray&)`, `bleDataRx(QByteArray)` et `dataRx(QByteArray)`.
- Décompilé `FUN_004b3300`, dispatcher Qt statique de la classe (adresse du static meta object `0x00519218`) : le `case 0x0c` délègue vers `FUN_00480ed0` (lecture de disponibilité/lecture du device puis parser); le `case 0x17` appelle `FUN_00482750`, qui transmet un QByteArray au même `FUN_00496480` stream parser. `FUN_00480ed0` et `FUN_00482750` sont confirmés comme deux ingress vers le même parser; le lien exact de case 0x17 à `bleDataRx` doit encore être vérifié contre la table Qt, donc pas d'affirmation BLE ferme.
- `FUN_00481860` (8 octets) est un tail-call simple vers `FUN_00496010`, avec appelant `FUN_004b3300` (case 0x10), ce qui rattache le frame builder au dispatcher `FtescLowLevelFace`. La fonction `FUN_00480ed0` appelle le `QIODevice` virtuel à `this+0x3c` (méthode vtable +0x50) pour obtenir disponibilité/lecture puis appelle `FUN_00496480` en boucle. `FUN_00482750` est un wrapper `QByteArray` et appelle le même parser.

- Créé `docs/WINDOWS_V1_6_UART_FRAME_PARSER.md` (commit `c3ff259d0d7c05be4dd421b61b0ed82bd011235f`) avec les fonctions V1.6 `FUN_00496010` / `FUN_00496280` / `FUN_00496480`, leur dispatch Qt, les correspondances de rôle V1.7, les limites et les tests de parité.
- Aligné le décodeur Python `scripts/ftesc_frame.py` sur l'ordre natif (terminateur avant CRC) (commit `a038693d774ab02535f9dd7129b967908cc69dff`) et ajouté `test_terminator_precedes_crc_error_like_native_parser` (commit `26d0506f52b8a34a8bffdc2d8c0ca0490913d567`). Les autres règles AA/BB, limites BB/254/255, CRC, fragmentation et resynchronisation étaient déjà couvertes.
- Vérifié le wrapper `FUN_00480F70` : c'est le traitement d'erreur du port série (texte `Serial port error_t:`), avec arrêt/état de la liaison; il n'initialise pas la limite de payload. Le plafond V1.6 à `this+0x20` reste donc à retrouver dans le constructeur de l'objet parseur.

- GitHub Actions run #233 (`45043795801`, head commit `26d0506f52b8a34a8bffdc2d8c0ca0490913d567`) : job `verify` réussi, **163 tests passés, 0 échec** ; le nouveau test `test_terminator_precedes_crc_error_like_native_parser` apparaît dans les logs et passe ; restauration des artefacts, régénération catalogue/profils et `python -m compileall -q scripts tests` réussis. Run : https://github.com/Estcool9/flipsky-esc-protocol-analysis/actions/runs/45043795801

- Rizin `axt @ 0x519248` sur V1.6 PE confirme de nombreuses références à un meta-object distinct du `FtescLowLevelFace` (`0x519218`) et de `uartPackData` (`0x519260`); les références convergent notamment vers `FUN_004b5bf0` et `FUN_004b5b90`.
- Décompilé `FUN_004b5bf0` : dispatcher Qt statique avec `&DAT_00519248`, méthodes d'invocation indexées `0x00..0x31` et handlers UartComm commençant notamment à `FUN_00492d00`..`FUN_004947f0`. Il gère également l'enregistrement de meta-types `FTESC_REALTIME_DATA` et `FTESC_FIRMWARE_NUMBER`. L'affectation précise des index aux noms de firmware reste à dériver du tableau QMetaObject brut.

- Décodage de la table Qt `UartComm` V1.6 terminé depuis le `QMetaObject` à `0x00519248` : `stringdata=0x00c1e900`, `meta_data=0x00c1e280`, `static_metacall=0x004b5bf0`. L'en-tête Qt indique 50 méthodes, `signalCount=19`. Le pool QArrayData contient les chaînes de méthode; offsets relatifs résolus pour les 50 enregistrements. Signaux index 0–18 : `sendDataToESC`, `ftescGetUuidAck`, `writeEncryptSuccess`, `ftescFirmwareVerRec`, `ftescFirmwareEraseRespenseFlag`, `ftescFirmwareVerRecType`, `ftescFirmwareWriteBlockSuccessFalg`, `ftescMotorSignalReadAck`, `ftescMotorSignalSecretKeyCheckAck`, `ftescAutoGetRealtimeDataAck`, `ftescSignalReadAckToRtData`, `ftescGetRealtimeDataOnce`, `ftescTermialPrint`, `ftescSamplesPrint`, `signalPPMRecAck`, `signalADCRecAck`, `motorIdentifyResAck`, `ftescGetIDResAck`, `imuCalibrationReceived`. Slots/méthodes 19–49 extraits également ; les 50 noms exacts sont enregistrés au prochain rapport dédié.

- Créé `docs/WINDOWS_V1_6_UARTCOMM_QTMETAOBJECT.md` (commit `14e68c38076c6cda5b3277dfc72a01fbc895e8fc`) : le QMetaObject `UartComm` V1.6 est décodé intégralement (50 méthodes, 19 signaux, 31 slots/invokables), chaque index relié au nom exact et au handler statique quand disponible.
- Confirmé le signal sortant commun : `FUN_00492ab0` trace « Sending to ESC » et invoque `FUN_004b55f0`; ce stub appelle `QMetaObject::activate` avec meta-object `0x00519248`, méthode index 0 = `sendDataToESC(QByteArray&)`.
- Décompilé les slots firmware V1.6 : index 20 `ftescObtainFwVerSlot` → `FUN_00492d00` (requête vide avec throttle `this+0x20`); index 21 `ftescEraseFirmware` → `FUN_00492e00` (son entier d'entrée est converti en quatre octets big-endian par `FUN_00496ad0`, puis signal sortant); index 22 `ftescWriteFirmware` → `FUN_00492f00` (trace par byte XOR mais envoie le QByteArray original sans mutation visible); index 23 `ftescJPMBootMode` → `FUN_004930a0` (QByteArray vide envoyé); index 32 `writeMcuEncrypt` → `FUN_004938f0` (throttle et helper `PTR_FUN_00c53318(1,0x10,param_1)` non résolu, aucune clé ou table secrète publiée).
- Le mapping de 50 méthodes permet désormais d'aligner les signaux firmware (`ftescFirmwareEraseRespenseFlag`, `ftescFirmwareWriteBlockSuccessFalg`, `writeEncryptSuccess`, `ftescGetUuidAck`, etc.) sur la surface d'API. Les IDs numériques de commandes, schéma exact des ACK, retry/timeout et chaîne bootloader restent ouverts; aucune commande ou flash matériel effectué.

- Décompilé `FUN_004945b0`, handler de `ftescObtainIdOverCan` (UartComm index 44). Il vérifie un cooldown sur `this+0x38`; si expiré, le positionne à 200 (l'unité/temps exact reste à confirmer), construit un `QByteArray` vide et le remet à `FUN_00492ab0`, donc à `UartComm::sendDataToESC(QByteArray&)`. Cela confirme un trigger de découverte CAN sans DATA dans la couche UartComm; ne prouve pas le format de réponse ni la sélection du target ESC.

- Correction basée sur le décodage des wrappers de flux : `FUN_00496880` et `FUN_00496890` sont des wrappers d'écriture d'un octet signé via `PTR_FUN_00c53300` ; ils ne construisent pas un QByteArray vide. Les méthodes UartComm émettent donc les octets de commande observés avant les données : `ftescObtainFwVerSlot` = CMD `0x11` seul; `ftescEraseFirmware` = CMD `0x16` + argument 32 bits big-endian via `FUN_00496ad0`; `ftescWriteFirmware` = CMD `0x18` + QByteArray d'entrée inchangé; `ftescJPMBootMode` = CMD `0x13` seul; `ftescObtainUuid` = CMD `0x21` seul; `writeMcuEncrypt` = CMD `0x22` + contenu produit par un helper protégé/non résolu; `ftescObtainIdOverCan` = CMD `0x01` seul (throttle `this+0x38`, valeur 200). Les anciens commentaires de la présente session décrivant ces requêtes comme « QByteArray vide » étaient erronés et sont remplacés par cette lecture byte-level.
- Décompilé `FUN_004968a0` : convertit la valeur en 16 bits signés puis ajoute l'octet haut suivi de l'octet bas au flux (BE). `FUN_00496890`/`FUN_00496880` ajoutent un seul octet signé.
- Décompilé `FUN_00496c30`, appelé par `ftescIdentifyMotorOverCan` : multiplie le premier flottant par 100, ajoute/soustrait 0.5 selon le signe, puis applique un arrondi dirigé qui réalise le nearest/ties-away-from-zero et appelle le writer 16 bits BE. Dans `FUN_00494440`, le quatrième argument float est au contraire converti par `FISTP` avec le mode x87 `0x0C00` (truncate toward zero). Ordre CMD 0x0F + champs DATA observé : arg2 (U8), low byte de arg1 (U8), arg4 tronqué (S16 BE), arg3*100 arrondi half-away (S16 BE), arg5 (U8), soit 7 octets DATA. Les noms/unités métier des cinq arguments restent inconnus.
- Corrigé le builder Python `build_identify_motor_over_can_info` : le champ arg4 utilise maintenant une conversion int16 tronquée vers zéro, arg3*100 conserve l'arrondi half-away. Commit code `8f1696bc435bda7a742b6d64ccf8f9bc97dda28f`; nouveaux tests dans `497c100bc3c3b1eb08f3d538cb69eb1c207bdf7c`; vecteur d'origine ajusté à `-2` pour arg4 dans `8c29b07bc051bda394072585efa93a72aa5a439a`.

- Complément de l'analyse `FUN_00494440` : primitives de sérialisation native vérifiées. `FUN_00496890`/`FUN_00496880` ajoutent un octet, `FUN_004968a0` ajoute un int16 signé big-endian, `FUN_00496c30` fait `float*100` puis nearest/ties-away, tandis que `FISTP` de `param4` sous x87 RC `0x0C00` tronque vers zéro. Le builder CMD 0x0F avait donc un écart de parité : `arg4` est désormais encodé avec `_truncated_i16`; `arg3*100` garde l'arrondi half-away.
- Corrigé le vecteur natif existant `test_identify_motor_over_can_native_field_order` (-2.5 devient `0xFFFE`, soit -2) et ajouté un test dédié positif/négatif qui vérifie `arg4` tronqué et `arg3*100` arrondi. Les commits de code/tests/vecteur sont `8f1696bc435bda7a742b6d64ccf8f9bc97dda28f`, `497c100bc3c3b1eb08f3d538cb69eb1c207bdf7c`, `8c29b07bc051bda394072585efa93a72aa5a439a`.
- CI #248 et #249 ont échoué uniquement sur l'ancien vecteur CMD 0x0F qui attendait `-3` pour `-2.5`; le code native-aligned rend `-2`. Vecteur corrigé dans #250; run #252 (`45048896742`, commit `3b33076edaedd867e97aadd5d9ee0defebe158e6`) est vert : **164 tests, 0 failures**, `compileall`, restauration, catalogue de paramètres et profils ordonnés réussis. Logs : https://github.com/Estcool9/flipsky-esc-protocol-analysis/actions/runs/45048896742
