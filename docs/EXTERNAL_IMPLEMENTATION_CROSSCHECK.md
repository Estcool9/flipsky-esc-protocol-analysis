# Independent FTESC UART implementation cross-check

**Date:** 2026-11-22  
**Analyzed application:** Flipsky ESC Tool V1.7, SHA-256 `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`

## Reference implementation inspected

A separate public implementation was inspected at a pinned GitHub commit:

- Repository: [adamivie/flipsky-ft85bd](https://github.com/adamivie/flipsky-ft85bd)
- Commit: [49989ac0cde531a68799284d1de9efdd7ba14c7f](https://github.com/adamivie/flipsky-ft85bd/commit/49989ac0cde531a68799284d1de9efdd7ba14c7f)
- Python source: [python/flipsky_ft85bd.py](https://github.com/adamivie/flipsky-ft85bd/blob/49989ac0cde531a68799284d1de9efdd7ba14c7f/python/flipsky_ft85bd.py)
- Arduino source: [FlipskyFT85BD.cpp](https://github.com/adamivie/flipsky-ft85bd/blob/49989ac0cde531a68799284d1de9efdd7ba14c7f/arduino/FlipskyFT85BD/FlipskyFT85BD.cpp)
- Header: [FlipskyFT85BD.h](https://github.com/adamivie/flipsky-ft85bd/blob/49989ac0cde531a68799284d1de9efdd7ba14c7f/arduino/FlipskyFT85BD/FlipskyFT85BD.h)

The repository describes itself as an implementation of Flipsky FTESC UART V1.4 for FT85BD and says it was tested on hardware. Those are the repository author's claims; this analysis did not independently test that hardware. The code is treated as an independent implementation, not as Flipsky's official application source or as an authoritative V1.7 specification.

## Cross-check results

| Feature | Public implementation | V1.7 executable | Result |
|---|---|---|---|
| Short frame start | `0xAA` | `0xAA` | Match |
| Length field | 1 byte | 1 byte for short frames | Match |
| Payload | CMD + DATA | INFO = CMD + DATA | Match |
| CRC | CRC-16/MODBUS, init `0xFFFF`, poly `0xA001` | Same lookup-table algorithm | Match |
| CRC byte order | High byte then low byte | High byte then low byte | Match |
| End marker | `0xDD` | `0xDD` | Match |
| Extended frame | Not implemented in this small driver | `0xBB` + 16-bit BE length | V1.7 adds capability |
| Telemetry base DATA | 28 bytes | 28-byte base layout | Match |
| Base telemetry fields | ID, error, voltage, currents, eRPM, duty, temperatures, CPU, encoder angle | Same field order/scales | Match |
| CAN wrapper | CMD `0x10`, CAN ID, nested command/data | V1.7 has CAN-forward state and command paths; exact wrapping is still being traced | Partial |
| Keepalive | CMD `0x19`, claimed ≤500 ms | V1.7 API/response maps contain CMD `0x19` | Command match; scheduling not yet confirmed |
| Speed command | CMD `0x27`, signed 32-bit BE eRPM | V1.7 request method emits CMD `0x27`, signed 32-bit BE | Match |

## Independent byte-vector check

The public implementation's example gives a one-byte INFO payload containing command `0x11` as:

```text
AA 01 11 4C 7F DD
```

The independently implemented codec in this repository generates exactly the same bytes:

```text
encode_frame(bytes.fromhex("11"))
=> aa 01 11 4c 7f dd
```

Both implementations also agree on the standard CRC-16/MODBUS check vector:

```text
CRC16("123456789") = 0x4B37
```

A regression test for the exact `AA 01 11 4C 7F DD` vector has been added to `tests/test_ftesc_frame.py`.

## V1.7 extended telemetry detail

The public V1.4-oriented Python driver parses the base telemetry layout and, for a 44-byte DATA extension, preserves 12 bytes as a reserved extension and reads a signed 32-bit PAS RPM from offsets 40–43.

The V1.7 executable's CMD `0x00` response handler gives those first 12 extension bytes a more specific interpretation:
- DATA 28–31: signed 32-bit value / 1,000,000, converted from radians to degrees;
- DATA 32–35: same;
- DATA 36–39: same;
- DATA 40–43: signed 32-bit PAS RPM.

This is a useful versioned refinement: V1.7 consumes the three fields that the V1.6 public document calls reserved, while retaining PAS RPM at the end. The exact product/UI names for the three angular values are not yet known and are deliberately left generic.

The new offline parser `parse_realtime_data_00_v17_extension` returns these three degree values and PAS RPM. Tests cover positive, negative, zero, and wrong-command inputs.

## Important differences and limitations

- The independent driver implements only the short `0xAA` frame. The V1.7 executable also supports the extended `0xBB` frame.
- The public driver labels its target as FT85BD / FTESC UART V1.4. Do not assume every V1.4 detail is identical across all FT ESC models or firmware versions.
- Its README states 460800 baud and a keepalive interval of at most 500 ms. This session did not confirm the V1.7 executable's UART baud selection path or the exact scheduler.
- The third-party code's `CAN_OVER` wrapper is useful corroboration, but the V1.7 CAN-forward byte wrapping and slave reply routing remain open.
- No third-party source code was copied into this repository. The cross-check records observations and a small independent regression vector only.

## Conclusion

The outer short-frame and CRC reconstruction is now independently corroborated by a second implementation and a concrete byte vector. The common telemetry field order/scaling and several command concepts also align. This raises confidence in the common FTESC UART subset but does not establish complete cross-model, cross-firmware compatibility or hardware correctness.
