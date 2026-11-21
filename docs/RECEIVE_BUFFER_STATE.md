# uartPackData receive buffering and resynchronization

**Reference executable SHA-256:** \`dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38\`  
**Date:** 2026-11-22

## Call path and ownership

The Qt meta-object at the string-table region near \`0x00F24080\` identifies a helper object named \`uartPackData\`; its methods include \`sendDataToESC\`, \`uartPackDataFromESC\`, \`uartPackDataHandle\`, and \`uartPackDataTimerSl\`.

Receive path:

\`\`\`text
QSerialPort::readyRead()
  -> UartComm::uartDataHandleAvailable() [0x00481030]
     -> uartPackDataHandle()             [0x0049CA30]
        -> outer-frame parser            [0x0049C830]
\`\`\`

The call from \`0x0049CA30\` into \`0x0049C830\` is at \`0x0049CC8D\`.

## Parser result handling

The caller distinguishes three important return values:

| Return | Meaning supported by the code | Caller behaviour |
|---|---|---|
| Positive | Bytes consumed by a valid frame | Advance current offset by that size, decrement remaining-byte count, and loop again |
| \`-1\` (\`0xFFFFFFFF\`) | Invalid candidate frame | Advance candidate offset by one byte and decrement remaining input by one; continue scanning |
| \`-2\` (\`0xFFFFFFFE\`) | Incomplete candidate frame | Use a separate incomplete-input path rather than treating it as a completed frame |

Evidence:
- Parser call: \`0x0049CC8D\`.
- Compare against -2: \`0x0049CC95\`–\`0x0049CC98\`.
- Compare against -1 and one-byte advance: \`0x0049CCB0\`–\`0x0049CCBE\`.
- Positive consumed-length update: \`0x0049CC9A\`–\`0x0049CCA8\`.

The loop repeats after a positive return, demonstrating that more than one complete frame can be processed from a single larger input buffer.

## Buffer object initialization

The \`uartPackData\` constructor at \`0x0049C460\` initializes these fields:

| Offset | Initial value | Observation |
|---:|---:|---|
| \`+0x0C\` | \`0\` | State field |
| \`+0x10\` | \`0x32\` (50) | Semantic name not yet recovered |
| \`+0x14\` | \`0\` | Parse offset/state |
| \`+0x18\` | \`0\` | Parse progress/state |
| \`+0x1C\` | \`0\` | Additional parse state |
| \`+0x20\` | \`0x2710\` (10,000) | Maximum payload bound checked by parser |
| \`+0x24\` | \`0x2718\` (10,008) | Related buffer-size field |
| \`+0x28\` | Allocated pointer | Internal buffer storage |

These are raw structure offsets and initial values. Semantic names are only assigned where call-site usage supports them.

## Established vs. open

Established: receive ownership, handler-to-parser call, three result classes, one-byte resynchronization on -1, consumed-length advancement on success, and looping over concatenated frames.

Open: exact behaviour across every fragmented arrival boundary, reset policy after prolonged incomplete/error sequences, and whether BLE shares this exact buffer path. Do not infer retry or timeout guarantees from these findings.
