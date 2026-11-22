# Analysis checkpoint — 2026-11-22

**Repository:** \`Estcool9/flipsky-esc-protocol-analysis\`  
**Overall estimated progress: 87%**  
**Executable SHA-256:** \`dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38\`

This is the authoritative hand-off note. Update it at every significant milestone.

## Latest confirmed milestone: outer framing and CRC

- Short: \`AA | LEN8 | PAYLOAD | CRC16_BE | DD\`.
- Extended: \`BB | LEN16_BE | PAYLOAD | CRC16_BE | DD\`.
- Sender uses AA for payload lengths 1–255, BB above 255.
- Receiver rejects empty AA payloads and BB lengths <=254.
- Constructor at \`0x0049C460\` initializes max payload at \`this+0x20\` to \`0x2710\` = 10,000.
- CRC-16/MODBUS: reflected polynomial A001, init FFFF, xorout 0000; payload only; serialized big-endian.
- Tables at \`0x005310C0\` and \`0x005311C0\` match generated split MODBUS tables; standard vector 123456789 gives 4B37.

## Code path

- Receive: \`0x00481030\` → \`0x0049CA30\` (\`uartPackDataHandle\`) → \`0x0049C830\` (frame parser), call at \`0x0049CC8D\`.
- Transmit: wrapper \`0x004819C0\` → \`0x0049C5C0\` (frame builder).
- Numeric readers: 16-bit big-endian at \`0x0049D3B0\`; 32-bit big-endian at \`0x0049D450\`.

## Component ownership correction

The meta-object string table near \`0x00F24080\` names the helper object \`uartPackData\` and lists:

0. \`sendDataToESC\`
1. \`uartPackDataFromESC\`
2. \`uartPackDataHandle\`
3. \`uartPackDataTimerSl\`

The handler dispatch is \`0x0049CA30\`; it calls \`0x0049C830\`. Earlier notes tentatively labelled a second component as UartComm; refine that interpretation: the framing/parser helper is the \`uartPackData\` object. Keep \`UartComm\` distinct.

## Workstream progress estimates

| Workstream | Progress |
|---|---:|
| Binary inventory and integrity | 100% |
| Embedded XML extraction and validation | 100% |
| Parameter catalog generation | 100% |
| Qt/QML architecture and class ownership | 90% |
| UART/Qt event and meta-object mapping | 100% |
| Outer frame and CRC reconstruction | 100% |
| Inner command IDs and payload layouts | 65% |
| Firmware update / TEA relationship | 55% |
| VESC compatibility assessment | 25% |
| Offline frame/parser/stream tests | 100% (36 tests passing on published tree) |
| Hardware validation | 0% |

Overall progress is a milestone-weighted estimate toward an evidenced protocol specification and offline client, not a measure of certainty or commercial-app feature completion.

## Next tasks

1. Run the new offline test suite and record exact results.
2. Trace receive buffering in \`0x0049CA30\`, including incomplete and concatenated frames.
3. Map inner response IDs in the dispatch table inside \`0x004997A0\` to acknowledgement slots.
4. Trace outgoing payload builders from \`ftescObtain*\` methods into the frame builder.
5. Document payload numeric types/scaling from their reader helpers.
6. Continue TEA call-site analysis; do not claim ordinary UART payload encryption without proof.
7. Compare only confirmed framing with VESC; do not infer compatibility from UI similarity.

## Tooling and constraints

- Rizin 0.9.1 and Ghidra 12.2 are already available in REA; no install needed for static work.
- Original EXE remains on REA (50,611,200 bytes); its identity is recorded in \`docs/ARTIFACT_INVENTORY.md\`.
- All 13 XML resources and derived catalogs are published as gzip/base64; restore with \`python scripts/restore_payloads.py --root .\`.
- No firmware image or passive serial capture was obtained in this session.
- No packets were sent to physical ESC hardware.


## Receive-buffer and test update — 2026-11-22

- Added [RECEIVE_BUFFER_STATE.md](RECEIVE_BUFFER_STATE.md), the outer-frame codec and unit tests.
- The receive handler distinguishes parser results -1, -2 and positive consumed length. -1 triggers one-byte cursor advance; positive values advance by frame length and the loop continues.
- Test command: \`python3 -m unittest discover -s tests -v\`.
- Result on REA using the published GitHub versions: **13 passed, 0 failures**.
- Current overall estimate: **40%**.


## Official V1.6 reference milestone — 2026-11-22

- Added the official V1.6 UART protocol digest, V1.4/V1.6 delta, V1.7 cross-reference, manual notes and Nextcloud source inventory.
- Preserved the ECU-side example C source under reference/.
- Added a protocol helper module and tests. Combined test suite on REA: 26 passed, 0 failed.
- V1.6 changes CMD 00 automatic telemetry, moves CMD 02 current request from D0-D1 to D2-D3 and adds the PAS-mode alias for CMD 02.
- Outer frame, CRC and big-endian conventions remain unchanged from V1.4 to V1.6 and match the private V1.7 parser/builder.
- Current overall project estimate: **46%**.
- V1.6 Windows executables are inventoried in Nextcloud but are not staged on REA.
- V1.7 command-ID to Qt-response mapping remains the next major reverse-engineering target.


## V1.7 Qt API names — 2026-11-22

- New report: [V1_7_QT_API_STRING_MAP.md](V1_7_QT_API_STRING_MAP.md).
- Found high-level API names for duty/current/brake/D-axis current/speed/position, automatic telemetry, CAN ID/identification, firmware version/update and encryption-related flows.
- The low-level uartPackData class remains distinct from the high-level FtescLowLevelFace façade.
- Candidate V1.6 opcode relationships remain unconfirmed until call sites and payload bytes are traced.
- Overall progress estimate: **48%**.


## V1.7 receive-path deep dive — 2026-11-22

- Detailed Ghidra pseudocode reviewed for parser `0x0049C830`, receive handler `0x0049CA30`, builder `0x0049C5C0`, and CRC helper `0x0049C7A0`.
- Receive handler's countdown at object offset +0x1C is set by parser output on -2 and decremented for incoming bytes before retrying parse.
- Invalid candidates advance one byte; complete frames advance by the returned consumed length; the loop can emit multiple frames per serial read callback.
- Buffer compaction preserves the unconsumed suffix and is distinct from invalid-candidate resynchronization.
- New report: [RECEIVE_PATH_DEEP_DIVE.md](RECEIVE_PATH_DEEP_DIVE.md).
- New code: `scripts/ftesc_stream.py`; new tests: `tests/test_ftesc_stream.py`.
- Published repository re-cloned and tested on REA: **36 passed, 0 failed**.
- Overall estimate: **50%**. Receive-buffer analysis 90%; stream codec and tests 100%; V1.7 command-ID mapping 20%.
- A memoryview lifetime issue discovered by negative tests was fixed by decoding from an immutable snapshot before mutating the receive buffer.
- No hardware interaction or frame transmission.


## Qt dispatch and response command map — 2026-11-22

- Decoded all 64 Qt method records in the FtescLowLevelFace meta-object and matched them to the switch cases in `0x004B98D0`.
- New report: [QT_METACALL_DISPATCH_MAP.md](QT_METACALL_DISPATCH_MAP.md).
- Resolved TEA method indexes and direct firmware-update caller; encryption use in ordinary UART frames remains unproven.
- Decompiled response dispatcher `0x004997A0`; high-confidence response correlations: CMD 0x00 telemetry, 0x11 firmware identity, 0x1A periodic telemetry ack, 0x1E ESC ID list.
- CMD 0x00 V1.7 reads the 44-byte extended telemetry DATA layout, including three extra 32-bit angular values and PAS RPM.
- New report: [V1_7_RESPONSE_DISPATCH_MAP.md](V1_7_RESPONSE_DISPATCH_MAP.md).
- Overall estimated progress: **54%**. FtescLowLevelFace Qt meta-call map 100%; V1.7 command cross-reference 35%.


## UartComm outbound command map — 2026-11-22

- Decoded UartComm static meta-object at `0x0051F248`: 58 methods, including 21 signals and 37 slots/invokable methods.
- Static meta-call at `0x004BC2B0` maps request methods to native implementations; slot index 21 `uartPackHandle` calls response dispatcher `0x004997A0`.
- New report: [V1_7_REQUEST_DISPATCH_MAP.md](V1_7_REQUEST_DISPATCH_MAP.md).
- Confirmed motor control opcodes: duty 0x03, current 0x04, brake current 0x06, D-axis current 0x25, position 0x26, speed 0x27; all values encoded as scaled, rounded 32-bit big-endian integers.
- Confirmed firmware/setup/sensor/CAN request command values and telemetry CMD 0x1A layout. Details and caveats are in the request map.
- Setup payload marker constants recovered but not semantically named.
- Overall estimated progress: **58%**. V1.7 command/payload mapping 65%; firmware update/TEA 75%.
- No physical ESC interaction.


## Response callback mapping — 2026-11-22

- Native callback wrappers now mapped to exact Qt signal indexes through their immediate arguments and UartComm meta-object pointer.
- See [V1_7_RESPONSE_DISPATCH_MAP.md](V1_7_RESPONSE_DISPATCH_MAP.md), section 8.
- Overall estimated progress: **60%**.


## Typed setup serializer — 2026-11-22

- Static code path `0x004A0B00 → 0x004A0790` recovered; marker + ordered typed values.
- XML `valType`/`valueTET`/ `evalScl` correlation documented.
- Offline serializer and 10 tests added; full published suite: **46 passed, 0 failed**.
- See [SETUP_VALUE_SERIALIZER.md](SETUP_VALUE_SERIALIZER.md).
- Overall estimate: **62%**.


## End-to-end transport pipeline — 2026-11-22

- Identified FtescLowLevelFace, ToolLib, UartComm and uartPackData Qt meta-objects.
- Linked UartComm raw INFO signal → FtescLowLevelFace frame builder → uartPackData framed signal → serial write slot.
- Linked serial read handler → stream buffer/parser → uartPackData payload signal → response dispatcher.
- Exact QObject connect argument order is still being checked; see [TRANSPORT_PIPELINE.md](TRANSPORT_PIPELINE.md).
- Added V1.7 telemetry extension decoder and two tests.
- Full published test suite: **48 passed, 0 failed**.
- Overall progress: **64%**.


## Firmware authorization flow — 2026-11-22

- `firmwareUpdatePro` requests UUID (CMD 0x21), waits 2 s, TEA-encrypts a 16-byte local buffer with the UUID pointer, sends CMD 0x22, then waits 2 s for write-encrypt acknowledgement.
- Separate update methods: boot mode 0x13, erase 0x16, block write 0x18; CMD 0x18 has a separate XOR transform.
- Image validator `0x00485130` checks 0xE9 magic and structured segments; exact firmware format remains unidentified.
- Added [FIRMWARE_UPDATE_FLOW.md](FIRMWARE_UPDATE_FLOW.md).
- Overall estimate: **66%**.


## BLE transport — 2026-11-22

- BLE receive callback feeds the same stream parser as UART.
- BLE transmit fragments the same framed packet into 20-byte writes and waits for asynchronous completion.
- Qt Bluetooth imports include `QLowEnergyService::writeCharacteristic`; characteristic UUIDs/write mode not yet mapped.
- See [TRANSPORT_PIPELINE.md](TRANSPORT_PIPELINE.md).
- Overall estimate: **68%**.


## Independent frame and telemetry cross-check — 2026-11-22

- Inspected third-party `adamivie/flipsky-ft85bd` pinned commit `49989ac0cde531a68799284d1de9efdd7ba14c7f`. It is a community implementation, not Flipsky source.
- Short frame and CRC independently agree; exact example `AA 01 11 4C 7F DD` reproduced by our codec.
- Standard CRC vector `123456789` → `0x4B37`.
- Added `parse_realtime_data_00_v17_extension`: 3 signed 32-bit micro-radian values converted to degrees, plus signed 32-bit PAS RPM.
- Added [EXTERNAL_IMPLEMENTATION_CROSSCHECK.md](EXTERNAL_IMPLEMENTATION_CROSSCHECK.md).
- Fresh clone test suite: **51 passed, 0 failed**; compileall succeeded.
- Overall estimate: **70%**.


## CAN target state — 2026-11-22

- UartComm +0x0C = CAN-forward enabled; +0x10 = selected target ID.
- UI selection validates ID <255, stores target and requests motor-signal setup CMD 0x1C.
- Automatic ID discovery sends CMD 0x01; per-target setup iteration and TopFlow CMD 0x3B mapped.
- The V1.7 code path that inserts CMD 0x10 + CAN ID into the outgoing payload and routes slave responses remains unresolved.
- See [CAN_FORWARDING_STATE.md](CAN_FORWARDING_STATE.md).
- Overall estimate: **71%**.


## Direct CAN V1.4 decoder — 2026-11-22

- Read the official Flipsky FTESC CAN Protocol V1.4 PDF from Nextcloud.
- Added read-only parser for 29-bit extended IDs, CRC-16/MODBUS and periodic telemetry commands 0x0B/0x0C/0x0D.
- Signed 24-bit current/eRPM fields, signed 16-bit temperatures and voltage are decoded with documented scales.
- Direct CAN command IDs are a separate namespace from UART INFO command IDs.
- Added [FTESC_CAN_PROTOCOL_V1.4.md](FTESC_CAN_PROTOCOL_V1.4.md) and [scripts/ftesc_can.py](../scripts/ftesc_can.py).
- Fresh clone test suite: **60 passed, 0 failed**.
- Overall estimate: **73%**.


## CMD 0x02 gap — 2026-11-22

- Public V1.6 CMD 0x02 request layout is 14 DATA bytes; V1.6 moved current request to DATA offsets 2–3.
- V1.7 response dispatcher `0x004997A0` contains no CMD 0x02 case.
- UartComm request table has no direct CMD 0x02 builder.
- Signal index 13 `ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA)` exists, but it is response-side Qt signal evidence, not a request builder.
- See [V1_7_ONE_SHOT_CMD_02_STATUS.md](V1_7_ONE_SHOT_CMD_02_STATUS.md).
- Overall estimate remains **73%**.


## V1.7 firmware update pipeline — 2026-11-22

- `firmwareUpdatePro` at 0x00486570: built-in/custom file selection, 0x30F98 native size bound, UUID CMD 0x21, TEA challenge and CMD 0x22 authorization.
- `FUN_00485130`: erase, then sequential 240-byte chunks.
- Erase CMD 0x16 contains uint32 BE image size; wait for `ftescFirmwareEraseRespenseFlag`.
- Write CMD 0x18 applies XOR sequence per block: first mask 0xD0, then 239-byte table at 0x00530F61; waits for `ftescFirmwareWriteBlockSuccessFalg`.
- Each block waits 2 s and retries up to 3 times on timeout.
- Implemented offline codec `scripts/ftesc_firmware.py`; 11 new tests.
- Earlier claim of an 0xE9 firmware magic check at 0x00485130 withdrawn; that function is the flash loop.
- Fresh clone test suite: **71 passed, 0 failed**.
- Overall estimate: **75%**.


## ValueSeque order — 2026-11-22

- All 13 XML resources restored and parsed.
- 736 values, 721 ordered entries, 15 omitted values; no duplicate/unknown sequence IDs.
- ValueSeque order differs from Values order in all 13 resources.
- Added profile order extractor, profile-aware setup block encoder, compressed full CSV/JSON artifacts and summary.
- Fresh clone restore + generation succeeded; **77 tests passed, 0 failed**.
- Overall estimate: **77%**.


## CMD 0x00 telemetry signal correlation — 2026-11-22

- `0x004BC060` copies `FTESC_REALTIME_DATA` and emits UartComm signal index 13 `ftescGetRealtimeDataOnce(...)`.
- The CMD 0x00 response branch calls this wrapper.
- This signal is response-side, not a CMD 0x02 request builder.
- CMD 0x02 remains unresolved; progress remains **77%**.


## Firmware config table discovery — 2026-11-22

- `0x00488010` selects embedded V1.7 default table paths.
- `0x00492570` scans firmware directories and loads four named XML tables, matching two numeric selectors.
- 13 ValueSetups resources classify into 4 control, 6 motor, 3 motor-signal/FOC groups.
- 736 Values entries, 721 ValueSeque entries, 15 omissions.
- Updated family classifier and compressed order artifacts.
- Fresh clone: **80 tests passed, 0 failed**.
- Overall estimate: **78%**.


## Firmware config version selection — 2026-11-22

- `FUN_00492570` is called by `FUN_0047F530` and `FUN_0048E570`, both with parameters `(1,7)`.
- This matches `ftesc/1.7` and resolves the selector as firmware major/minor.
- Hardware/SKU mapping of the 13 ValueSetups resources remains open.
- Overall estimate: **79%**.


## V1.6 C source cross-check — 2026-11-22

- Source confirms UART AA/BB framing, CRC16-MODBUS, CRC high/low order and DD terminator.
- Command enum includes CMD 0x02 and CMD 0x10; sample only sends/parses CMD 0x00 telemetry.
- Confirms base telemetry field order/scales.
- Added [V1_6_C_REFERENCE_CROSSCHECK.md](V1_6_C_REFERENCE_CROSSCHECK.md).
- Overall estimate: **80%**.


## V1.7 request payload builders — 2026-11-22

- Added offline INFO builders for control scalars, auto telemetry CMD 0x1A, setup marker blocks 0x07/0x1B/0x3A, reset variants 0x1D and IMU calibration 0x29.
- Native auto telemetry method index 32 → `FUN_004993F0`: enable byte + uint16 BE interval.
- Optional second CMD 0x1B marker is emitted only when second vector exists.
- Added [V1_7_REQUEST_PAYLOAD_SCHEMAS.md](V1_7_REQUEST_PAYLOAD_SCHEMAS.md) and `scripts/ftesc_requests.py`.
- Fresh clone: **89 tests passed, 0 failed**.
- Overall estimate: **82%**.


## CMD 0x0F and rounding — 2026-11-22

- Native function `0x00499180` payload order: 0F, arg2, low8(arg1), signed16(arg4), signed16(arg3×100), arg5.
- Semantic argument labels remain unknown; offline builder uses generic names.
- Native helpers `0x0049D150` and `0x0049D1E0` implement round-half-away-from-zero; 0.5 epsilon at 0x005312C0.
- Added two tests; fresh clone **91 passed, 0 failed**.
- Overall estimate: **83%**.


## V1.7 response decoders — 2026-11-22

- CMD 0x0D one signed int32 ÷1e6.
- CMD 0x0E six signed int32 values with scales [1e6,1e6,1,1,1,1e6].
- CMD 0x16/0x18/0x22 one-byte boolean ACK; CMD 0x1A no-data ACK.
- CMD 0x29 nine signed int32 values ÷1e6.
- CMD 0x01 and 0x1E share ESC ID vector parser.
- Added `scripts/ftesc_responses.py`; fresh clone **99 tests passed, 0 failed**.
- Overall estimate: **84%**.


## UUID response — 2026-11-22

- CMD 0x21 copies response DATA into QByteArray; firmware TEA preflight consumes 16 bytes.
- Native response branch does not visibly enforce length; decoder preserves raw length.
- Added `parse_uuid_response()` and test.
- Fresh clone: **100 tests passed, 0 failed**.
- Overall estimate: **85%**.


## Setup response decoding — 2026-11-22

- `FUN_004A10C0` validates setup marker; `FUN_004A0B70` decodes each typed value using ValueSeque metadata.
- Added `decode_profile_block()` with sequential `next_offset` for two-marker responses.
- Supports observed numeric, float and byte types; TopFlow schema still unavailable.
- Added [V1_7_SETUP_RESPONSE_DECODER.md](V1_7_SETUP_RESPONSE_DECODER.md).
- Fresh clone: **104 tests passed, 0 failed**.
- Overall estimate: **87%**.
