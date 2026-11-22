# Flipsky VESC UART/CAN Protocol V1.0 — analysis of the user's source PDFs

**Analysis date:** 2026-11-22  
**Source folder:** user-provided Nextcloud folder `/Projet Perso/Revolt-Engine/Software/VESC Protocol`  
**Scope:** Flipsky's VESC-based FSESC family, not the non-VESC FTESC family.

## 1. Source inventory

The folder contains four Flipsky documents, two languages for each bus:

| File | Document number | Version / target firmware | Issue date | Cover page metadata |
|---|---|---|---|---|
| `VESC UART Protocol V1.0.pdf` | `VESC-CM-UART-20250331-01` | V1.0 / VESC FW V3.00+ | 2025-04-15 | Public, 17 pages |
| `VESC UART 协议 V1.0.pdf` | `VESC-CM-UART-20250331-01` | V1.0 / VESC FW V3.00+ | 2025-04-15 | Public, 17 pages |
| `VESC CAN Protocol V1.0.pdf` | `VESC-CM-CAN-20250331-01` | V1.0 / VESC FW V3.00+ | 2025-04-15 | Public, 12 pages |
| `VESC CAN 协议 V1.0.pdf` | `VESC-CM-CAN-20250331-01` | V1.0 / VESC FW V3.00+ | 2025-04-15 | Public, cover says 17 pages |

The English and Chinese covers identify Guangdong FLIPSKY Technology Co., Ltd. and mark the documents Public. The PDFs were read through the connected Nextcloud file reader and their cover pages visually inspected. The documents themselves are not copied into this repository; this digest records protocol facts and source identifiers.

**Editorial issues observed:**
- The English UART table of contents contains stale FTESC-style entries such as `UART_OBTAIN_DATA_ONCE(00H)`, but the body and command enum define VESC `COMM_FW_VERSION(00H)`, `COMM_GET_VALUES(04H)`, and VESC command names. Use the body/enum and the VESC primary source, not that stale TOC.
- The English CAN cover states 12 pages, while the Chinese CAN cover states 17 pages, despite matching document number/date and largely matching protocol content. This is a document presentation discrepancy, not a wire-protocol version difference.
- The CAN identifier prose is ambiguous about the bit naming/order. The C example in the PDF and the matching VESC firmware source settle the implemented mapping: controller/node ID is in bits 0..7 and CAN command ID in bits 8..15. Do not implement the contradictory phrase literally.

## 2. Flipsky VESC UART V1.0

### Link layer

| Field | Documented value |
|---|---|
| Default baud rate | 115200 bit/s; configurable in VESC Tool App Settings |
| Serial format | 8 data bits, 1 stop bit, no parity |
| Flow control | None |
| Duplex | Half or full duplex |
| Integer byte order | Big-endian |
| Start / length modes | `0x02`, `0x03`, `0x04` |
| End marker | `0x03` |
| CRC | CRC16 over INFO = command byte + DATA, high byte first |

Frame formats:

```text
Short:   02 | LEN8       | INFO | CRC16_BE | 03
Medium:  03 | LEN16_BE   | INFO | CRC16_BE | 03
Long:    04 | LEN24_BE   | INFO | CRC16_BE | 03
```

`LEN` counts INFO bytes, including the command byte. The document specifies short form through 255 bytes, medium form through 65,535 bytes, and long form above that. The example ECU sender only illustrates the short and medium forms; VESC Tool's current `Packet::sendPacket()` implementation handles the long form too.

The CRC table and C routine define the non-reflected `0x1021` CRC with initial value zero and no final XOR. This is commonly called CRC-16/XMODEM. The CRC covers INFO only and is sent high byte then low byte. Reference vectors:
- CRC of `04` = `0x4084`;
- CRC of ASCII `123456789` = `0x31C3`;
- GET_VALUES request: `02 01 04 40 84 03`.

### UART command namespace

The document's command enum and body use:

