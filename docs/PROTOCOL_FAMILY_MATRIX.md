# Protocol family matrix — explicit adapter selection

**Reference date:** 2026-11-22

The goal of the open-source replacement is to support Flipsky's two controller families without conflating them.

| Product family | Protocol adapter | Main public evidence | Configuration model | Programming tool |
|---|---|---|---|---|
| FT ESC / NON-VESC | FTESC V1.4 / V1.6 / V1.7 profiles | FTESC UART V1.6, FTESC CAN V1.4 PDFs and V1.7 executable | `ValueSetups` + `ValueSeque`, marker-prefixed blocks | Flipsky ESC Tool |
| FSESC / VESC-based | VESC V3.00+ protocol profile | Flipsky VESC UART/CAN V1.0 PDFs and `vedderb/bldc` | VESC firmware configuration structures | VESC Tool |

## Adapter rules

1. A device profile must explicitly name both product family and protocol version.
2. Brand alone must never select a protocol.
3. UART framing, CRC, command namespaces, CAN identifier layouts and configuration schemas remain separate per adapter.
4. Shared UI abstractions may expose concepts such as telemetry, motor settings, CAN node selection and firmware information, but their wire encoders/decoders are adapter-specific.
5. No auto-probe may send a potentially state-changing command. A passive identification response or user-selected profile is required.
6. Firmware update remains disabled until image format, authorization, bootloader sequence, rollback/recovery and hardware-specific compatibility have been verified.

## Current implementation

- FTESC offline codecs and tests: substantial, but TopFlow XML/profile mapping and the V1.7 native CAN routing path remain incomplete.
- VESC UART offline framing/CRC codec: added from Flipsky V1.0 document.
- VESC direct-CAN ID and basic offline command codec: added from Flipsky V1.0 document and cross-checked against VESC firmware.
- Shared desktop UI, actual serial/BLE device transport, firmware upload UI and live-device integration: not implemented.

See [FLIPSKY_VESC_PROTOCOL_V1.0.md](FLIPSKY_VESC_PROTOCOL_V1.0.md), [VESC_COMPARISON.md](VESC_COMPARISON.md) and [STATUS.md](STATUS.md).
