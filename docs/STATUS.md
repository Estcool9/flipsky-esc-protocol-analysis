# Project status

**Reference date:** 2026-11-22  
**Overall estimated progress: 88%** toward an evidenced protocol specification and independently testable offline client.

Percentages are milestone-weighted estimates, not measurements of certainty or commercial application feature completion.

## Workstream progress

| Workstream | Progress |
|---|---:|
| Binary inventory and integrity (V1.7) | 100% |
| Embedded XML extraction and validation | 100% |
| Parameter catalog generation | 100% |
| Qt/QML architecture and class ownership | 90% |
| UART/Qt event and meta-object mapping | 100% |
| Outer frame format and CRC reconstruction | 100% |
| Receive-buffer and resynchronization analysis | 90% |
| Public V1.6 UART protocol extraction | 100% |
| V1.4-to-V1.6 protocol comparison | 90% |
| V1.7 command-ID and payload cross-reference | 86% |
| Offline frame and protocol codecs/tests | 100% |
| Firmware authorization and block-transfer flow | 90% |
| Direct CAN V1.4 telemetry decoder | 100% |
| V1.7 UART CAN-forward wrapper and slave response routing | 40% |
| VESC compatibility assessment | 25% |
| V1.6 executable binary comparison | 0% |
| Hardware validation | 0% |
| **Overall estimate** | **88%** |

## Confirmed evidence

### Official direct CAN V1.4 protocol and decoder
- Read the user's Nextcloud copy of Flipsky FTESC CAN Communication Protocol V1.4 (FT-CM-CAN-20250423-04, 22 pages, 2025-04-23).
- Implemented an offline-only 29-bit extended-ID parser and CRC validation for documented command ranges.
- Implemented read-only telemetry decoding for CAN 0x0B (motor/battery current), 0x0C (eRPM/duty) and 0x0D (temperatures/voltage), including signed 24-bit sign extension.
- Added 9 tests. The direct CAN protocol is distinct from UART INFO framing and opcodes. See [FTESC_CAN_PROTOCOL_V1.4.md](FTESC_CAN_PROTOCOL_V1.4.md).

## Confirmed evidence

### Independent implementation cross-check
- Inspected a separate public FTESC UART V1.4 implementation at pinned commit `49989ac0cde531a68799284d1de9efdd7ba14c7f`.
- Its short AA frame, CRC-16/MODBUS, big-endian CRC trailer and 0xDD terminator match V1.7.
- Independently reproduced the reference frame `AA 01 11 4C 7F DD` and standard CRC vector `123456789 → 0x4B37`.
- The public implementation is a third-party project, not Flipsky source; its model/firmware compatibility claims are not independently validated.
- V1.7 CMD 0x00 extension decoder now exposes three scaled angular values plus PAS RPM, with unknown semantic labels preserved as generic names.

## Confirmed evidence

### V1.7 executable
- File: Flipsky_ESC_Tool_V1.7_20261029.exe; 50,611,200 bytes.
- SHA-256: dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38.
- Native PE32 x86; no CLR/.NET header observed.
- Unusual .enigma1 and .enigma2 sections; protection/packing is plausible but the protector is not identified.

### Embedded metadata
- 13 embedded XML resources recovered and validated.
- 736 catalog rows, 222 unique parameter IDs and 13 profile/resource variants.
- Derived catalogs and XML resources are stored as gzip/base64 and restored with scripts/restore_payloads.py.

### Qt architecture and UART code paths
- Qt 5, C++/QML, QtSerialPort and QtBluetooth.
- FtescLowLevelFace is the high-level Qt façade.
- Separate uartPackData meta-object includes sendDataToESC, uartPackDataFromESC, uartPackDataHandle and uartPackDataTimerSl.
- Receive path: 0x00481030 → 0x0049CA30 → 0x0049C830.
- Transmit wrapper: 0x004819C0 → 0x0049C5C0.

### Outer frame and CRC
- Short: AA | LEN8 | INFO | CRC16_BE | DD.
- Extended: BB | LEN16_BE | INFO | CRC16_BE | DD.
- INFO is CMD + DATA; DLEN counts the entire INFO field.
- CRC-16/MODBUS over INFO only: reflected polynomial A001, init FFFF, xorout 0000, sent big-endian.
- V1.7 table bytes match generated CRC-16/MODBUS tables; check vector 123456789 returns 4B37.
- V1.7 constructor initializes maximum payload to 0x2710 (10,000 bytes).
- Receive handler distinguishes valid, malformed and incomplete candidates; invalid candidates advance one byte, valid consumed sizes advance the parser.

See WIRE_FRAME_FORMAT.md, RECEIVE_BUFFER_STATE.md, RECEIVE_PATH_DEEP_DIVE.md, QT_METACALL_DISPATCH_MAP.md, V1_7_RESPONSE_DISPATCH_MAP.md and V1_7_REQUEST_DISPATCH_MAP.md.

