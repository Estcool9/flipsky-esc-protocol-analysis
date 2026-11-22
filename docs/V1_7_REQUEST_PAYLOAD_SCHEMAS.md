# V1.7 UART request payload schemas

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Analysis date:** 2026-11-22

This document describes INFO payloads (command byte + DATA). The outer UART AA/BB frame is described in [FTESC_UART_PROTOCOL_V1.6.md](FTESC_UART_PROTOCOL_V1.6.md). Builders in `scripts/ftesc_requests.py` return INFO bytes only and do not transmit.

## 1. Scalar control requests

All multi-byte values are big-endian signed 32-bit integers. The native code rounds the scaled float before serialization. The helpers at `0x0049D150` (signed int32) and `0x0049D1E0` (signed int16) use a 0.5 epsilon and x87 rounding-control changes to implement round-half-away-from-zero; the Python builders match this behavior.

| CMD | UartComm method | DATA field | Scale |
|---:|---|---|---:|
| `0x03` | `ftescControlDuty` | signed int32 | value ×100,000 |
| `0x04` | `ftescControlCurrent` | signed int32 | value ×1,000 |
| `0x06` | `ftescControlBrakeCurrent` | signed int32 | value ×1,000 |
| `0x25` | `ftescControlIdCurrent` | signed int32 | value ×1,000 |
| `0x26` | `ftescControlPosition` | signed int32 | value ×1,000 |
| `0x27` | `ftescControlSpeed` | signed int32 | value ×1 |

These are encoding scales, not safe operating limits or recommended values.

## 2. Automatic realtime telemetry

Native method `ftescGetAutoRealtimeData` is UartComm meta-object method index 32 and dispatches to `FUN_004993F0`.

| INFO offset | Field | Encoding |
|---:|---|---|
| 0 | CMD `0x1A` | one byte |
| 1 | enable | one byte |
| 2–3 | interval | unsigned 16-bit big-endian |

The method signature takes an 8-bit enable and a 16-bit interval. The response acknowledgement is a separate UartComm signal `ftescAutoGetRealtimeDataAck()`.

## 3. Setup writes and markers

### CMD 0x07 — motor setup

The native setter `FUN_00498D60` builds the marker-prefixed block when the motor setup vector exists:

```text
07 D2 C6 EF 10 [ValueSeque-ordered serialized values]
```

Marker: `0xD2C6EF10`.

### CMD 0x1B — motor signal setup

The native setter `FUN_00498540` conditionally builds two blocks:
- first vector at object offset `+0x18`: marker `0xD2C6EF10`;
- optional second vector at object offset `+0x1C`: marker `0x4879187D`.

```text
1B D2 C6 EF 10 [first ValueSeque block]
   [optional 48 79 18 7D second ValueSeque block]
```

The second marker is emitted only when the second vector exists. The exact product/model rule deciding when that vector exists is still unresolved.

### CMD 0x3A — TopFlow setup

The native setter `FUN_00498960` builds:

```text
3A 54 46 43 46 [TopFlow ValueSeque-ordered values]
```

Marker: `0x54464346`.

The independent TopFlow XML schema has not yet been recovered. The marker and block construction are known, but the full TopFlow value list and sequence are not.

## 4. Reset operations

The same command byte `0x1D` is used by two native methods:
- `resetTopFlowSetup()`: command `0x1D`, no DATA;
- `resetandRebootMotorSignalSetup(flag)`: command `0x1D` plus one trailing byte.

The meaning of the trailing flag is not identified, so the offline builder names it generically.

## 5. IMU calibration

Native method `ftescObtainImuCalibration(float)` dispatches to `FUN_00499070`:
- CMD `0x29`;
- one signed 32-bit big-endian value;
- input multiplied by 1,000 and rounded.

The acknowledgement signal is `imuCalibrationReceived(int)`.

## 6. CMD 0x0F — identify motor over CAN

Native method `ftescIdentifyMotorOverCan` dispatches to `FUN_00499180`. Instruction-level inspection confirms the exact serialized field order:

| INFO offset | Field source | Encoding |
|---:|---|---|
| 0 | command | `0x0F` |
| 1 | argument 2 | unsigned byte |
| 2 | low byte of argument 1 | unsigned byte |
| 3–4 | argument 4 | signed 16-bit BE, rounded |
| 5–6 | argument 3 | signed 16-bit BE, argument ×100, rounded |
| 7 | argument 5 | unsigned byte |

The semantic names/units of the five API arguments are not established, so the offline builder keeps generic argument names. The method name says “over CAN”; this builder produces only the INFO payload. It does not implement the unresolved UART CMD 0x10 wrapper.

## 7. No-DATA requests

The following mapped methods construct a one-byte INFO payload (CMD only):

| CMD | Method / operation |
|---:|---|
| `0x00` | Obtain realtime data once |
| `0x01` | Obtain IDs over CAN |
| `0x09` | Obtain motor setup |
| `0x0A` | Obtain control/signal setup |
| `0x0D` | Obtain PPM signal |
| `0x0E` | Obtain ADC signal |
| `0x11` | Obtain firmware version |
| `0x13` | Enter boot mode |
| `0x19` | Keepalive |
| `0x1C` | Obtain motor signal setup |
| `0x1E` | Obtain all ESC IDs |
| `0x21` | Obtain UUID |
| `0x23` | Reboot |
| `0x3B` | Obtain TopFlow setup |
| `0x3C` | Obtain default TopFlow setup |

Firmware erase/write commands 0x16/0x18 and authorization command 0x22 are covered separately in [FIRMWARE_UPDATE_FLOW.md](FIRMWARE_UPDATE_FLOW.md).

## 8. Unresolved/unsupported builders

- CMD `0x02`: defined by V1.6, but no V1.7 outbound builder or response case has been established.
- CMD `0x0F` payload layout is now implemented; semantic names/units of its five API arguments remain unknown.
- CMD `0x10` UART CAN-forward wrapper: enum exists in V1.6 source, but V1.7 wrapper insertion and slave response routing are not traced.
- TopFlow table: marker and setter path are known; the actual TopFlow value schema remains unavailable.
- Optional second CMD 0x1B marker block: condition is vector presence; product selection rule remains open.

## 9. Offline implementation

`scripts/ftesc_requests.py` implements the resolved scalar controls, auto-telemetry configuration, setup marker blocks, reset variants and no-DATA queries. It deliberately does not implement CMD 0x0F, CMD 0x02 or CMD 0x10.

`tests/test_ftesc_requests.py` validates scaling, signed big-endian encoding, marker order, optional second block and reset variants. These are offline byte-builder tests only; no motor command was sent.
