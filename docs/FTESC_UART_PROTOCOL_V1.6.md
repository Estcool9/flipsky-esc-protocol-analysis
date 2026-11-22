
# Flipsky FT ESC UART protocol — V1.6

**Document:** FLIPSKY FT ESC UART Communication Protocol V1.6  
**Protocol document date:** 2025-12-09  
**Firmware version stated:** V1.6  
**Document ID:** FT-CM-UART-20250422-01  
**Length:** 23 pages  
**Related example:** [reference/ftesc_v1.4_1.5_1.6_uart_handle.c](../reference/ftesc_v1.4_1.5_1.6_uart_handle.c)

This is an English-language engineering digest of the V1.6 protocol PDF stored in the user's Nextcloud project directory. It is kept distinct from observations made directly in the V1.7 Windows executable.

## 1. UART link and outer frame

Documented UART settings: 115200 bit/s, 8 data bits, 1 start bit, 1 stop bit, no parity, no flow control, half or full duplex.

Frame layout:

    STX | DLEN | INFO (CMD + DATA) | CRC16 | ETX

| Field | Size | Meaning |
|---|---:|---|
| STX | 1 byte | 0xAA for INFO length <=255; 0xBB for INFO length >255 and <=65535 |
| DLEN | 1 or 2 bytes | Total INFO length, including CMD and DATA |
| CMD | 1 byte | Command / response identifier |
| DATA | 0..65534 bytes | Command-specific data |
| CRC16 | 2 bytes | CRC of the complete INFO field (CMD + DATA), high byte first |
| ETX | 1 byte | 0xDD |

For extended 0xBB frames, DLEN is 16-bit big-endian. The sender example uses 0xAA for lengths through 255 and 0xBB for lengths above 255.

### CRC parameters

The vendor C example contains the same 256-entry high/low lookup tables and update algorithm identified in V1.7:
- CRC-16/MODBUS, reflected polynomial 0xA001;
- initial value 0xFFFF;
- final XOR 0x0000;
- coverage: INFO only, i.e. CMD followed by DATA;
- wire order: high CRC byte then low CRC byte.

The standard check vector 123456789 produces 0x4B37. The V1.7 tables at VAs 0x005310C0 and 0x005311C0 independently match the split MODBUS tables.

### Numeric representation

The protocol specifies big-endian representation for uint16_t, int16_t, uint32_t and int32_t. Unmarked one-byte values are uint8_t.

The sample C implementation also contains:
- I16/U16, I24/U24 and I32/U32 big-endian compose/decompose helpers;
- F16/F32 helpers that scale a float to a signed integer before serialization;
- AF32, a custom frexpf-based 32-bit float encoding helper.

The presence of AF32 in the sample does not establish that every command uses it. Follow the command-specific descriptions.

## 2. Command identifiers

| ID | Official V1.6 symbol | Function |
|---:|---|---|
| 0x00 | UART_OBTAIN_DATA_ONCE | One-shot real-time telemetry |
| 0x02 | UART_CONTROL_AND_OBTAIN_DATA_ONCE | UART-mode control input plus telemetry |
| 0x03 | UART_SET_DUTY | Duty-cycle control |
| 0x04 | UART_SET_CURRENT | Motor-current control |
| 0x05 | UART_SET_CURRENT_GEAR | Motor-current control plus gear |
| 0x06 | UART_SET_BRAKE_CURRENT | Brake-current control |
| 0x10 | UART_CAN_OVER | Forward an instruction to a CAN slave |
| 0x11 | UART_OBTAIN_FIRMWARE_VERSION | Firmware / hardware identity |
| 0x19 | UART_KEEP_LIVE | Keep the previous control command valid |
| 0x1A | UART_SET_AUTO_OBTAIN_REALTIME_DATA | Configure periodic telemetry |
| 0x1D | UART_RESET_AND_REBOOT_FTESC | Restore factory settings and reboot |
| 0x1E | UART_OBTAIN_ALL_FTESC_ID | Enumerate master and slave ESC IDs |
| 0x20 | UART_SET_CURRENT_GEAR_AND_OBTAIN_DATA | Current plus gear, with telemetry response |
| 0x23 | UART_REBOOT_FTESC | Reboot |
| 0x25 | UART_SET_ID_CURRENT | D-axis current control |
| 0x26 | UART_SET_POSITION | Position control (encoder mode) |
| 0x27 | UART_SET_SPEED | Electrical-RPM control |