### Public V1.6 UART protocol reference
- V1.6 official UART protocol PDF read from Nextcloud: document date 2025-12-09, firmware version V1.6, 23 pages.
- V1.4 counterpart also read, enabling a documented comparison.
- V1.6 ECU-side C example preserved under reference/. It is a sample implementation, not Flipsky ESC Tool source code or firmware source.
- V1.6 adds periodic telemetry extension fields to CMD 00, changes CMD 02 UART request data ordering, and adds a PAS-mode alias for CMD 02.
- V1.6 specifies 17 principal command IDs: 00, 02-06, 10, 11, 19, 1A, 1D, 1E, 20, 23 and 25-27.
- V1.6 manual supplies product coverage, input mode and bootloader/update workflow context.

See FTESC_UART_PROTOCOL_V1.6.md, V1_4_TO_V1_6_PROTOCOL_CHANGES.md, V1_7_BINARY_CROSS_REFERENCE.md, V1.6_MANUAL_NOTES.md and NEXTCLOUD_SOURCE_INVENTORY.md.

### Offline implementation tests
- scripts/ftesc_frame.py: frame codec.
- scripts/ftesc_protocol.py: V1.6 command/telemetry helpers.
- tests/test_ftesc_frame.py, tests/test_ftesc_protocol.py and tests/test_ftesc_stream.py.
- Executed on REA against the published GitHub copies: **104 tests passed, 0 failed** (26 frame/protocol tests plus 10 incremental-stream tests).

## Open technical questions
- Map V1.7 outbound command builders and response handlers to numeric command IDs.
- Confirm V1.7's implementation of the V1.6 CMD 02 offset order and PAS alias.
- Trace CAN forwarding payloads and acknowledgements.
- Trace periodic telemetry 0x1A and keepalive 0x19 scheduling.
- Compare actual V1.6 Windows executables with V1.7 after staging a V1.6 build on REA.
- Determine BLE-specific framing separately from UART framing.
- Trace firmware-update block format and precise TEA usage.
- Validate across actual ESC hardware revisions only when a safe, isolated test setup is available.

## Tooling and safety
Rizin 0.9.1 and Ghidra 12.2 are already installed in REA. The three V1.6 Windows executables are inventoried in Nextcloud but are not yet on REA. No physical ESC has been tested and no firmware has been flashed. Do not treat software defaults or limits as safe operating recommendations; do not transmit unknown frames to a motor-connected ESC.


### V1.7 Qt API string map
- High-level Qt string/meta-object data exposes method names for duty, current, brake current, D-axis current, speed, position, auto-realtime data, CAN enumeration/identification and firmware update.
- A separate uartPackData string group confirms a distinct low-level framing helper.
- writeMcuEncrypt and encrypt_res names are present, but ordinary UART payload encryption remains unproven.
- These are API names and candidate opcode relationships, not confirmed command IDs. See V1_7_QT_API_STRING_MAP.md.


### V1.7 CAN target-state mapping
- UartComm fields at +0x0C and +0x10 hold CAN-forward enabled and target ID; accessors and setter are mapped.
- UI target selection/clear flows, ID discovery request 0x01, per-target setup reads 0x1C and TopFlow reads 0x3B are traced.
- The generic V1.7 CMD 0x10 wrapper insertion and slave response routing remain unresolved. See [CAN_FORWARDING_STATE.md](CAN_FORWARDING_STATE.md).


### V1.7 CMD 0x02 one-shot path
- The public V1.6 command layout is documented.
- No CMD 0x02 branch is present in the mapped V1.7 response dispatcher at 0x004997A0.
- No direct CMD 0x02 builder appears in the decoded UartComm request method table.
- UartComm signal index 13 `ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA)` exists, but a signal name is not proof of an outbound request.
- See [V1_7_ONE_SHOT_CMD_02_STATUS.md](V1_7_ONE_SHOT_CMD_02_STATUS.md); class/QML bridge tracing remains open.


### V1.7 firmware erase/write pipeline
- Corrected earlier function classification: `0x00485130` is the erase-and-block-write orchestrator, not an image validator.
- Confirmed erase CMD 0x16 carries 32-bit BE image size.
- Confirmed CMD 0x18 blocks are at most 240 bytes, XOR-masked with a per-block reset, retried up to 3 times on 2-second timeouts.
- Recovered the 239-byte XOR mask and implemented an offline-only block codec.
- The app's 150-Kbyte UI warning differs from its native 0x30F98-byte bound; exact intended limit remains unresolved.
- See [FIRMWARE_UPDATE_FLOW.md](FIRMWARE_UPDATE_FLOW.md).


### Exact setup serialization order recovered
- All 13 ValueSetups resources contain a `ValueSeque` list; its order differs from the `Values` order in all 13.
- Total: 736 Values entries, 721 ordered transmit entries, 15 omitted entries; no duplicate or unknown sequence IDs.
- Added `scripts/ftesc_profiles.py`, profile-aware serializer entry point, full compressed CSV/JSON order artifacts, summary JSON and tests.
- Omitted keys are recorded, not guessed. Product/hardware resource selection and conditional second-block selection remain open.
- See [V1_7_PROFILE_SERIALIZATION_ORDER.md](V1_7_PROFILE_SERIALIZATION_ORDER.md).


