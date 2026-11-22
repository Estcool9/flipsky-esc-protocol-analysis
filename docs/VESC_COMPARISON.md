# VESC Tool comparison: functional similarity, protocol divergence

**Conclusion:** the Flipsky application resembles VESC Tool at the product/UI level, but the analyzed V1.7 binary implements a distinct FTESC command and frame protocol. It must not be treated as a drop-in VESC Tool protocol implementation.

## 1. Flipsky's official product distinction

Flipsky's own article, dated 9 January 2026, divides its controllers into:
- **FSESC / VESC**: VESC-based controllers configured with VESC Tool.
- **FT ESC / NON-VESC**: independently developed by Flipsky and intended to work with Flipsky ESC Tool.

Flipsky explicitly says the product families and programming tools are not interchangeable:
- [Flipsky — Differences Between FT ESC and FSESC](https://flipsky.net/blogs/vesc-tool/differences-between-ft-esc-and-fsesc)

Flipsky's March 2026 FT-series firmware update guide also directs users to the Flipsky ESC Tool and describes the FT-series bootloader/update sequence:
- [Flipsky — How to Update FT Series ESC to V1.6](https://flipsky.net/blogs/vesc-tool/how-to-update-ft-series-esc-to-v16)

## 2. Evidence from the analyzed V1.7 executable

The binary contains FTESC-specific Qt modules and methods:
- `Flipsky.ftesc.FtescLowLevelFace`
- `Flipsky.ftesc.uartcomm`
- `Flipsky.ftesc.valuesetups`
- `ftescMotorSignalReadAck(...)`
- `ftescGetRealtimeDataOnce(...)`

More importantly, the binary's actual frame and command bytes diverge from the standard VESC protocol.

## 3. Outer frame comparison

| Field | FTESC V1.7 binary | Standard VESC UART |
|---|---|---|
| Short-frame start | `0xAA` | `0x02` |
| Long-frame start | `0xBB` | `0x03` |
| Length | 1 byte for short; 2-byte big-endian for long | 1 byte for short; 2-byte big-endian for long |
| CRC coverage | INFO payload | Payload |
| CRC | CRC-16/MODBUS as implemented in the FTESC binary | VESC CRC16 implementation |
| Stop byte | `0xDD` | `0x03` |

VESC's public UART packet documentation describes start byte 2/3, length, payload, CRC and stop byte 3:
- [Benjamin Vedder — Communicating with the VESC using UART](https://vedder.se/2015/10/communicating-with-the-vesc-using-uart/)
- [VESC Tool — packet.h](https://github.com/vedderb/vesc_tool/blob/master/packet.h)

The FTESC framing is therefore not the standard VESC UART frame, even though both use a length-prefixed payload and CRC.

## 4. Command-ID comparison

The following are observed request command bytes in the FTESC V1.7 binary and standard VESC command IDs from the open-source VESC firmware `datatypes.h`.

| Operation | FTESC V1.7 | Standard VESC |
|---|---:|---:|
| Telemetry / values | `0x00` (FTESC realtime response) | `0x04` COMM_GET_VALUES |
| Firmware version | `0x11` | `0x00` COMM_FW_VERSION |
| Bootloader | `0x13` | `0x01` COMM_JUMP_TO_BOOTLOADER |
| Erase application | `0x16` | `0x02` COMM_ERASE_NEW_APP |
| Write firmware block | `0x18` | `0x03` COMM_WRITE_NEW_APP_DATA |
| Duty | `0x03` | `0x05` COMM_SET_DUTY |
| Current | `0x04` | `0x06` COMM_SET_CURRENT |
| Brake current | `0x06` | `0x07` COMM_SET_CURRENT_BRAKE |
| Speed / RPM | `0x27` | `0x08` COMM_SET_RPM |
| Position | `0x26` | `0x09` COMM_SET_POS |

This creates dangerous numeric collisions: for example, FTESC `0x04` is a current-control request, while standard VESC `0x04` is COMM_GET_VALUES. Never send a command based only on its numeric ID without the correct protocol and controller family.

Primary VESC command source:
- [vedderb/bldc — datatypes.h](https://github.com/vedderb/bldc/blob/master/datatypes.h)

## 5. Similarities that remain useful

The two ecosystems still share high-level concepts:
- Qt/C++ application architecture and parameter editors;
- motor control modes such as duty, current, speed and position;
- FOC, motor identification, encoder and thermal configuration;
- real-time telemetry;
- UART, BLE and multi-controller/CAN workflows;
- firmware update and bootloader concepts.

These similarities can guide the architecture of a new client, but not the low-level wire protocol.

## 6. Practical recommendation

Build the independent client around the FTESC evidence recovered from V1.7:
1. FTESC AA/BB framing and CRC implementation.
2. FTESC command IDs and payload schemas.
3. FTESC `ValueSetup` typed serializer and profile ordering.
4. FTESC UART/BLE transport and CAN forwarding.
5. FTESC-specific firmware authorization/update workflow.

Reuse VESC Tool only as a conceptual reference for UI patterns, motor-control terminology and general engineering practices. Do not reuse its command IDs or packet codec for FTESC.

## 7. References

- [Flipsky — Differences Between FT ESC and FSESC](https://flipsky.net/blogs/vesc-tool/differences-between-ft-esc-and-fsesc)
- [Flipsky — How to Update FT Series ESC to V1.6](https://flipsky.net/blogs/vesc-tool/how-to-update-ft-series-esc-to-v16)
- [Benjamin Vedder — Communicating with the VESC using UART](https://vedder.se/2015/10/communicating-with-the-vesc-using-uart/)
- [VESC Tool — packet.h](https://github.com/vedderb/vesc_tool/blob/master/packet.h)
- [VESC firmware — datatypes.h](https://github.com/vedderb/bldc/blob/master/datatypes.h)