**Mode-dependent alias:** V1.6 also defines PAS_GEAR_CONTROL_AND_OBTAIN_DATA_ONCE as command 0x02. The same command byte is interpreted according to the ESC's configured input-signal mode. In UART mode, the 14 data bytes are control inputs; in PAS mode, only D0 (PAS gear) is valid and D1-D13 are ignored. These are not two different numeric opcodes.

The sample C enum spells 0x10 as UART_CAN_FWARD, whereas the PDF uses UART_CAN_OVER. The numeric command is identical; this is a naming difference.

## 3. Command and response layouts

Lengths below are INFO/DLEN lengths unless labelled DATA length. Since INFO includes CMD, subtract one from DLEN to obtain DATA byte count.

### 3.1 One-shot telemetry — CMD 0x00

Request: DLEN 0x01, CMD 0x00, no DATA.

Response base layout:

| DATA offset | Size | Field | Representation |
|---:|---:|---|---|
| 0 | 1 | MCU/controller ID | uint8 |
| 1 | 1 | Error code | uint8 |
| 2 | 2 | Battery voltage | int16 / 100 |
| 4 | 4 | Battery current | int32 / 1,000,000 |
| 8 | 4 | Motor current | int32 / 1,000,000 |
| 12 | 4 | Motor electrical RPM | int32 |
| 16 | 2 | Duty | int16 / 10,000 |
| 18 | 2 | MOSFET temperature | int16 / 100 |
| 20 | 2 | Motor temperature | int16 / 100 |
| 22 | 2 | CPU utilization | int16 / 10,000 |
| 24 | 4 | Encoder angle | int32 / 1,000,000 |

Base DATA length is 28 bytes; INFO/DLEN is 29 (0x1D).

When automatic telemetry command 0x1A is enabled, V1.6 documents a longer response with INFO/DLEN 0x2D (44 DATA bytes):
- DATA offsets 28-39: 12 reserved bytes, default zero;
- DATA offsets 40-43: PAS RPM, int32.

The sample C source decodes the 28-byte base response only. The PDF describes the additional auto-report fields.

### 3.2 UART control plus telemetry — CMD 0x02

Request: INFO/DLEN 0x0F, containing CMD and 14 DATA bytes. This interpretation is valid when Input Signal Type is UART.

V1.6 request DATA:

| Offset | Size | Meaning |
|---:|---:|---|
| 0-1 | 2 | Reserved, default 0x0000 |
| 2-3 | 2 | Current request: 0-1023; 0-511 braking/negative, 512-1023 driving |
| 4 | 1 | Enable direction switching (0/1) |
| 5 | 1 | Direction: 0 forward, 1 reverse; valid only when offset 4 is 1 |
| 6 | 1 | Gear: 0 none, 1 low, 2 medium, 3 high, 4 reverse |
| 7 | 1 | External horn: 0 off, 1 on |
| 8 | 1 | External headlight: 0 off, 1 on |
| 9 | 1 | External brake light: 0 off, 1 on |
| 10 | 1 | Enable cruise control: 0/1 |
| 11 | 1 | Cruise mode: 0 exit, 1 enter |
| 12 | 1 | Enable multi-mode control: 0/1 |
| 13 | 1 | Multi-mode: 0 normal, 1 tank U-turn, 2 off-road hill-climb |

Response: INFO/DLEN 0x1C, CMD 0x02, 27 DATA bytes.

| DATA offset | Size | Field | Representation |
|---:|---:|---|---|
| 0 | 1 | Error code | uint8 |
| 1 | 2 | Battery voltage | int16 / 100 |
| 3 | 4 | Battery current | int32 / 1,000,000 |
| 7 | 4 | Motor current | int32 / 1,000,000 |
| 11 | 4 | Motor electrical RPM | int32 |
| 15 | 2 | Duty | int16 / 10,000 |
| 17 | 2 | MOSFET temperature | int16 / 100 |
| 19 | 2 | Motor temperature | int16 / 100 |
| 21 | 2 | CPU utilization | int16 / 10,000 |
| 23 | 4 | Encoder angle | int32 / 1,000,000 |

