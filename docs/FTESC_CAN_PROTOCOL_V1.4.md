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
| `0x1A` / `0x20` | Brake current | Conflict in V1.4 PDF: C enum assigns decimal 26 (`0x1A`), but section heading says `20H` (`0x20`) |
| `0x1B` / `0x21` | Brake-current percentage | Conflict in V1.4 PDF: C enum assigns decimal 27 (`0x1B`), but section heading says `21H` (`0x21`) |

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

The decoder uses signed 24-bit sign extension for current and eRPM fields. For command 0x0D, the PDF frame table specifies three signed 16-bit values (six data bytes plus two CRC bytes), while the sample C parser appears to call a 24-bit compose helper three times. Three 24-bit values cannot fit in the documented 8-byte CAN frame with a two-byte CRC. The implementation follows the frame table and records the sample-code inconsistency.

## 5. Control-command cadence

The V1.4 document says control commands should be refreshed at least every 450 ms or the command times out and becomes invalid. This is a protocol timing note, not a recommendation to send motor-control commands during this analysis.

## 6. Offline implementation

The repository now contains:
- `scripts/ftesc_can.py`: fixed 29-bit ID codec, generic CAN frame parser, CRC validation, read-only telemetry decoders for 0x0B/0x0C/0x0D, and offline encoders for all documented CRC and no-CRC control command families;
- `tests/test_ftesc_can.py`: tests for ID prefix, ESC ID and command extraction, signed 24-bit telemetry, scaling, CRC failure, control command payloads and malformed lengths.

The implementation does not open a CAN interface or transmit frames. The command builders only produce offline byte structures; they do not apply safety limits or select operating values. V1.4 float-to-integer scaling uses truncation toward zero to match the sample C conversion behavior. The D-axis current command encodes only the 4-byte signed current before the 2-byte CRC. For the two no-CRC brake commands, the builder requires an explicit `command_id` choice because the PDF's C enum values and section headings disagree.

## 7. Relationship to UART and V1.7

The UART protocol has its own `0xAA/0xBB` serial framing and a UART-level CAN-forward command. The direct CAN protocol described here uses 29-bit extended CAN identifiers and a different command namespace. For example, direct CAN command `0x00` means current-with-gear, while UART INFO command `0x00` is realtime telemetry. Never reuse numeric command IDs between these layers.

V1.7 UI code maps CAN target selection and setup-read workflows, but the exact native insertion of the UART CAN-forward wrapper and slave response routing remain open. See [CAN_FORWARDING_STATE.md](CAN_FORWARDING_STATE.md).

## 8. Source and limitations

This digest was derived from the user's V1.4 CAN PDF. The full PDF is not duplicated in this repository. It is a public Flipsky protocol document, but the user's source copy remains the reference used here. The protocol is versioned V1.4; newer hardware/firmware revisions may differ.

No physical CAN bus or ESC was connected during this work.


## 9. PDF inconsistencies retained as explicit variants

The V1.4 PDF is not internally consistent for the two no-CRC braking command IDs:
- C enum: `CAN_SET_CURRENT_BRAKE=26`, `CAN_SET_CURRENT_BRAKE_PERCENT=27` (decimal literals; therefore `0x1A` and `0x1B`);
- section headings: `CAN_SET_CURRENT_BRAKE(20H)` and `CAN_SET_CURRENT_BRAKE_PERCENT(21H)` (therefore `0x20` and `0x21`).

The offline builder exposes both variants and requires an explicit command ID. It does not decide which is used by the shipping firmware. An authoritative corrected PDF, firmware source or live capture is required to resolve this.

The V1.4 PDF's CMD 0x14 D-axis-current frame contains four current bytes and two CRC bytes. There is no reserved/gear byte. The encoder and tests now follow that six-byte data length.