| ID | VESC command | Meaning |
|---:|---|---|
| `0x00` | `COMM_FW_VERSION` | Firmware version / hardware identity query |
| `0x04` | `COMM_GET_VALUES` | One-shot realtime telemetry query |
| `0x05` | `COMM_SET_DUTY` | Duty command |
| `0x06` | `COMM_SET_CURRENT` | Motor current |
| `0x07` | `COMM_SET_CURRENT_BRAKE` | Brake current |
| `0x08` | `COMM_SET_RPM` | eRPM |
| `0x09` | `COMM_SET_POS` | Position |
| `0x0A` | `COMM_SET_HANDBRAKE` | Handbrake current |
| `0x1D` | `COMM_REBOOT` | Reboot |
| `0x1E` | `COMM_ALIVE` | Keepalive |
| `0x22` | `COMM_FORWARD_CAN` | Forward an inner command to a CAN slave |
| `0x23` | `COMM_SET_CHUCK_DATA` | Chuck/remote data |

The document states that control requests such as duty/current/RPM are no-response commands. Its keepalive section says to send `COMM_ALIVE` at regular intervals after control commands or the control request expires; the timeout is configurable in VESC Tool.

For VESC firmware V3.00 specifically, the manual defines a fixed 74-byte (`0x4A`) GET_VALUES response payload. It explicitly warns that the firmware-version response layout is for V3.00 hardware and later firmware requires the corresponding `commands.c` source. This repository therefore does not claim that the V3.00 telemetry layout covers every modern VESC firmware revision.

### UART-to-CAN forwarding

The Flipsky document describes the following envelope inside INFO:

```text
22 | SlaveID | SlaveCMD | SlaveDATA...
```

VESC Tool source independently corroborates the wrapper: `Commands::emitData()` prepends `COMM_FORWARD_CAN` (0x22) and then the selected `mCanId` when CAN forwarding is enabled. This is an application-level UART wrapper, distinct from a direct CAN frame.

## 3. Flipsky VESC direct CAN V1.0

### Bus and frame facts

- CAN bitrates listed: 10, 20, 50, 75, 100, 125, 250, 500 and 1000 kbit/s.
- Extended 29-bit identifiers.
- Data frames (not remote frames).
- DLC follows the actual payload length; classic CAN data is at most 8 bytes.
- Multi-byte integers are big-endian.
- The period of automatically emitted status packets is configured through the VESC CAN status settings.

### Extended identifier mapping

The manual's C example constructs IDs as:

```c
controller_id | ((uint32_t)CAN_PACKET_ID << 8)
```

The pinned VESC firmware `comm/comm_can.c` uses the same expression. The resulting implemented bit layout is:

```text
bits 0..7   = controller / ESC ID
bits 8..15  = CAN_PACKET command ID
bits 16..28 = reserved / zero in the documented basic commands
```

The PDF prose describing "CAN ID" and "ESC ID" is less clear than its code. The code expression and the primary firmware source are treated as authoritative for this implementation. The Python parser preserves bits 16..28 as a reserved field rather than silently discarding them.

### Main direct-CAN command IDs

| ID | VESC CAN command |
|---:|---|
| `0x00` | `CAN_PACKET_SET_DUTY` |
| `0x01` | `CAN_PACKET_SET_CURRENT` |
| `0x02` | `CAN_PACKET_SET_CURRENT_BRAKE` |
| `0x03` | `CAN_PACKET_SET_RPM` |
| `0x04` | `CAN_PACKET_SET_POS` |
| `0x09` | `CAN_PACKET_STATUS` |
| `0x0A` | `CAN_PACKET_SET_CURRENT_REL` |
| `0x0B` | `CAN_PACKET_SET_CURRENT_BRAKE_REL` |
| `0x0C` | `CAN_PACKET_SET_CURRENT_HANDBRAKE` |
| `0x0D` | `CAN_PACKET_SET_CURRENT_HANDBRAKE_REL` |
| `0x0E` | `CAN_PACKET_STATUS_2` |
| `0x0F` | `CAN_PACKET_STATUS_3` |
| `0x10` | `CAN_PACKET_STATUS_4` |
| `0x1B` | `CAN_PACKET_STATUS_5` |

Basic control messages use a four-byte big-endian signed value in the V1.0 examples:
- duty × 100,000;
- current × 1,000;
- brake current × 1,000;
- eRPM as signed 32-bit integer;
- position in degrees × 1,000,000.