The PAS alias also lists PAS RPM in DATA bytes 27-30. However, the same section still labels the response DLEN as 0x1C, which cannot contain those additional four bytes. 31 DATA bytes plus CMD would require DLEN 0x20. This is an inconsistency in the PDF, recorded as unresolved. The offline decoder accepts either the 27-byte base DATA or 31-byte PAS-extended DATA and does not invent missing bytes.

Offline request builders now distinguish the V1.4 field order (current code at DATA[0:2], reserved at DATA[2:4]) from the V1.6 field order (reserved at DATA[0:2], current code at DATA[2:4]). See `build_v14_control_and_obtain_data_once_info()` and `build_v16_control_and_obtain_data_once_info()` in `scripts/ftesc_requests.py`. The V1.6 PAS alias has a separate builder.

### 3.3 Current, duty and motion commands

| CMD | Request DLEN | DATA | Response |
|---:|---:|---|---|
| 0x03 | 5 | int32 duty × 100,000 | None |
| 0x04 | 5 | int32 motor current × 1,000 | None |
| 0x05 | 6 | int32 motor current × 1,000; uint8 gear | None |
| 0x06 | 5 | int32 brake current × 1,000 | None |
| 0x20 | 6 | int32 motor current × 1,000; uint8 gear | Telemetry, DLEN 0x1C |
| 0x25 | 5 | int32 D-axis current × 1,000 | None |
| 0x26 | 5 | int32 position × 1,000; encoder mode only | None |
| 0x27 | 5 | int32 electrical RPM | None |

The PDF says commands 0x03, 0x04, 0x05, 0x06, 0x20, 0x25, 0x26 and 0x27 are only valid when Input Signal Type is OFF. These protocol descriptions are not safe motor-configuration advice.

### 3.4 CAN forwarding — CMD 0x10

Request DATA:
- D0: slave ESC ID;
- D1: command to send to that slave;
- D2-Dn: slave command data.

Response DATA:
- D0: returned slave command ID (must match the slave command);
- D1-Dn: slave response data.

This defines the UART-level envelope for forwarding to a CAN slave. The repository implements this as `build_can_forward_info(slave_id, slave_command, slave_data)`; the reply's first INFO byte is the returned slave command ID and is decoded by `parse_can_forward_response()`. CAN arbitration identifiers and low-level CAN transport details are specified separately in [FTESC_CAN_PROTOCOL_V1.4.md](FTESC_CAN_PROTOCOL_V1.4.md). The exact V1.7 desktop-code insertion point for this envelope is still unresolved.

### 3.5 Identity, keepalive and reboot

- 0x11: request DLEN 1, no DATA. Response CMD 0x11: D0 version major, D1 version minor, D2 mode marker (0xAC bootloader, 0xEF application), D3 onward hardware name as ASCII, followed by hardware serial number. The V1.7 response decoder now exposes these semantic field names.
- 0x19: no DATA request; DLEN 1. After relevant control commands, send this at least every 500 ms to keep the last command valid. Response is an empty CMD 0x19.
- 0x1D: request DLEN 2 and one reserved DATA byte set to zero. Response DLEN 1, empty DATA. The controller begins factory reset and restart 50 ms after the ECU receives the response.
- 0x23: request DLEN 1, no DATA; no response is specified.
- 0x1E: request DLEN 1, no DATA. Response DATA D0 is master MCU ID; D1 onward are slave MCU IDs.

### 3.6 Periodic telemetry — CMD 0x1A

Request: DLEN 4, CMD 0x1A, DATA:
- D0: enable auto-return (0 off, 1 on);
- D1-D2: report frequency, uint16, range 1-1000 Hz.

Response: DLEN 8, CMD 0x1A, DATA:
- D0: automatic-return marker;
- D1-D2: frequency;
- D3-D6: automatic-return function address.

