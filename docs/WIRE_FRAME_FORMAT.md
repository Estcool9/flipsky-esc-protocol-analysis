# Flipsky FT ESC outer UART frame format

**Reference:** \`Flipsky_ESC_Tool_V1.7_20261029.exe\`  
**SHA-256:** \`dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38\`  
**Analysis date:** 2026-11-22

The outer framing layer is now evidenced by both the receive parser and the transmit builder. Inner command/payload schemas remain a separate workstream.

## 1. Frame layouts

### Short frame (sender uses for 1–255 payload bytes)

| Offset | Size | Field | Encoding |
|---:|---:|---|---|
| 0 | 1 | Start | \`0xAA\` |
| 1 | 1 | Payload length | Unsigned byte |
| 2 | N | Payload | Opaque bytes at this layer |
| 2 + N | 2 | CRC-16 | Big-endian |
| 4 + N | 1 | Terminator | \`0xDD\` |

Total size: \`N + 5\` bytes.

### Extended frame (sender uses when payload length >255)

| Offset | Size | Field | Encoding |
|---:|---:|---|---|
| 0 | 1 | Start | \`0xBB\` |
| 1 | 2 | Payload length | Unsigned 16-bit big-endian |
| 3 | N | Payload | Opaque bytes at this layer |
| 3 + N | 2 | CRC-16 | Big-endian |
| 5 + N | 1 | Terminator | \`0xDD\` |

Total size: \`N + 6\` bytes.

The receiver rejects zero-length short payloads and rejects \`0xBB\` lengths <=254. The sender selects \`0xAA\` for 1–255 bytes and \`0xBB\` for lengths above 255. Thus, the receiver appears to accept a \`0xBB\` length of 255 even though the observed sender uses \`0xAA\` at that boundary.

The \`uartPackData\` constructor at VA \`0x0049C460\` initializes a maximum-payload field at \`this+0x20\` to \`0x2710\` (10,000 decimal). The parser compares received length against that field. This is the default bound observed in this binary, not a tuning recommendation or universal hardware limit.

## 2. CRC-16/MODBUS

The two 256-byte lookup tables at VAs \`0x005310C0\` and \`0x005311C0\` match the split lookup tables for reflected polynomial \`0xA001\`. They were compared byte-for-byte with generated tables.

| Parameter | Value |
|---|---|
| Width | 16 |
| Reflected polynomial | \`0xA001\` (normal polynomial \`0x8005\`) |
| Initial value | \`0xFFFF\` |
| RefIn / RefOut | true / true |
| XorOut | \`0x0000\` |
| Wire order | Big-endian, high byte first |
| Check vector | ASCII \`123456789\` → \`0x4B37\` |

The parser computes the CRC over the payload only, compares the result with the two bytes immediately following the payload, then checks the final \`0xDD\` byte.

## 3. Disassembly evidence

All VAs refer to the SHA-256-verified PE32 binary.

### Receive

- \`0x00481030\` is the callback mapped from \`uartDataHandleAvailable\`.
- It calls \`0x0049CA30\` at \`0x0048106C\`.
- \`0x0049CA30\` is the \`uartPackDataHandle\` path and calls outer-frame parser \`0x0049C830\` at \`0x0049CC8D\`.
- \`0x0049C830\` tests start byte \`0xAA\` or \`0xBB\` at \`0x0049C852\`–\`0x0049C85D\`.
- Short length is read from \`[buffer+1]\` at \`0x0049C9B4\`–\`0x0049C9C9\`; payload offset is 2.
- Extended length is read from word \`[buffer+1]\` and byte-swapped at \`0x0049C970\`–\`0x0049C99A\`; payload offset is 3.
- \`0xDD\` is checked at \`buffer + payload_offset + payload_length + 2\` (\`0x0049C893\`–\`0x0049C898\`).
- CRC covers the payload (\`0x0049C8AD\`–\`0x0049C8DB\`) and is compared with the big-endian trailer (\`0x0049C8E2\`–\`0x0049C8FC\`).

### Transmit

- Wrapper at \`0x004819C0\` jumps to builder \`0x0049C5C0\`.
- Payload length is compared with \`0xFF\` at \`0x0049C5E8\`.
- Short path appends \`0xAA\` and one length byte (\`0x0049C6C0\`–\`0x0049C6DE\`).
- Extended path appends \`0xBB\` and high then low length bytes (\`0x0049C725\`–\`0x0049C752\`).
- CRC high byte, CRC low byte and \`0xDD\` are appended in the common path (\`0x0049C646\`–\`0x0049C68D\`).

### CRC helpers / tables

- Buffer-oriented builder/helper: \`0x0049C5C0\`.
- Pointer-plus-length CRC helper: \`0x0049C7A0\`.
- Table addresses: \`0x005310C0\` and \`0x005311C0\`.
- Standard check vector: \`123456789\` → bytes \`4B 37\`.

## 4. Inner payload numeric byte order

The \`uartPackData\` numeric readers assemble multi-byte values in big-endian order:

- 16-bit reader at \`0x0049D3B0\` shifts the first byte left by 8 and ORs the next byte.
- 32-bit reader at \`0x0049D450\` places byte 0 at bits 31–24, byte 1 at 23–16, byte 2 at 15–8 and byte 3 at 7–0.
- An 8-bit reader is present at \`0x0049D330\`.

This applies to these helper routines; it does not prove every payload field uses them or lacks a special encoding.

## 5. Offline implementation

- \`scripts/ftesc_frame.py\`: encoder, single-frame decoder and concatenated-frame decoder.
- \`tests/test_ftesc_frame.py\`: CRC vector, short/extended frames, boundaries, corruption and truncated input.

Run tests:

\`\`\`bash
python -m unittest discover -s tests -v
\`\`\`

Example decode:

\`\`\`bash
python scripts/ftesc_frame.py "aa036f6b3ffd2edd"
\`\`\`

The example carries payload bytes \`6F 6B 3F\`.

## 6. Not yet established

- Inner command IDs/opcodes and operation-specific payloads.
- BLE-specific framing or an additional envelope.
- Whether ordinary UART payloads are encrypted or authenticated.
- Stream resynchronization after malformed bytes.
- Whether all hardware revisions share the same limit/framing.

The method named \`tea_encrypt\` exists in the Qt meta-object and its confirmed use is in the firmware-update path. Systematic encryption of ordinary UART payloads has not been demonstrated. No packet was sent to physical hardware.
