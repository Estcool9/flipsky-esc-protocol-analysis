# Analysis checkpoint — 2026-11-22

**Repository:** \`Estcool9/flipsky-esc-protocol-analysis\`  
**Overall estimated progress: 38%**  
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
| UART/Qt event and meta-object mapping | 80% |
| Outer frame and CRC reconstruction | 85% |
| Inner command IDs and payload layouts | 8% |
| Firmware update / TEA relationship | 55% |
| VESC compatibility assessment | 25% |
| Offline frame parser and tests | 70% (implementation added; execution still pending) |
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
