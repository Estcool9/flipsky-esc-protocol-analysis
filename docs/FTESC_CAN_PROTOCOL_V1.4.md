# FTESC direct CAN protocol V1.4 — offline decoder

**Source:** `FLIPSKY FTESC CAN Protocol V1.4 English.pdf`  
**Document number:** FT-CM-CAN-20250423-04  
**Issue date:** 2025-04-23  
**Firmware version stated:** V1.4  
**Pages:** 22  
**Source location:** user-provided Nextcloud project, Flipsky ESC Tool V1.4 directory

This is the direct FTESC CAN-bus protocol. It is **not** the UART envelope and must not be conflated with UART INFO command IDs or the serial CMD 0x10 forwarding mechanism.

## 1. Physical and identifier format

The specification lists:
- CAN bitrates: 250, 500, 750 or 1000 kbit/s;
- extended 29-bit identifiers;
- data frames (RTR=0);
- DLC determined by payload length;
- big-endian multi-byte numeric fields.

The identifier diagram assigns:
- bits 0–7: CAN command ID;
- bits 8–15: ESC ID;
- bits 16–28: fixed/reserved prefix.

The documented pattern is interpreted as:

```text
29-bit extended ID
28..26    fixed 100
25..16    reserved zero
15..8     ESC ID
7..0      CAN command
```

Equivalently, the encoder uses `0x10000000 | (esc_id << 8) | command`. It rejects IDs outside 29 bits or with a different fixed/reserved prefix.

## 2. Command families

The following rows reflect the V1.4 C command enum and command sections. All scaling factors describe the wire representation only; they are not operating limits or recommendations.

### CRC-bearing commands

| ID | Operation | DATA layout before CRC |
|---:|---|---|
| `0x00` | Current with gear | signed int32 current ×100,000; gear byte |
| `0x01` | Brake current | signed int32 current ×100,000 |
| `0x02` | Duty with gear | signed int32 duty ×1,000,000; gear byte |
| `0x03` | Current percentage | signed int32 percentage ×100,000 |
| `0x04` | Current percentage with gear | signed int32 percentage ×100,000; gear byte |
| `0x05` | Brake-current percentage | signed int32 percentage ×100,000 |
| `0x0B` | Realtime data 0 | signed int24 motor current ×1,000; signed int24 battery current ×1,000 |
| `0x0C` | Realtime data 1 | signed int24 eRPM; signed int24 duty ×1,000 |
| `0x0D` | Realtime data 2 | signed int16 MOSFET temperature ×100; signed int16 motor temperature ×100; signed int16 battery voltage ×100 |
| `0x12` | eRPM with gear | signed int32 eRPM; gear byte |
| `0x13` | Position with gear | signed int32 position ×100,000; gear byte |
| `0x14` | D-axis current | signed int32 current ×100,000 |

Each CRC-bearing command appends the two-byte CRC after its data bytes, high byte then low byte. For command 0x14, the payload is **four current bytes + two CRC bytes**; there is no reserved/gear byte.

### Commands without an application CRC

| V1.4 C enum value | Section heading | Operation |
|---:|---:|---|
| `0x15` | `15H` | Current with gear |
| `0x16` | `16H` | Current percentage with gear |
| `0x17` | `17H` | Duty with gear |
| `0x18` | `18H` | eRPM with gear |
| `0x19` | `19H` | Position with gear |
| `0x1A` **or** `0x20` | section says `20H` | Brake current |
| `0x1B` **or** `0x21` | section says `21H` | Brake-current percentage |

The last two commands are internally inconsistent in the PDF: the C enum assigns decimal values 26 and 27 (hex `0x1A` and `0x1B`), while the section headings state `20H` and `21H` (hex `0x20` and `0x21`). The offline builder exposes both alternatives and requires an explicit `command_id`; it does not guess which ID the shipping firmware accepts.

## 3. CRC

