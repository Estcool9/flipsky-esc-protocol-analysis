# FTESC V1.7 vs VESC Tool — source-pinned protocol and architecture comparison

**Research date:** 2026-11-22  
**FTESC binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`, SHA-256 `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`

## Executive conclusion

Both products use Qt/C++ technologies and expose familiar ESC functions (duty, current, speed, telemetry, setup, CAN and firmware update). That similarity is at the application/product level only.

The public VESC Tool source and the Flipsky V1.7 binary have different UART frame markers, CRC algorithms, request command namespaces, firmware-update protocols, and CAN identifier layouts. Flipsky explicitly categorizes FT ESC as **NON-VESC** and says FT ESC and FSESC/VESC programming tools are not interchangeable. A client must select a protocol profile for the exact controller family; it must never select a protocol from a name such as “Flipsky” or from a matching numeric command ID.

**The independent FTESC codec in this repository must not be used to control a VESC, and VESC Tool's codec must not be used to control an FTESC.**

## 1. Source material pinned for this comparison

The comparison uses source code rather than relying only on screenshots or product descriptions.

### VESC Tool application

- Repository: [vedderb/vesc_tool](https://github.com/vedderb/vesc_tool)
- Default branch at inspection: `master`
- Pinned commit: [`04614bf50909b78f23716af694bf19ab9745e7df`](https://github.com/vedderb/vesc_tool/commit/04614bf50909b78f23716af694bf19ab9745e7df), dated 2026-11-21
- Relevant files:
  - [`packet.cpp`](https://github.com/vedderb/vesc_tool/blob/04614bf50909b78f23716af694bf19ab9745e7df/packet.cpp) — UART frame encoder, parser and CRC
  - [`commands.cpp`](https://github.com/vedderb/vesc_tool/blob/04614bf50909b78f23716af694bf19ab9745e7df/commands.cpp) — command builders, response dispatch and CAN forwarding
  - [`datatypes.h`](https://github.com/vedderb/vesc_tool/blob/04614bf50909b78f23716af694bf19ab9745e7df/datatypes.h) — UART and CAN command IDs
  - [`bleuart.cpp`](https://github.com/vedderb/vesc_tool/blob/04614bf50909b78f23716af694bf19ab9745e7df/bleuart.cpp) — BLE UART service and characteristics
  - [`README.md`](https://github.com/vedderb/vesc_tool/blob/04614bf50909b78f23716af694bf19ab9745e7df/README.md) — project and licence statement

### VESC firmware

Some CAN identifier and command semantics belong to the firmware rather than the desktop application. The firmware reference was pinned separately:

- Repository: [vedderb/bldc](https://github.com/vedderb/bldc)
- Pinned commit: [`6fda11c299a475d5e6a6d1c5f5efd2539643d70b`](https://github.com/vedderb/bldc/commit/6fda11c299a475d5e6a6d1c5f5efd2539643d70b), dated 2026-11-21
- Relevant files:
  - [`datatypes.h`](https://github.com/vedderb/bldc/blob/6fda11c299a475d5e6a6d1c5f5efd2539643d70b/datatypes.h)
  - [`comm/comm_can.c`](https://github.com/vedderb/bldc/blob/6fda11c299a475d5e6a6d1c5f5efd2539643d70b/comm/comm_can.c)
  - [`comm/commands.c`](https://github.com/vedderb/bldc/blob/6fda11c299a475d5e6a6d1c5f5efd2539643d70b/comm/commands.c)
  - [`documentation/comm_can.md`](https://github.com/vedderb/bldc/blob/6fda11c299a475d5e6a6d1c5f5efd2539643d70b/documentation/comm_can.md)

The file hashes and commit identities are also recorded in [`analysis-data/vesc-reference-manifest.json`](../analysis-data/vesc-reference-manifest.json).

## 2. Application architecture: similar toolkit, different product

| Area | FTESC V1.7 | VESC Tool |
|---|---|---|
| Implementation | Native PE32 x86 application | Public C++/Qt source |
| UI technology observed | Qt 5 / QML, QtQuick, QtCharts | Qt/C++ application with application/pages/widgets and resource collections |
| Transport abstractions | Flipsky `FtescLowLevelFace`, `uartcomm`, `bleuart` | `Packet`, `Commands`, `BleUart` |
| Configuration model | 13 recovered ValueSetup XML variants, ordered by `ValueSeque`, marker-prefixed blocks | VESC configuration structures and typed command serialization such as MC configuration and setup-values queries |
| Protocol family | FTESC-specific UART and CAN | VESC COMM and VESC CAN |
| Source availability | The analyzed Flipsky V1.7 program is a shipped binary; its source was not available in the supplied project | Official public source repository; GPL-3.0 |

The shared use of Qt and similar control features is not evidence of shared command implementations, data structures or wire compatibility.

## 3. UART framing: not wire-compatible

### FTESC V1.7

```text
Short:     AA | LEN8      | INFO | CRC16_BE | DD
Extended:  BB | LEN16_BE  | INFO | CRC16_BE | DD
```

- CRC covers INFO (command byte plus DATA).
- CRC-16/MODBUS: reflected polynomial `0xA001`, initial value `0xFFFF`, high byte then low byte.
- The V1.7 send path selects short form through 255 INFO bytes, then extended form.
- The native constructor sets a maximum payload field to `0x2710` (10,000 bytes).

### VESC Tool

The pinned `Packet::sendPacket()` implementation uses three forms:

```text
Short:      02 | LEN8       | PAYLOAD | CRC16_BE | 03
Medium:     03 | LEN16_BE   | PAYLOAD | CRC16_BE | 03
Long:       04 | LEN24_BE   | PAYLOAD | CRC16_BE | 03
```

- CRC covers the payload (including the VESC command byte).
- The VESC CRC lookup table is the non-reflected `0x1021` family and the accumulator starts at zero; the wire order is high byte then low byte.
- VESC's parser validates the `0x03` stop byte and CRC before returning the payload.

**Interoperability consequence:** even though both systems use a length, payload, CRC and terminator, the start/stop markers, extended-length forms and CRC initialisation/polynomial differ. A VESC packet encoder cannot emit a valid FTESC frame by changing only the command ID.

## 4. UART command namespace: numeric collisions are real

Representative VESC command IDs from the pinned VESC `datatypes.h` and Flipsky V1.7 commands recovered from the executable:

| Operation | FTESC V1.7 | VESC |
|---|---:|---:|
| Realtime values request | `0x00` | `0x04` (`COMM_GET_VALUES`) |
| Firmware version | `0x11` | `0x00` (`COMM_FW_VERSION`) |
| Enter bootloader | `0x13` | `0x01` (`COMM_JUMP_TO_BOOTLOADER`) |
| Erase application | `0x16` | `0x02` (`COMM_ERASE_NEW_APP`) |
| Write firmware block | `0x18` | `0x03` (`COMM_WRITE_NEW_APP_DATA`) |
| Duty | `0x03` | `0x05` (`COMM_SET_DUTY`) |
| Current | `0x04` | `0x06` (`COMM_SET_CURRENT`) |
| Brake current | `0x06` | `0x07` (`COMM_SET_CURRENT_BRAKE`) |
| Speed / RPM | `0x27` | `0x08` (`COMM_SET_RPM`) |
| Position | `0x26` | `0x09` (`COMM_SET_POS`) |

Examples of dangerous collisions:
- FTESC `0x04` is a current-control command; VESC `0x04` requests telemetry.
- FTESC `0x00` requests realtime telemetry; VESC `0x00` requests firmware-version information.
- FTESC `0x06` is brake current; VESC `0x06` is motor current.

Never send an opcode based only on its numeric value or a UI label.

## 5. UART-to-CAN forwarding: similar idea, different opcode and context

Both tools can address a remote ESC through a UART forwarding command:

| Detail | FTESC | VESC |
|---|---|---|
| UART forwarding command | `0x10` | `COMM_FORWARD_CAN = 34 = 0x22` |
| Target ID | one-byte slave ESC ID | one-byte `mCanId` |
| Nested content | slave command followed by slave DATA | VESC command followed by DATA |
| Desktop implementation observed | FTESC UI/target state and offline envelope codec are known; native V1.7 insertion point is still unresolved | `Commands::emitData()` prepends `COMM_FORWARD_CAN` and `mCanId` when CAN forwarding is enabled |

This is a conceptual similarity, not a compatible wrapper. The FTESC desktop binary's precise wrapper insertion and slave-response correlation remain an open reverse-engineering task; the standalone `build_can_forward_info()` function implements the versioned FTESC protocol envelope, not a proven full reproduction of every V1.7 UI call path.

## 6. Direct CAN: identifier layout, command IDs and payloads differ

### VESC CAN

The pinned VESC firmware uses:

```text
Extended ID:
B28..B16 = unused
B15..B8  = CAN_PACKET command ID
B7..B0   = VESC controller ID
```

The firmware builds identifiers as:

```text
controller_id | (CAN_PACKET_ID << 8)
```

Its basic CAN command IDs are:
- `0` duty;
- `1` current;
- `2` brake current;
- `3` RPM;
- `4` position.

The documented basic commands carry a four-byte signed big-endian value with command-specific scaling; the CAN link supplies the data-link CRC, and the simple command payload does not append a second application CRC.

### FTESC direct CAN V1.4

The Flipsky document describes:
- a 29-bit extended ID;
- a fixed upper prefix (the decoder uses `0x10000000`);
- ESC ID in bits 8–15;
- CAN command in bits 0–7.

The offline codec encodes this as:

```text
0x10000000 | (esc_id << 8) | command
```

Representative FTESC commands include:
- `0x00` current with gear + CRC16;
- `0x01` brake current + CRC16;
- `0x02` duty with gear + CRC16;
- `0x0B`, `0x0C`, `0x0D` periodic telemetry + CRC16;
- `0x12` eRPM with gear + CRC16;
- `0x13` position with gear + CRC16;
- `0x14` D-axis current + CRC16.

The node/command byte positions are **reversed** relative to VESC, the upper identifier bits differ, the command IDs have different meanings, and FTESC adds application-level CRC16 to the documented data payloads.

### A PDF ambiguity left open

The FTESC V1.4 PDF's C enum assigns decimal values `26` and `27` to the two no-CRC brake commands (which are `0x1A` and `0x1B`), while their section headings label them `20H` and `21H` (which are `0x20` and `0x21`). The offline builder exposes both variants and requires an explicit command ID. It does not guess which one a shipping ESC accepts.

The same PDF's section 3.1.7 says CAN telemetry 0x0B is emitted every 10 ms, while the C enum comment says every 20 ms. Section 3.1.8 and 3.1.9 say 10 ms. The 0x0B timing conflict is unresolved.

## 7. Parameter and firmware-update data models

| Area | FTESC V1.7 | VESC |
|---|---|---|
| Configuration | XML `ValueSetups` records plus explicit `ValueSeque` order; setup payloads contain fixed 32-bit marker values | VESC configuration structures and typed `COMM_GET_VALUES_SETUP` / MC configuration commands |
| Firmware boot/update commands | enter boot mode `0x13`, erase `0x16`, block write `0x18` | jump-to-bootloader `0x01`, erase `0x02`, write-new-app-data `0x03` |
| Update security | V1.7 UUID request, 16-byte TEA challenge/response and block XOR transform | Separate VESC firmware update implementation and firmware image handling |
| Block model | 240-byte image blocks in the analyzed V1.7 desktop flow | VESC Tool/firmware's own chunk and image protocol |

These models are not interchangeable. The public VESC sources were inspected for comparison only; no VESC code was copied into the FTESC codec.

## 8. BLE: VESC's UART service known; FTESC's UUID unresolved

The pinned VESC Tool `bleuart.cpp` uses the Nordic UART Service UUID:
- service: `6e400001-b5a3-f393-e0a9-e50e24dcca9e`;
- RX characteristic: `6e400002-b5a3-f393-e0a9-e50e24dcca9e`;
- TX characteristic: `6e400003-b5a3-f393-e0a9-e50e24dcca9e`.

The VESC implementation writes in 20-byte chunks using `WriteWithoutResponse`.

The FTESC binary contains the internal `Flipsky.ftesc.bleuart` module and Qt5Bluetooth usage. The three exact VESC UUID strings were not found in the Ghidra-defined string inventory. That does not prove FTESC uses a different service: values could be constructed, stored in a different resource/data form, or missed by the current string analysis. FTESC BLE UUIDs, MTU/chunk size and write mode remain open.

## 9. Compatibility verdict

| Question | Result |
|---|---|
| Can VESC Tool's UART packet codec be reused for FTESC? | **No** — markers and CRC algorithm differ. |
| Can VESC UART command IDs be reused? | **No** — multiple numeric IDs have different meanings. |
| Can VESC direct-CAN IDs be reused? | **No** — node/command bit positions and command IDs differ. |
| Is UART-to-CAN forwarding conceptually similar? | **Yes** — both prefix a target ID and nested command, but opcode and native routing differ. |
| Is BLE transport known to be identical? | **Unknown** — VESC uses Nordic UART; FTESC service UUID not recovered. |
| Are configuration records interchangeable? | **No evidence** — FTESC uses ValueSetup/ValueSeque and marker blocks. |
| Are firmware images or update flows interchangeable? | **No evidence; treat as incompatible** — different commands and authorization/block formats. |

Flipsky's [official product-family statement](https://flipsky.net/blogs/vesc-tool/differences-between-ft-esc-and-fsesc) explicitly says FT ESC is NON-VESC and its programming tool is not interchangeable with VESC Tool. The low-level evidence independently supports that warning.

## 10. Licence and clean-room boundary

The VESC Tool repository declares GPL-3.0. This project records protocol and architecture observations and links to the exact source locations; it does not copy VESC source files or source-code snippets into the FTESC implementation. Any future port/adaptation of VESC code must be reviewed for GPL obligations and attribution. The current comparison is not legal advice.

## 11. Next VESC/FTESC comparison tasks

1. Obtain and hash a legitimate VESC Tool binary only if binary-to-source analysis is needed; the current comparison uses the VESC public source.
2. Compare VESC and FTESC receive-buffer handling under identical fragmented/concatenated synthetic packet sequences using independent test harnesses.
3. Search the FTESC binary/resource data for BLE service/characteristic UUIDs; do not infer them from VESC.
4. Compare setup serialization semantics at the data-model level without translating GPL source.
5. Keep the V1.7 UART CMD 0x10 wrapper insertion point, slave reply routing, TopFlow XML and live-device behavior in the residual-unknown list.

No ESC was connected and no VESC/FTESC control command was transmitted.
