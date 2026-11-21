# Project status

**Reference date:** 2026-11-22  
**Overall estimated progress: 46%** toward an evidenced protocol specification and independently testable offline client.

Percentages are milestone-weighted estimates, not measurements of certainty or commercial application feature completion.

## Workstream progress

| Workstream | Progress |
|---|---:|
| Binary inventory and integrity (V1.7) | 100% |
| Embedded XML extraction and validation | 100% |
| Parameter catalog generation | 100% |
| Qt/QML architecture and class ownership | 90% |
| UART/Qt event and meta-object mapping | 85% |
| Outer frame format and CRC reconstruction | 100% |
| Receive-buffer and resynchronization analysis | 70% |
| Public V1.6 UART protocol extraction | 100% |
| V1.4-to-V1.6 protocol comparison | 90% |
| V1.7 command-ID and payload cross-reference | 12% |
| Offline frame and protocol codecs/tests | 100% |
| Firmware update and TEA relationship | 55% |
| VESC compatibility assessment | 25% |
| V1.6 executable binary comparison | 0% |
| Hardware validation | 0% |
| **Overall estimate** | **46%** |

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

See WIRE_FRAME_FORMAT.md and RECEIVE_BUFFER_STATE.md.

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
- tests/test_ftesc_frame.py and tests/test_ftesc_protocol.py.
- Executed on REA against the published GitHub copies: **26 tests passed, 0 failed**.

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