The PDF supplies the CRC lookup-table implementation. The offline implementation uses the same CRC-16/MODBUS routine as the recovered FTESC UART protocol:
- reflected polynomial `0xA001`;
- initial value `0xFFFF`;
- CRC covers data bytes before the two-byte trailer;
- high byte then low byte.

For the periodic 8-byte telemetry messages, CRC covers the first six bytes and occupies bytes 6–7.

## 4. Periodic telemetry

The detailed sections 3.1.7–3.1.9 state that commands 0x0B, 0x0C and 0x0D are automatically emitted every 10 ms. The C enum comment elsewhere says 0x0B is emitted every 20 ms. The 0x0B cadence is therefore unresolved in this document.

### Command 0x0B — currents

| Data bytes | Field | Conversion |
|---|---|---|
| 0–2 | Motor current | signed 24-bit BE ÷1,000 A |
| 3–5 | Battery current | signed 24-bit BE ÷1,000 A |
| 6–7 | CRC16 | high byte, low byte |

The sample description uses “current percent” wording in one table, but the accompanying examples and code treat these values as motor and battery current.

### Command 0x0C — eRPM and duty

| Data bytes | Field | Conversion |
|---|---|---|
| 0–2 | Motor eRPM | signed 24-bit BE |
| 3–5 | Duty | signed 24-bit BE ÷1,000 |
| 6–7 | CRC16 | high byte, low byte |

### Command 0x0D — temperatures and voltage

| Data bytes | Field | Conversion |
|---|---|---|
| 0–1 | MOSFET temperature | signed 16-bit BE ÷100 °C |
| 2–3 | Motor temperature | signed 16-bit BE ÷100 °C |
| 4–5 | Battery voltage | signed 16-bit BE ÷100 V |
| 6–7 | CRC16 | high byte, low byte |

The 0x0D frame table has three 16-bit values, exactly fitting six data bytes plus the two-byte CRC. The example C parser later calls a 24-bit compose helper three times, which cannot fit this documented 8-byte frame. The offline decoder follows the frame table and records the sample-code inconsistency.

## 5. Control-command refresh note

The V1.4 document says relevant control commands should be refreshed at least every 450 ms or the command times out and becomes invalid. This is a protocol timing statement, not a recommendation to send motor-control commands during this analysis.

## 6. Offline implementation

The repository contains:
- `scripts/ftesc_can.py`: fixed 29-bit ID codec, generic CAN frame parser, CRC validation, read-only telemetry decoders for 0x0B/0x0C/0x0D, and offline encoders for documented CRC and non-CRC control commands;
- `tests/test_ftesc_can.py`: tests for ID prefix, ESC ID and command extraction, signed 24-bit telemetry, signed 16-bit telemetry, scaling, CRC, control payloads and malformed lengths.

The two ambiguous no-CRC brake command IDs require an explicit choice in the corresponding encoder function. The D-axis current encoder emits four bytes of current followed by the CRC. No CAN interface is opened and no frames are transmitted.

## 7. Relationship to UART and V1.7

Direct CAN uses 29-bit extended IDs and the direct-CAN command namespace. UART has its own `0xAA/0xBB` serial framing and UART INFO command namespace. For example:
- direct CAN command `0x00` is current-with-gear;
- UART INFO command `0x00` is realtime telemetry.

Never reuse numeric command IDs between the UART and direct-CAN layers.

V1.7 UI code maps selected CAN target state and setup-read workflows, but the exact native insertion point for the UART CAN-forward wrapper and slave-response routing remains unresolved. See [CAN_FORWARDING_STATE.md](CAN_FORWARDING_STATE.md).

## 8. Source and limitations

This digest was derived from the user's V1.4 CAN PDF. The original PDF is not duplicated in this repository. The C enum/section-heading mismatch for brake command IDs, the 0x0B telemetry cadence mismatch and the 0x0D sample-parser width inconsistency remain explicitly unresolved.

No physical CAN bus or ESC was connected during this work.
