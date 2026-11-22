# V1.7 receive-path deep dive

**Artifact:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Provider:** Ghidra 12.2 through REA 6.10.1  
**Analysis date:** 2026-11-22

This note records a fresh decompilation of the parser, stream handler, transmit builder and CRC helper. The pseudocode is decompiler output, not vendor source.

## 1. Functions inspected

| VA | Recovered role | Evidence |
|---|---|---|
| `0x0049C830` | Parse one candidate outer frame | Complete Ghidra pseudocode |
| `0x0049CA30` | Append incoming bytes, maintain stream state, dispatch complete frames | Complete Ghidra pseudocode |
| `0x0049C5C0` | Build and append an outer frame around an existing payload | Complete Ghidra pseudocode |
| `0x0049C7A0` | CRC helper | Complete Ghidra pseudocode |
| `0x00481030` | UART ready-read callback | Previously mapped call path |

The target opened in REA/Ghidra and its SHA-256 matched the known V1.7 executable exactly.

## 2. Single-frame parser: `0x0049C830`

The function takes a candidate byte pointer, the number of available bytes and an output pointer used to report how many additional bytes are required.

Observed decision sequence:

1. Zero available bytes: return `-2` and request one more byte.
2. Start byte must be `0xAA` or `0xBB`; any other value returns `-1`.
3. For `0xAA`, require a two-byte header and a nonzero one-byte length.
4. For `0xBB`, require a three-byte header and decode a 16-bit big-endian length. The parser rejects lengths below 255; it therefore accepts 255 even though the observed sender chooses `0xAA` for 255.
5. Reject lengths above the object's configured maximum at `this+0x20` (default initialized value `0x2710`).
6. Require the complete candidate size: header + payload + two CRC bytes + one terminator.
7. Require terminator `0xDD`.
8. Compute CRC over payload bytes only, compare against the two-byte big-endian CRC trailer.
9. On success, pass the payload pointer and payload length to an indirect callback, then return the number of bytes consumed.

Return convention:

| Return | Meaning |
|---:|---|
| positive | Full frame consumed; value is header + payload + 3 trailer bytes |
| `-1` | Invalid candidate; caller may advance one byte and rescan |
| `-2` | Incomplete candidate; output parameter reports bytes still required |

For an incomplete short header, the parser reports the missing header byte count. For an incomplete frame body, it reports total expected candidate size minus currently available bytes.

## 3. Stream handler: `0x0049CA30`

The handler is not simply a call to the parser once per serial callback. It accumulates the incoming QByteArray **one byte at a time** into an internal receive buffer and evaluates the parser as enough bytes become available.

The following offsets are observed in the helper object. Names below are descriptive labels for the observed use, not recovered source-level field names.

| Object offset | Observed use |
|---:|---|
| `+0x14` | Current parse cursor / consumed prefix |
| `+0x18` | Receive-buffer used length |
| `+0x1C` | Remaining-byte countdown returned by the parser |
| `+0x20` | Maximum accepted payload; constructor default 10,000 |
| `+0x24` | Receive-buffer capacity / related allocation bound |
| `+0x28` | Receive-buffer pointer |

### 3.1 Incomplete-frame optimization

When the parser returns `-2`, it writes the number of additional bytes needed into `this+0x1C`.

On each subsequent input byte:
- if the countdown is at least 2, the handler decrements it and skips a full parser call;
- once it falls below 2, the handler tries the parser again.

This is a byte-countdown optimization: a large incomplete payload does not trigger a full CRC/frame parse after every individual byte.

### 3.2 Resynchronization

When the parser returns `-1`, the handler advances the parse cursor by exactly one byte and retries. This is a sliding resynchronization strategy, not a full-buffer reset.

When the parser returns a positive consumed length, the handler advances by that entire frame length and continues parsing. Therefore multiple concatenated frames in one input QByteArray can be consumed by the same handler pass.

When the current unconsumed region is exhausted, the observed code resets the parse cursor and used-length fields to zero.

### 3.3 Buffer compaction

Before appending a byte, the handler checks available space. If the unconsumed bytes would exceed the configured capacity, it moves the remaining unconsumed suffix to the beginning of the buffer and resets the parse cursor. The exact helper at `0x004C29B4` is used for this move.

This compaction is distinct from invalid-frame resynchronization: compaction preserves the unconsumed suffix, while an invalid candidate advances the cursor by one byte.

### 3.4 What remains unknown

- Exact semantic names and all lifecycle/reset rules for every object field.
- Whether the separate timer slot changes or clears the buffer after a timeout.
- Whether BLE feeds the same handler or a different framing path.
- Behaviour under every possible overflow/invalid-byte sequence has not yet been exercised against a live transport.
- No passive hardware capture is available to compare against this implementation.

## 4. Transmit builder: `0x0049C5C0`

The function receives an existing byte-array payload and appends an outer frame:

- Rejects an empty payload.
- Rejects a payload longer than the object's configured maximum.
- Uses `0xAA` plus one length byte when length is below `0x100` (1–255).
- Uses `0xBB` plus a 16-bit big-endian length when length is at least `0x100` and below `0x10000`.
- Calculates CRC over the payload bytes only.
- Appends CRC high byte, CRC low byte and `0xDD`.

The observed maximum of 10,000 means the builder's no-header path for lengths >=65,536 is outside the configured range.

## 5. CRC helper: `0x0049C7A0`

The helper initializes two CRC bytes to `0xFF`, processes each payload byte using the two lookup tables at `0x005310C0` and `0x005311C0`, and returns the two-byte result.

This independently supports CRC-16/MODBUS:
- reflected polynomial `0xA001`;
- initial value `0xFFFF`;
- xorout `0x0000`;
- payload-only coverage;
- big-endian serialization by the frame builder.

The helper returns `0xFFFFFFFF` for zero length; the builder rejects zero-length payloads before invoking the normal frame path, and the parser rejects empty short frames.

## 6. Stream-processing pseudocode

The following is a behavioural summary, not a source-code reproduction:

```text
for each byte in the serial input chunk:
    append byte to receive buffer
    if parser countdown >= 2:
        decrement countdown
        continue

    while a candidate can be evaluated:
        result = parse_one_frame(buffer + cursor)

        if result == NEED_MORE:
            countdown = parser_required_bytes
            break
        if result == INVALID:
            cursor += 1
            continue
        if result > 0:
            dispatch validated payload
            cursor += result
            continue

    if all buffered bytes were consumed:
        cursor = 0
        used_length = 0
```

## 7. Impact on the offline codec

The current offline codec correctly handles complete individual frames and concatenated complete frames. Its `decode_frames` API intentionally does not implement the application's byte-by-byte resynchronization policy and is not yet a streaming state machine.

The next software milestone is to add a separate `FrameStreamDecoder` with:
- incremental `feed(bytes)`;
- preservation of incomplete candidates across calls;
- one-byte recovery after invalid candidates;
- multiple-frame output from one call;
- bounded buffer growth using the observed maximum;
- explicit reset and diagnostic counters.

The streaming decoder should be tested with every possible split point of known frames, random chunk sizes, leading garbage, corrupted candidates, and concatenated valid frames. These are offline synthetic tests; they do not require hardware.

## 8. Safety and scope

All evidence here is static analysis of the V1.7 application. No bytes were sent to an ESC. The recovered frame builder is not a licence to transmit unknown commands; command payload meanings and device safety constraints remain separate workstreams.
