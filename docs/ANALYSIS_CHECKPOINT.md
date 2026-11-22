# Analysis checkpoint — 2026-11-22

**Repository:** \`Estcool9/flipsky-esc-protocol-analysis\`  
**Overall estimated progress: 58%**  
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
