# Windows V1.6 UART frame builder and receive parser — static reconstruction

**Reference date:** 2026-11-22  
**Artifact:** `Flipsky_ESC_Tool_V1.6_20260912.exe`  
**SHA-256:** `051d57a776782ae8daaeaa45179f9b568f7e89b4a78ab8dd8e558ecd3e53b968`  
**Provider:** REA 6.10.1 / Ghidra 12.2, with Rizin 0.9.1 cross-check  
**Scope:** static inspection only; the executable was not launched.

## Reconstructed functions

| Function | Address | Role established by the decompilation |
|---|---:|---|
| `FUN_00496010` | `0x00496010` | Builds the outer AA/BB UART frame from an INFO QByteArray |
| `FUN_00496280` | `0x00496280` | Validates one frame candidate and distinguishes invalid vs incomplete input |
| `FUN_00496480` | `0x00496480` | Incremental stream/buffer handler; calls the candidate parser and dispatches valid INFO |
| `FUN_00481860` | `0x00481860` | Eight-byte tail-call wrapper to `FUN_00496010`; invoked from the Qt class dispatcher |
| `FUN_00480ED0` | `0x00480ED0` | Device-read loop feeding bytes to `FUN_00496480` |
| `FUN_00482750` | `0x00482750` | QByteArray-input wrapper feeding the same stream parser |
| `FUN_004B3300` | `0x004B3300` | Large Qt static-metacall-style dispatcher for `Flipsky.ftesc.FtescLowLevelFace` |

The same V1.6 build exposes the Qt metadata strings `Flipsky.ftesc.FtescLowLevelFace`, `uartDataHandleAvailable()`, `readyRead()`, `uartPackDataFromESC(QByteArray&)`, `uartCommSendToFtesc(QByteArray&)`, `bleDataRx(QByteArray)` and `dataRx(QByteArray)`. These strings are static class/method metadata, not proof of runtime transport behavior by themselves.

## Outer frame builder — `FUN_00496010`

The function receives a QByteArray-like INFO value, reads its byte length, checks the configured maximum held at the owning object's offset `+0x20`, and appends the outer frame components using Qt byte-array helper calls.

Observed branches:

- INFO length `1..255`: append `0xAA`, then one-byte length.
- INFO length `256..65535`: append `0xBB`, then the two-byte big-endian length.
- Compute CRC-16/MODBUS over the INFO bytes only, initialized to `0xFFFF`, using the two lookup tables at `0x0052A760` and `0x0052A660`.
- Append the CRC high byte followed by the low byte.
- Append terminal marker `0xDD`.

The public wire layout is therefore:

```text
AA | LEN8       | INFO... | CRC16_BE | DD
BB | LEN16_BE   | INFO... | CRC16_BE | DD
```

The short/extended split is at 255/256 bytes. The encoder chooses AA for exactly 255 bytes, while the parser also tolerates a BB frame carrying length 255. The native builder checks a per-instance maximum before constructing the frame. Its exact initial value in this V1.6 object is not yet tied to the constructor; do not infer it solely from the V1.7 default.

The common reference check remains `INFO=11 -> AA 01 11 4C 7F DD`, and the CRC check vector `123456789 -> 0x4B37`.

## Candidate parser — `FUN_00496280`

Recovered inputs are the candidate byte pointer, available byte count, and an output field used to report how many more bytes are needed. The decompilation shows three result classes:

- `-1`: invalid candidate (bad marker/length/limit/terminator/CRC).
- `-2`: incomplete candidate; the output field reports the remaining byte count.
- Non-negative: total frame size consumed after successful validation.

Validation order and rules:

1. Accept only marker `0xAA` or `0xBB`.
2. AA requires at least two header bytes and a non-zero one-byte INFO length.
3. BB requires at least three header bytes, decodes a big-endian 16-bit INFO length, and rejects lengths below 255. Thus BB/254 is invalid and BB/255 is accepted.
4. Reject payload lengths over the per-instance limit at `this+0x20`.
5. Require the complete header + INFO + two CRC bytes + one terminal byte.
6. Check the final `0xDD` byte first.
7. Recompute CRC-16/MODBUS over INFO alone and compare the two wire bytes in big-endian order.
8. Only after successful validation, pass the INFO pointer/length to the downstream byte-array/dispatch helper and return total frame length.

