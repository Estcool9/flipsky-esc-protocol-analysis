# Progress log

## 2026-11-25 — V1.6 CMD 0x10 CAN-forward wrapper confirmed in TX helper

**Binary:** V1.6 2026-09-12 (`051d57a7…`), Ghidra 12.2 via REA 6.10.1, checkpoint active.

### Facts (DIRECT CODE EVIDENCE)

- `FUN_00492ab0` decompiled fully (REA evidence `ev_9407521b152a83ed0c9eb9e261cdfff4faea8a455c2c11d9a5c1fbe5020ed0ca`).
- **UartComm `+0x0C`** = CAN-forward enable flag (byte, non-zero = active). Confirmed by pseudocode branch `if (*(char *)(in_ECX + 0x0C) != '\0')`.
- **UartComm `+0x10`** = CAN slave target ID (byte/char). Confirmed by `PTR_FUN_00c53314((int)*(char *)(in_ECX + 0x10))`.
- When canForward is active, the UUID helper pointer `PTR_FUN_00c53314` is called twice: once with the slave ID, once with the literal `0x10`. This is the **inline CMD 0x10 wrapper insertion** mechanism in V1.6.
- After the CAN wrapper calls, the standard UART frame builder (`PTR_FUN_00c535b0(param_1)`) is called with the original payload.
- String `"Sending to ESC:"` is embedded in this function (confirmed via pseudocode).
- Function has 25 callers, 11 direct callees, 14 computed call sites. Callees include `0x4b55f0` (cleanup) and 10 functions in the `0x854f08–0x856b18` range (Enigma/Qt virtual).

### Hypotheses

- The two calls to `PTR_FUN_00c53314` with `slave_id` then `0x10` likely build the prefix `[0x10][slave_id]` before the actual payload bytes, matching the public FTESC V1.6 UART protocol CMD 0x10 format (`CMD | CAN_ID | nested_payload`). This is a STRONG INFERENCE based on the argument order and the known protocol spec; the exact byte sequence is not directly readable from the Enigma-protected helper.

### Unknowns

- Exact byte-level output of `PTR_FUN_00c53314` (Enigma-protected, 1-byte Ghidra body, unresolvable statically).
- Whether V1.7 performs CMD 0x10 insertion through a path not yet traced (separate signal, BLE path, or gateway-specific slot).
- Slave response routing in both V1.6 and V1.7.

### Architectural difference V1.6 vs V1.7 (CONFIRMED)

- V1.6 `FUN_00492ab0`: inserts CMD 0x10 wrapper inline **before** calling the frame builder.
- V1.7 `FUN_00495910`: passes QByteArray unmodified to the frame builder signal. No CMD 0x10 insertion observed in the normal transmit chain.

### Progress update

- CAN/gateway workstream: **65%** (up from 60%). The V1.6 insertion mechanism is now confirmed. V1.7 alternate path and slave response routing remain.
- Overall weighted estimate: **73%** (up from 72%).

### Commits

- `7464055983d5de47cf25ea54f1e884b118c0e2fe` — `docs/CAN_FORWARDING_STATE.md` updated with V1.6 TX helper analysis.
- `6e4c3673133cca4176134c3769a3b911ce857175` — `docs/ANALYSIS_CHECKPOINT.md` updated.

---

## 2026-11-22 — Project baseline

- Identified the Windows executable as PE32 x86, native, with no CLR/.NET header.
- Verified its SHA-256: `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`.
- Observed unusual `.enigma1` and `.enigma2` sections; a protected/packed build is plausible, but the exact protector is not confirmed.
- Recovered and validated 13 Zlib-compressed XML resources.
- Built a reproducible catalog with 736 profile rows, 222 unique parameter IDs and 13 profile/resource variants.
- Identified Qt 5, C++, QML, QtSerialPort and QtBluetooth components.
- Mapped the first UART signal/slot connections in the FtescLowLevelFace initialization path.
- Published the project reports, analysis scripts, catalogs and all 13 extracted XML resources to GitHub. Larger text files are stored as gzip/base64 payloads; [the restoration guide](PAYLOAD_FORMAT.md) explains how to reconstruct them.
