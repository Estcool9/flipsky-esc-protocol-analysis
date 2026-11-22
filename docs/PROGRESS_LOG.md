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