The VESC firmware source confirms these scales for the basic command encoders. The VESC CAN codec in this repository is offline-only; it does not open a CAN interface or send frames.

## 4. Cross-check against upstream VESC source

The same source-pinned VESC snapshot already used in [VESC_COMPARISON.md](VESC_COMPARISON.md) was rechecked against these newly supplied Flipsky PDFs:

- VESC Tool commit [`04614bf50909b78f23716af694bf19ab9745e7df`](https://github.com/vedderb/vesc_tool/commit/04614bf50909b78f23716af694bf19ab9745e7df):
  - `packet.cpp`: 02/03/04 UART markers, VESC CRC table, init zero, INFO checksum, big-endian CRC and ETX 03;
  - `datatypes.h`: UART command IDs, including 00, 04-0A, 1D, 1E, 22 and 23;
  - `commands.cpp`: `COMM_FORWARD_CAN` plus target-ID insertion in `Commands::emitData()`.
- VESC firmware commit [`6fda11c299a475d5e6a6d1c5f5efd2539643d70b`](https://github.com/vedderb/bldc/commit/6fda11c299a475d5e6a6d1c5f5efd2539643d70b):
  - `datatypes.h`: direct-CAN command enumeration;
  - `comm/comm_can.c`: `controller_id | (CAN_PACKET_ID << 8)` and control scales.

The VESC Tool repository declares GPL-3.0. The new Python VESC codec is an independent implementation of documented wire formats and constants; no VESC source file or source-code body was copied into this repository. Any future reuse of VESC Tool source itself must be reviewed for GPL compliance and attribution.

## 5. VESC vs FTESC: do not merge protocol profiles

| Layer | Flipsky VESC / FSESC V1.0 | FTESC V1.7 / FTESC V1.4-1.6 references |
|---|---|---|
| UART start | `02/03/04` | `AA/BB` |
| UART end | `03` | `DD` |
| UART CRC | `0x1021`, init 0, non-reflected | CRC-16/MODBUS `0xA001`, init `0xFFFF` |
| UART telemetry request | `0x04` | `0x00` |
| UART duty | `0x05` | `0x03` |
| UART current | `0x06` | `0x04` |
| UART brake current | `0x07` | `0x06` |
| UART forward-CAN | `0x22` | `0x10` in public FTESC V1.6 protocol |
| Direct-CAN ID | controller ID low byte, command next byte | fixed prefix `0x10000000`, ESC ID bits 8..15 and command low byte |
| Direct CAN payload | basic VESC frames without an extra application CRC | FTESC V1.4 command payloads frequently carry application CRC16 |
| Config model | VESC configuration structures / command family | FTESC `ValueSetups`, `ValueSeque` and marker blocks |
| Programming tool | VESC Tool | Flipsky ESC Tool |

The numeric collision is significant: VESC UART `0x04` requests telemetry, whereas FTESC V1.7 UART `0x04` is current control. VESC `0x00` requests firmware version, whereas FTESC V1.7 `0x00` requests realtime telemetry.

Flipsky's official [Differences Between FT ESC and FSESC](https://flipsky.net/blogs/vesc-tool/differences-between-ft-esc-and-fsesc) article identifies FT ESC as NON-VESC and FSESC as VESC-based and says their programming tools are not interchangeable. Its 20 November 2026 [CAN Gateway explainer](https://flipsky.net/blogs/vesc-tool/what-is-a-can-gateway) also describes separate FSESC/VESC and FTESC gateways.

## 6. Open-source implementation boundary

This repository now has separate offline modules:
- `scripts/ftesc_frame.py`, `ftesc_protocol.py`, `ftesc_can.py` for FTESC;
- `scripts/vesc_uart.py`, `scripts/vesc_can.py` for Flipsky VESC V1.0 wire framing and basic direct-CAN identifiers/commands.

The modules intentionally do not share CRC, command IDs or frame markers. A future UI should require an explicit controller/protocol profile (for example `FTESC V1.7` or `Flipsky VESC V3.x`) and should never auto-detect a protocol from the Flipsky brand name alone.

No serial, BLE or CAN device was opened; no command was transmitted and no firmware was updated.
