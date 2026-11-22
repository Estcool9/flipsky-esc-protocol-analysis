# V1.4–V1.6 C reference cross-check against V1.7

**Source inspected:** `ftesc_v1.4_1.5_1.6_uart_handle.c` (12,314 bytes, user-provided Nextcloud source)  
**Related document:** [FTESC UART Protocol V1.6](FTESC_UART_PROTOCOL_V1.6.md)  
**Analysis date:** 2026-11-22

The C file is treated as a versioned reference implementation. It is not copied into this public repository; this report records the protocol facts needed to cross-check the V1.7 binary.

## 1. Command enum cross-check

The C enum assigns:

| ID | C enum name | Operation |
|---:|---|---|
| `0x00` | `UART_OBTAIN_DATA_ONCE` | Obtain realtime data once |
| `0x02` | `UART_CONTROL_AND_OBTAIN_DATA_ONCE` | Control and obtain realtime data once |
| `0x03` | `UART_SET_DUTY` | Set duty |
| `0x04` | `UART_SET_CURRENT` | Set current |
| `0x05` | `UART_SET_CURRENT_GEAR` | Set current with gear |
| `0x06` | `UART_SET_BRAKE_CURRENT` | Set brake current |
| `0x10` | `UART_CAN_FWARD` | UART-level CAN forwarding |
| `0x11` | `UART_OBTAIN_FIRMWARE_VERSION` | Obtain firmware version |
| `0x19` | `UART_KEEP_LIVE` | Keepalive |
| `0x1A` | `UART_SET_AUTO_OBTAIN_REALTIME_DATA` | Configure automatic telemetry |
| `0x1D` | `UART_RESET_AND_REBOOT_FTESC` | Reset/reboot |
| `0x1E` | `UART_OBTAIN_ALL_FTESC_ID` | Obtain master/slave IDs |
| `0x20` | `UART_SET_CURRENT_GEAR_AND_OBTAIN_DATA` | Current/gear and telemetry |
| `0x23` | `UART_REBOOT_FTESC` | Reboot |
| `0x25` | `UART_SET_ID_CURRENT` | Set ID/current |
| `0x26` | `UART_SET_POSITION` | Set position |
| `0x27` | `UART_SET_SPEED` | Set speed |

These values align with the common V1.7 command families where those commands remain present. V1.7 adds firmware authorization/update commands and setup commands not present in this older enum.

## 2. Frame encoder cross-check

The C function `FTESC_Uart_packSendPayload`:
- computes CRC-16 using the two 256-byte lookup tables;
- uses `0xAA` plus one-byte length for payloads up to 255 bytes;
- uses `0xBB` plus 16-bit big-endian length for larger payloads;
- copies the INFO payload;
- appends CRC high byte, CRC low byte and `0xDD`.

This independently matches the V1.7 frame builder at `0x0049C5C0` and the offline codec in `scripts/ftesc_frame.py`.

## 3. CMD 0x00 telemetry cross-check

The C source's `Ftesc_Obtain_Realtime_Data` sends a one-byte INFO payload containing command `0x00`.

Its response parser reads:
- controller ID and fault;
- voltage ÷100;
- battery and motor current ÷1,000,000;
- RPM as 32-bit;
- duty ÷10,000;
- MOSFET and motor temperatures ÷100;
- CPU load ÷10,000;
- encoder angle ÷1,000,000.

This matches the base portion of the V1.7 CMD 0x00 response. V1.7 extends the payload with three additional angular values and PAS RPM, documented in [V1_7_RESPONSE_DISPATCH_MAP.md](V1_7_RESPONSE_DISPATCH_MAP.md).

## 4. CMD 0x02 and CAN forwarding gaps

The C enum names CMD `0x02` and CMD `0x10`, but:
- its example parser only implements response case `0x00`;
- it does not contain an outbound builder for CMD `0x02`;
- it declares `UART_CAN_FWARD=0x10` but does not implement the forwarding wrapper.

This independently supports the current status: V1.7's actual CMD 0x02 path and UART CAN-forward envelope still require native tracing. The enum entry alone is not an implementation.

## 5. Parser caveat

The sample C helper `valueCompose_I32` assembles big-endian bytes into an `int32_t`; its signed 24-bit helper does not visibly sign-extend the high bit. The offline direct-CAN decoder in this repository deliberately uses proper signed 24-bit conversion according to the CAN protocol's signed field definitions. Do not copy the C sample's integer edge-case behavior without checking the protocol type.

## 6. Conclusion

The user-provided C source independently corroborates the common UART framing, CRC byte order, CMD 0x00 telemetry base layout and several command IDs. It does not close the V1.7 CMD 0x02 or CMD 0x10 implementation gaps.
