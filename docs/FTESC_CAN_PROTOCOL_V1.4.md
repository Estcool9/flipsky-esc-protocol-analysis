# FTESC direct CAN protocol V1.4 — offline decoder

**Source:** `FLIPSKY FTESC CAN Protocol V1.4 English.pdf`  
**Document number:** FT-CM-CAN-20250423-04  
**Issue date:** 2025-04-23  
**Firmware version stated:** V1.4  
**Pages:** 22  
**Source location:** user-provided Nextcloud project, Flipsky ESC Tool V1.4 directory

This is the direct FTESC CAN-bus protocol. It is **not** the UART envelope and must not be conflated with UART command IDs or the serial CMD 0x10 forwarding mechanism.

## 1. Physical and identifier format

The specification lists:
- CAN bitrates: 250, 500, 750 or 1000 kbit/s;
- extended 29-bit identifiers;
- data frames (RTR=0);
- DLC determined by payload length;
- big-endian 16-bit and 32-bit numeric fields.

The identifier diagram assigns:
- bits 0–7: CAN command ID;
- bits 8–15: ESC ID;
- upper identifier bits: fixed protocol prefix/reserved bits.

The documented layout is interpreted by the decoder as:

```text
29-bit extended ID
31..29    not part of 29-bit identifier
28..26    fixed 100
25..16    reserved zero
15..8     ESC ID
7..0      CAN command
```

Equivalently, the encoded 29-bit value is `0x10000000 | (esc_id << 8) | command`. The decoder rejects identifiers outside 29 bits or with a different fixed/reserved prefix.

## 2. Command families

The V1.4 enum contains these command IDs:

| ID | Operation | Payload notes |
|---:|---|---|
| `0x00` | Current with gear, CRC | signed 32-bit current ×100,000; gear; CRC16 |
| `0x01` | Brake current, CRC | signed 32-bit current ×100,000; CRC16 |
| `0x02` | Duty with gear, CRC | signed 32-bit duty ×1,000,000; gear; CRC16 |
| `0x03` | Current percentage, CRC | signed 32-bit percentage ×100,000; CRC16 |
| `0x04` | Current percentage with gear, CRC | signed 32-bit percentage ×100,000; gear; CRC16 |
| `0x05` | Brake-current percentage, CRC | signed 32-bit percentage ×100,000; CRC16 |
| `0x0B` | Realtime data 0 | motor current, battery current, CRC16 |
| `0x0C` | Realtime data 1 | motor eRPM, duty, CRC16 |
| `0x0D` | Realtime data 2 | MOSFET temp, motor temp, battery voltage, CRC16 |
| `0x12` | eRPM with gear, CRC | eRPM; gear; CRC16 |
| `0x13` | Position with gear, CRC | position ×100,000; gear; CRC16 |
| `0x14` | D-axis current, CRC | signed 32-bit current ×100,000; reserved/gear byte; CRC16 |
| `0x15` | Current with gear | no CRC variant |
| `0x16` | Current percentage with gear | no CRC variant |
| `0x17` | Duty with gear | no CRC variant |
| `0x18` | eRPM with gear | no CRC variant |
| `0x19` | Position with gear | no CRC variant |
| `0x1A` | Brake current | no CRC variant |
| `0x1B` | Brake-current percentage | no CRC variant |

Control values and scale factors above describe the protocol encoding only. They are not operating limits or safe motor settings.

## 3. CRC

The PDF includes the same split-table CRC-16/MODBUS algorithm:
- reflected polynomial `0xA001`;
- initial value `0xFFFF`;
- CRC covers the CAN data bytes before the two-byte CRC trailer;
- high byte then low byte.

For the periodic 8-byte telemetry messages, CRC covers the first six bytes and occupies bytes 6–7.

## 4. Periodic telemetry

The ESC sends these messages automatically on the CAN bus every 10 ms, according to the V1.4 document.

### Command 0x0B — currents

| Data bytes | Field | Conversion |
|---|---|---|
| 0–2 | Motor current | signed 24-bit BE ÷1000 A |
| 3–5 | Battery current | signed 24-bit BE ÷1000 A |
| 6–7 | CRC16 | high byte, low byte |

### Command 0x0C — eRPM and duty

| Data bytes | Field | Conversion |
|---|---|---|
| 0–2 | Motor eRPM | signed 24-bit BE |
| 3–5 | Duty | signed 24-bit BE ÷1000 |
| 6–7 | CRC16 | high byte, low byte |

### Command 0x0D — temperatures and voltage

| Data bytes | Field | Conversion |
|---|---|---|
| 0–1 | MOSFET temperature | signed 16-bit BE ÷100 °C |
| 2–3 | Motor temperature | signed 16-bit BE ÷100 °C |
| 4–5 | Battery voltage | signed 16-bit BE ÷100 V |
| 6–7 | CRC16 | high byte, low byte |

The decoder uses signed 24-bit sign extension for the current and eRPM fields. The sample C helper in the PDF assembles 24-bit values into a 32-bit integer without an obvious sign-extension step; that sample-code detail is not copied as protocol semantics.

## 5. Control-command cadence

The V1.4 document says control commands should be refreshed at least every 450 ms or the command times out and becomes invalid. This is a protocol timing note, not a recommendation to send motor-control commands during this analysis.

## 6. Offline implementation

The repository now contains:
- `scripts/ftesc_can.py`: extended-ID decode/encode helpers, generic CAN frame parser, CRC validation for the documented CRC-bearing command ranges, and read-only telemetry decoding for 0x0B, 0x0C and 0x0D;
- `tests/test_ftesc_can.py`: tests for ID prefix, ESC ID and command extraction, signed 24-bit telemetry, scaling, CRC failure and malformed lengths.

The implementation does not open a CAN interface, transmit frames, or generate motor-control commands.

## 7. Relationship to UART and V1.7

The UART protocol has its own `0xAA/0xBB` serial framing and a UART-level CAN-forward command. The direct CAN protocol described here uses 29-bit extended CAN identifiers and a different command namespace. For example, direct CAN command `0x00` means current-with-gear, while UART INFO command `0x00` is realtime telemetry. Never reuse numeric command IDs between these layers.

V1.7 UI code maps CAN target selection and setup-read workflows, but the exact native insertion of the UART CAN-forward wrapper and slave response routing remain open. See [CAN_FORWARDING_STATE.md](CAN_FORWARDING_STATE.md).

## 8. Source and limitations

This digest was derived from the user's V1.4 CAN PDF. The full PDF is not duplicated in this repository. It is a public Flipsky protocol document, but the user's source copy remains the reference used here. The protocol is versioned V1.4; newer hardware/firmware revisions may differ.

No physical CAN bus or ESC was connected during this work.