### CMD 0x00 / realtime-data signal correlation
- The CMD 0x00 response branch calls callback wrapper `0x004BC060`, corresponding to UartComm signal index 13 `ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA)`.
- This is response-side telemetry. It is not evidence of a CMD 0x02 outbound request.
- CMD 0x02 remains unresolved; see [V1_7_ONE_SHOT_CMD_02_STATUS.md](V1_7_ONE_SHOT_CMD_02_STATUS.md).


### V1.7 firmware configuration discovery
- `0x00488010` selects embedded V1.7 table paths for TopFlow vs Motor+Control setup.
- `0x00492570` scans firmware directories and reads MotorSetupValueTable_official.xml, ControlSetupValueTable.xml, TopFlowSetupValueTable.xml and FirmwareVersionInf.xml.
- It matches two parsed integer fields to its input parameters; their exact meaning and the resource-ID-to-SKU mapping remain unresolved.
- The 13 extracted resources classify as 4 control, 6 motor and 3 motor-signal/FOC variants.
- See [V1_7_FIRMWARE_CONFIG_DISCOVERY.md](V1_7_FIRMWARE_CONFIG_DISCOVERY.md).


### Firmware-version selector resolved
- Both call sites invoke `FUN_00492570(...,1,7)`.
- These are the firmware major/minor selectors for the `ftesc/1.7` directory; the loader compares them with `FirmwareVersionInf.xml`.
- Hardware/SKU mapping of the 13 ValueSetups resource IDs remains unresolved.


### V1.6 C reference cross-check
- Inspected the user's `ftesc_v1.4_1.5_1.6_uart_handle.c` source.
- Independently confirms AA/BB framing, CRC high/low order, DD terminator, CMD 0x00 base telemetry and command enum.
- Declares CMD 0x02 and CMD 0x10 but does not implement either outbound path in the sample; this corroborates the two open V1.7 gaps.
- See [V1_6_C_REFERENCE_CROSSCHECK.md](V1_6_C_REFERENCE_CROSSCHECK.md).


### V1.7 request payload builders
- Added offline builders for resolved scalar controls, auto telemetry, setup marker blocks, reset variants and no-data requests.
- Added exact marker/payload schema report; command 0x0F, 0x02 and UART CAN-forward 0x10 remain deliberately unimplemented because semantics/path are unresolved.
- 9 new request-builder tests; fresh clone now has 89 passing tests.
- See [V1_7_REQUEST_PAYLOAD_SCHEMAS.md](V1_7_REQUEST_PAYLOAD_SCHEMAS.md).


### CMD 0x0F payload and numeric rounding
- Implemented the exact CMD 0x0F INFO field order from x86 instruction-level evidence; semantic labels/units for the five API arguments remain unknown.
- Confirmed native scalar scaling helpers use round-half-away-from-zero; offline builders now have tie-case tests.
- Request-builder suite now covers CMD 0x0F.


### V1.7 response payload decoders
- Added offline decoders for CMD 0x0D PPM, 0x0E six-value ADC (mixed scales), 0x16/0x18/0x22 boolean ACKs, 0x1A no-data ACK and 0x29 nine-value IMU calibration.
- Corrected earlier response-map note: CMD 0x0E parses six values, not five.
- CMD 0x01 and 0x1E ID-list responses share the same vector decoder.
- 8 new tests; 99 passing tests on a fresh clone.
- See [V1_7_RESPONSE_DISPATCH_MAP.md](V1_7_RESPONSE_DISPATCH_MAP.md).


### UUID response
- CMD 0x21 response is copied to a QByteArray and emitted to the firmware-update preflight.
- Added raw UUID decoder that preserves response length; TEA preflight consumes a 16-byte key, while the native response branch does not visibly enforce that length.
- Fresh clone now has 100 passing tests.


### Setup response decoder
- Decompiled `FUN_004A10C0` marker validation and `FUN_004A0B70` per-value decode.
- Added inverse ValueSeque decoder supporting float32, scaled signed16/32, signed/unsigned byte, signed/unsigned16 and signed/unsigned32.
- Decoder supports sequential marker blocks via `next_offset`, including the optional second CMD 0x1B block.
- “Invalid SecretKey” is a fixed setup marker mismatch message, distinct from UUID/TEA firmware authorization.
- See [V1_7_SETUP_RESPONSE_DECODER.md](V1_7_SETUP_RESPONSE_DECODER.md).


### Reproducible CI and external cross-checks
- Added `.github/workflows/offline-checks.yml`: restore compressed artifacts, regenerate catalog/profile data, compare byte-for-byte, run unit tests and compileall.
- Initial catalog comparison found whitespace-normalization drift in the committed generated artifacts; regenerated the compressed CSV/JSON/ID catalog payloads using the current script.
- Re-ran the complete workflow-equivalent sequence on REA: all catalog/profile comparisons passed; **104 tests passed**; compileall passed.
- Verified repository visibility is public, default branch `main`, and write/admin permission is available.
- Added official FTESC Gateway USB-to-CAN passthrough context and official firmware update procedure cross-check.
