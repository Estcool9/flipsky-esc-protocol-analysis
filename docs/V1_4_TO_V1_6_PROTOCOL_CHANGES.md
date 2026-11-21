
# V1.4 to V1.6 UART protocol changes

## Executive summary

The V1.4 and V1.6 protocol documents retain the same outer UART framing and CRC scheme. The V1.6 revision table explicitly lists three changes: update §3.1.1, update §3.1.2 and add §3.1.18.

The changes are concentrated in real-time telemetry and the command 0x02 request layout, not the AA/BB frame envelope.

## Document metadata

| Item | V1.4 | V1.6 |
|---|---|---|
| Firmware version stated | V1.4 | V1.6 |
| Issue date | 2025-04-22 | 2025-12-09 |
| Pages | 21 | 23 |
| Document ID | FT-CM-UART-20250422-01 | FT-CM-UART-20250422-01 |

## Unchanged elements

- STX 0xAA for INFO length <=255 and 0xBB for length >255.
- DLEN is the total INFO length, i.e. CMD plus DATA.
- ETX is 0xDD.
- CRC-16/MODBUS covers INFO and is sent high byte first.
- 16-bit and 32-bit signed/unsigned protocol integers are big-endian.
- Main numeric command IDs remain: 00, 02-06, 10, 11, 19, 1A, 1D, 1E, 20, 23, 25, 26 and 27.

These points are directly visible in both protocol PDFs. The supplied V1.6 sample C repeats the same frame and CRC implementation, and V1.7's frame parser/builder independently matches.

## Change 1 — CMD 00 telemetry response

V1.4 documents the base response only:
- INFO/DLEN 0x1D;
- CMD 0x00;
- 28 DATA bytes: controller ID, error code, battery voltage/current, motor current, motor ERPM, duty, MOSFET/motor temperature, CPU utilization and encoder angle.

V1.6 documents:
- the same base 0x1D response when automatic telemetry is disabled;
- an extended 0x2D response when command 0x1A enables periodic data;
- DATA D28-D39 as 12 reserved zero bytes;
- DATA D40-D43 as signed 32-bit PAS RPM.

## Change 2 — CMD 02 UART-control request field ordering

V1.4 request DATA:
- D0-D1: current request (0-1023);
- D2-D3: reserved (default zero);
- D4-D13: direction, gears and auxiliary control flags.

V1.6 request DATA:
- D0-D1: reserved (default zero);
- D2-D3: current request (0-1023);
- D4-D13: same direction, gear and auxiliary control meanings.

This is a material compatibility change for an ECU encoder. A V1.4 request payload must not be assumed byte-compatible with V1.6 for command 0x02.

## Change 3 — PAS mode alias on CMD 02

V1.6 adds §3.1.18:
- symbolic command PAS_GEAR_CONTROL_AND_OBTAIN_DATA_ONCE;
- numeric CMD remains 0x02;
- interpretation is selected by the ESC input-signal mode;
- only DATA D0 (PAS gear, range 0-5) is valid;
- D1-D13 are ignored in PAS mode.

The response lists telemetry plus PAS RPM but retains DLEN 0x1C. Since this needs 31 DATA bytes plus CMD, the correct INFO/DLEN would be 0x20. This appears to be a specification inconsistency and is left unresolved.

## Implications for V1.7

- V1.7's outer parser/builder matches the public V1.6 frame and CRC rules.
- Qt strings include telemetry-related methods such as ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA) and ftescAutoGetRealtimeDataAck(), but these names alone do not prove numeric command mapping.
- Trace V1.7 command builders and response handlers before asserting that it implements every V1.6 command or always uses the same CMD 02 layout.
- Multiple V1.6 Windows builds are present in Nextcloud, but have not yet been staged on REA for binary-to-binary comparison.