The parser therefore distinguishes incomplete input from malformed frames; it does not treat truncation as a CRC failure.

## Incremental receive path — `FUN_00496480`

This routine accumulates incoming bytes in the owning object's buffer and maintains separate read/write/length/state fields. When enough bytes are available it calls `FUN_00496280`.

The recovered control flow is consistent with the expected stream behavior:

- Keep partial candidates buffered when the candidate parser returns `-2`.
- On an invalid candidate (`-1`), advance by one byte and retry, enabling resynchronization at the next AA/BB marker.
- On a valid candidate, dispatch the INFO payload and consume the complete frame.
- Compact/shift the buffer when required and continue across concatenated frames.

The device-read wrapper `FUN_00480ED0` interrogates a QIODevice-like object stored at `this+0x3c`, reads available bytes and feeds `FUN_00496480` in a loop. This is the serial/device ingress path.

The direct QByteArray wrapper `FUN_00482750` also calls `FUN_00496480`. The Qt string table contains the connection names `1bleDataRx(QByteArray)` and `2dataRx(QByteArray)`; this is consistent with the application forwarding a BLE QByteArray through the same parser. The exact Qt method-index-to-string association still needs a raw QMetaObject table cross-check before treating the method label as fully proven.

## Qt dispatcher and relation to V1.7

`FUN_004B3300` has the shape of a Qt static metacall dispatcher and references the static meta-object data at `0x00519218`. In its invocation branch:

- case `0x0C` calls `FUN_00480ED0` (device read loop);
- case `0x10` calls `FUN_00481860`, which tail-jumps to the frame builder `FUN_00496010`;
- case `0x17` calls `FUN_00482750`, the direct QByteArray wrapper to the same stream parser.

This connects the frame builder and both receive wrappers to the `FtescLowLevelFace` Qt dispatcher without requiring the high-level QML code to be executed.

The equivalent V1.7 functions already documented in [V1_7_BINARY_CROSS_REFERENCE.md](V1_7_BINARY_CROSS_REFERENCE.md) are:

| V1.6 PE 2026-09-12 | V1.7 PE 2026-10-29 | Role |
|---:|---:|---|
| `0x00496010` | `0x0049C5C0` | Frame builder |
| `0x00496280` | `0x0049C830` | Candidate frame parser |
| `0x00496480` | `0x0049CA30` | Incremental receive/stream handler |

The matching function roles, framing markers, length rules, CRC lookup-table pattern and stream handling strongly support continuity of the AA/BB UART transport from Windows V1.6 to V1.7. This is a static behavioral comparison; it is not a byte-for-byte function diff and does not establish live serial/BLE behavior.

## Python implementation parity

The repository's offline implementation already covered the recovered wire rules:

- `scripts/ftesc_frame.py`: AA/BB headers, one-/two-byte big-endian lengths, zero/BB-254 rejection, BB-255 tolerance, CRC-16/MODBUS, big-endian CRC bytes, DD terminator and configured max payload.
- `scripts/ftesc_stream.py`: incomplete candidate retention, one-byte resynchronization, fragmented/concatenated input handling and stream statistics.
- Existing tests already covered the public AA frame vector, CRC check vector, AA/BB length boundaries, corruption, terminator, fragmentation and resynchronization.

One small behavioral difference was found in error precedence for a candidate with *both* a bad CRC and a bad terminal byte: the V1.6 parser checks `0xDD` before computing CRC, while the Python decoder previously checked CRC first. The decoder now matches native order and a regression test pins this precedence. This does not change acceptance of valid frames.

## Remaining work

1. Map the V1.6 Qt static-metacall method indices to the raw QMetaObject string/method table for exact naming of `dataRx`, `bleDataRx` and `uartDataHandleAvailable`.
2. Confirm the V1.6 per-instance max payload initialization stored at `this+0x20`.
3. Continue tracing validated INFO payload dispatch into UartComm responses and Qt signals.
4. Resolve the protected Windows BLE write call path separately; Android V1.6 static analysis is stronger than the current Windows PE write-path evidence.
5. Do not claim a live transport implementation or hardware validation from static PE analysis.

## Safety

All operations were static inspection of immutable PE files. No Flipsky binary was executed, no controller was connected, no UART/CAN/BLE command was sent and no firmware was flashed.