The PDF states that the ECU must send this command at least every 800 ms after enabling periodic telemetry. On timeout the MCU stops returning telemetry. This differs from the 0x19 control keepalive interval of 500 ms.

## 4. Error codes

| Code | Meaning |
|---:|---|
| 0 | No error |
| 1-3 | Phase A/B/C software absolute overcurrent |
| 4-6 | Phase A/B/C current sensor fault |
| 7 | Sum of three phase currents is not zero |
| 8 | Bus undervoltage |
| 9 | Bus overvoltage |
| 10 | MOSFET overtemperature |
| 11 | Motor overtemperature |
| 12 | MOSFET temperature sensor fault |
| 13 | Watchdog reset |
| 14 | Flash corruption |
| 15 | MCU undervoltage |
| 16 | Motor temperature sensor fault |
| 17 | Motor blocking |
| 18 | Driver fault |
| 19 | Motor out of phase |
| 20 | Bus overcurrent |
| 23 | ERROR_END enum sentinel, not a fault description |

Codes 21-22 are not assigned in the table.

## 5. V1.4 to V1.6 revision comparison

The V1.6 revision table says it updates §3.1.1, updates §3.1.2 and adds §3.1.18.

| Area | V1.4 | V1.6 |
|---|---|---|
| Outer frame, STX, DLEN, ETX | AA/BB, INFO length, CRC16, DD | Same |
| CRC | MODBUS lookup tables, CRC over INFO (CMD+DATA) | Same |
| CMD 00 base telemetry | DLEN 1D, 28 DATA bytes | Same base response; auto mode documents DLEN 2D with 12 reserved bytes + PAS RPM |
| CMD 02 request offsets | D0-D1 current, D2-D3 reserved | D0-D1 reserved, D2-D3 current |
| CMD 02 response | Base telemetry, DLEN 1C | Base telemetry; PAS section reuses 02 and lists extra PAS RPM |
| PAS command | No §3.1.18 | New PAS-mode semantic alias on CMD 02 |

This is a material compatibility change for a UART-mode ECU encoder: V1.4 CMD 02 request bytes are not identical to V1.6.

The PAS response section lists 31 DATA bytes but retains DLEN 1C; that length inconsistency is not resolved by assuming one version is correct.

## 6. Scope and limitations

- This is the published UART protocol, not a BLE GATT specification.
- The protocol defines UART-level CAN forwarding but not all CAN transport details.
- The sample C file is an illustrative ECU-side implementation. It is not Flipsky ESC Tool source code or ESC firmware source.
- The sample C decodes only the base CMD 00 telemetry. The PDF describes the longer periodic telemetry response.
- No physical ESC was contacted during this analysis.

## 7. Offline implementation notes

- `build_can_forward_info()` implements the UART CMD 0x10 envelope; `parse_can_forward_response()` unwraps the slave command/data response.
- `build_v14_control_and_obtain_data_once_info()` and `build_v16_control_and_obtain_data_once_info()` preserve the version-specific CMD 0x02 byte order.
- `build_v16_pas_gear_control_info()` implements the PAS-mode CMD 0x02 alias.
- `build_current_gear_and_obtain_data_info()` covers CMD 0x20; `build_v14_reset_reboot_info()` preserves the V1.4 CMD 0x1D reserved byte.
- `build_keepalive_info()` builds CMD 0x19. The PDF specifies a 500 ms refresh after relevant control commands; this repository does not schedule or transmit it.
- `parse_auto_realtime_config()` decodes the V1.4/V1.6 seven-byte CMD 0x1A response; the V1.7 desktop binary's dispatcher instead emits a no-DATA acknowledgement.

## 8. Source inventory

- V1.4 UART protocol PDF: 510,037 bytes.
- V1.6 English UART protocol PDF: 534,546 bytes, 23 pages.
- V1.6 Chinese protocol counterpart: 520,303 bytes.
- V1.6 ECU-side C example: 12,314 bytes.
- V1.6 user manual: 7,387,878 bytes, 90 pages.

These were read from the user's Nextcloud project directory. The PDFs were text-extracted; page layout and figures have not yet been reviewed visually.
