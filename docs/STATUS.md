# Project status

**Reference date:** 2026-11-22  
**Overall estimated progress: 40%** toward an evidenced protocol specification and independently testable offline client.

Percentages are milestone-weighted estimates, not measurements of certainty or commercial application feature completion.

## Workstream progress

| Workstream | Progress |
|---|---:|
| Binary inventory and integrity | 100% |
| Embedded XML extraction and validation | 100% |
| Parameter catalog generation | 100% |
| Qt/QML architecture and class ownership | 90% |
| UART/Qt event and meta-object mapping | 85% |
| Outer frame format and CRC reconstruction | 100% |
| Receive-buffer and resynchronization analysis | 70% |
| Inner command IDs and payload layouts | 8% |
| Firmware update and TEA relationship | 55% |
| VESC compatibility assessment | 25% |
| Offline frame codec and unit tests | 100% |
| Hardware validation | 0% |
| **Overall estimate** | **40%** |

## Confirmed evidence

### Executable
- \`Flipsky_ESC_Tool_V1.7_20261029.exe\`, 50,611,200 bytes.
- SHA-256: \`dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38\`.
- Native PE32 x86; no CLR/.NET header observed.
- Unusual \`.enigma1\` and \`.enigma2\` sections; protection/packing is plausible but the protector is not identified.

### Embedded metadata
- 13 embedded XML resources recovered and validated.
- 736 catalog rows, 222 unique parameter IDs and 13 profile/resource variants.
- Complete catalogs, manifest and XML payloads are published as gzip/base64. Restore with \`python scripts/restore_payloads.py --root .\`.

### Qt architecture
- Qt 5, C++/QML, QtSerialPort and QtBluetooth.
- \`FtescLowLevelFace\` is the high-level Qt façade.
- The separate \`uartPackData\` meta-object includes \`sendDataToESC\`, \`uartPackDataFromESC\`, \`uartPackDataHandle\`, and \`uartPackDataTimerSl\`.
- Receive path: \`0x00481030\` → \`0x0049CA30\` → \`0x0049C830\`.
- Transmit wrapper: \`0x004819C0\` → \`0x0049C5C0\`.

### Outer frame
- Short: \`AA | LEN8 | PAYLOAD | CRC16_BE | DD\`.
- Extended: \`BB | LEN16_BE | PAYLOAD | CRC16_BE | DD\`.
- CRC-16/MODBUS: reflected polynomial A001, init FFFF, xorout 0000, calculated over payload only, sent big-endian.
- Lookup tables at \`0x005310C0\` and \`0x005311C0\` match generated CRC-16/MODBUS tables; standard check vector \`123456789\` returns \`0x4B37\`.
- Constructor initializes max payload to \`0x2710\` (10,000 bytes).
- Receive handler distinguishes valid, malformed and incomplete candidates; invalid candidates advance one byte, and valid consumed sizes drive the parsing loop.

See [WIRE_FRAME_FORMAT.md](WIRE_FRAME_FORMAT.md) and [RECEIVE_BUFFER_STATE.md](RECEIVE_BUFFER_STATE.md).

### Offline codec tests
The standard-library-only Python codec is \`scripts/ftesc_frame.py\`; tests are in \`tests/test_ftesc_frame.py\`. They were executed on REA against the GitHub files:

**13 tests passed, 0 failed** with \`python3 -m unittest discover -s tests -v\`.

## Open technical questions
- Inner command IDs/opcodes and operation-specific payload layouts.
- Request/acknowledgement matching and CAN forwarding payload format.
- Firmware-update block semantics and exact TEA usage.
- BLE's exact outer framing.
- Whether normal UART payloads ever use TEA encryption.
- Compatibility across physical FT ESC hardware revisions.

## Tooling and safety
Rizin 0.9.1 and Ghidra 12.2 are already installed in REA. No extra static-analysis package is currently needed. No physical ESC has been tested and no firmware has been flashed. XML defaults and limits are not safe-tuning recommendations; unknown payloads must not be sent to a motor-connected controller.
