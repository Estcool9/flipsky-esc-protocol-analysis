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
