# Windows V1.6 numeric readers and response codec parity

**Reference date:** 2026-11-22  
**Artifact:** `Flipsky_ESC_Tool_V1.6_20260912.exe`  
**SHA-256:** `051d57a776782ae8daaeaa45179f9b568f7e89b4a78ab8dd8e558ecd3e53b968`  
**Provider:** Ghidra 12.2 through REA; Gateway SSH to the REA host  
**Scope:** static decompilation; no binary execution or hardware communication.

## 1. Shared byte readers

The V1.6 response dispatcher `FUN_004948d0` and profile-value decoder `FUN_0049a5c0` use the following low-level readers. Every multibyte value is assembled in network/big-endian order from the current QByteArray/QDataStream cursor.

| Function | Raw width | Raw interpretation | Cursor advance | Evidence in the decompilation |
|---|---:|---|---:|---|
| `FUN_00496d80` | 1 byte | raw U8 storage; callers cast to `char` when signed interpretation is needed | 1 byte if available | reads byte at current data pointer and calls stream advance helper with size 1 |
| `FUN_00496dc0` | 1 byte | raw U8 | 1 byte if available | same one-byte cursor read; used for command IDs and ID vector elements |
| `FUN_00496e00` | 2 bytes | raw U16 bit pattern; callers cast to `short` for S16 | 2 bytes if available | reads first byte into high octet and second into low octet |
| `FUN_00496e50` | 2 bytes | raw U16 | 2 bytes if available | same big-endian 16-bit assembly; unsigned callers mask with `0xFFFF` |
| `FUN_00496ea0` | 4 bytes | raw U32 bit pattern; signedness is imposed by the caller | 4 bytes if available | assembles b0<<24, b1<<16, b2<<8, b3 |
| `FUN_00496f00` | 4 bytes | U32, used for marker comparisons | 4 bytes if available | same big-endian 32-bit assembly |
| `FUN_00496f60` | 4 bytes via `FUN_00496ea0` | **S32 / divisor** | 4 bytes if available | stores the raw reader result in an `int`, converts with signed integer-to-float semantics, divides by the supplied divisor |
| `FUN_00496f90` | 2 bytes via `FUN_00496e00` | **S16 / divisor** | 2 bytes if available | explicitly assigns raw reader to `short`, then divides by the supplied divisor |

The raw reader and signedness wrapper must not be conflated. `FUN_00496ea0` and `FUN_00496e00` return raw bit patterns in Ghidra's recovered type signatures; `FUN_00496f60` and `FUN_00496f90` establish signed interpretation for scaled response values.

### Truncation behavior

The byte readers initialize their return value to zero. When fewer than the required bytes remain, they do not perform a read/advance and return that default zero. The native reader alone therefore does not provide a typed short-buffer error. The offline decoders use strict DATA-length validation before calling `_signed_i32`; setup decoders use checked cursor reads and raise `SetupValueError`. Keep these checks rather than emulating the native zero-on-underflow behavior in the offline API.

## 2. Confirmed response layouts

### CMD 0x0D — PPM

`FUN_004948d0` reads one S32 through `FUN_00496f60(1,000,000)` and passes the resulting scalar to `FUN_004b5a10` / signal index 14 `signalPPMRecAck`.

- DATA size: 4 bytes.
- Encoding: signed int32, big-endian.
- Scale: divide by 1,000,000.
- Offline implementation: `parse_signal_ppm_response()`.
- Existing negative-value regression: `-500000 -> -0.5`.

### CMD 0x0E — ADC

The handler reads six S32 values in this order, each through `FUN_00496f60`, then emits `FUN_004b5a60` / signal index 15 `signalADCRecAck`.

| Index | DATA offset | Size | Native divisor |
|---:|---:|---:|---:|
| 0 | 0 | 4 | 1,000,000 |
| 1 | 4 | 4 | 1,000,000 |
| 2 | 8 | 4 | 1 |
| 3 | 12 | 4 | 1 |
| 4 | 16 | 4 | 1 |
| 5 | 20 | 4 | 1,000,000 |

- Total DATA size: 24 bytes.
- All values: signed int32, big-endian.
- Offline implementation: `parse_signal_adc_response()`.
- Existing tests cover positive and negative values and all six divisors.

### CMD 0x29 — IMU calibration

The handler makes nine consecutive `FUN_00496f60(1,000,000)` calls, then emits `FUN_004b5b90` / signal index 18 `imuCalibrationReceived`.

- DATA size: 36 bytes.
- Nine signed int32 values, big-endian.
- Each value is divided by 1,000,000.
- Semantic axis/field labels remain unknown; the offline model keeps a nine-value tuple.
- Offline implementation: `parse_imu_calibration_response()`.
- Tests now cover negative values and scaling as well as exact 36-byte length validation.

### CMD 0x00 — one-shot telemetry cross-check

The V1.6 pseudocode reads the following sequence using the same S16/S32 wrappers:

| DATA offset | Width | Native reader/divisor | Recovered interpretation |
|---:|---:|---|---|
| 0 | 1 | `FUN_00496dc0` | MCU/controller ID |
| 1 | 1 | `(char)FUN_00496d80` | signed error byte |
| 2 | 2 | `FUN_00496f90(100)` | battery voltage |
| 4 | 4 | `FUN_00496f60(1e6)` | battery current |
| 8 | 4 | `FUN_00496f60(1e6)` | motor current |
| 12 | 4 | `FUN_00496f60(1)` | motor electrical RPM |
| 16 | 2 | `FUN_00496f90(10000)` | duty |
| 18 | 2 | `FUN_00496f90(100)` | MOSFET temperature |
| 20 | 2 | `FUN_00496f90(100)` | motor temperature |
| 22 | 2 | `FUN_00496f90(10000)` | CPU utilization |
| 24 | 4 | `FUN_00496f60(1e6)` | encoder angle |
| 28 | 4 | `FUN_00496f60(1e6)`, then radians-to-degrees | additional angular value 1 |
| 32 | 4 | `FUN_00496f60(1e6)`, then radians-to-degrees | additional angular value 2 |
| 36 | 4 | `FUN_00496f60(1e6)`, then radians-to-degrees | additional angular value 3 |
| 40 | 4 | `FUN_00496f60(1)` | PAS RPM |

Total DATA length is 44 bytes. The first two IDs are raw bytes; the two-byte and four-byte numeric fields use the signed scaled wrappers above. The three angular values and PAS RPM agree with the V1.7 telemetry reconstruction. The exact names of the three extra angular values remain intentionally generic.

## 3. Setup ValueSeque typed-reader cross-check

The same reader families are used inside `FUN_0049a5c0` when it applies a ValueSetup entry:

- Floating `valType=1`: valueTET 7 uses signed S16 with its `evalScl` divisor; valueTET 8 uses signed S32 with its divisor; valueTET 9 reads a float32.
- Integer `valType=2`: valueTET 1/2 = U8/S8, 3/4 = U16/S16, 5/6 = U32/S32.
- Remaining native categories 4/6/7 read one signed byte in the observed switch.
- The metadata-driven offline `decode_profile_block()` uses big-endian signed/unsigned reads and preserves the caller-supplied `ValueSeque` order.

This supports reuse of the existing profile decoder for V1.6 single-block commands 0x09/0x0A and the V1.7 combined 0x1C response. It does not establish undocumented XML semantics or model-specific parameter names.

## 4. CMD 0x14 text termination parity correction

The V1.6 `uartPackHandle` CMD14 branch walks the DATA byte array from its start until the first NUL byte or the end of the supplied length, then constructs the terminal QString from only that prefix before calling `ftescTermialPrint` (signal index 12).

CMD24 takes a different path: it passes the complete QByteArray to `ftescSamplesPrint` (signal index 13), so an embedded NUL byte does not bound the byte array.

The offline `parse_text_response()` previously decoded all CMD14 DATA, including bytes after the first NUL. It now:
- truncates CMD14 raw bytes at the first `0x00`;
- preserves the complete CMD24 raw QByteArray, including embedded NUL bytes.

A regression test pins both behaviors. Text encoding still uses UTF-8 with replacement for display; no live device capture is available to validate every possible character encoding.

## 5. Offline parity conclusion

For the recovered Windows V1.6 response readers:

- PPM, ADC and IMU numeric widths, big-endian order, signedness and scale factors match the existing offline decoders.
- CMD00 telemetry field widths/scales match the existing extended telemetry model.
- No numeric codec change was required; the new tests increase coverage of signed IMU values.
- CMD14 did contain a native-vs-Python length discrepancy and is now corrected; CMD24 deliberately retains full byte-array length.

The remaining gaps are not these primitive integer readers. They are semantic naming of ADC/IMU fields, CMD01 meaning, additional setup/motor-signal variants, firmware state/ACK correlation, protected encryption helper behavior, and runtime/hardware validation.

## 6. Safety and provenance

- Evidence is static decompilation from the hashed V1.6 Windows PE; it is not original source.
- No Flipsky executable was run.
- No ESC was connected and no UART/CAN/BLE bytes were transmitted.
- No firmware was flashed.
- No key bytes, protected tables or device-specific secret material are included.


## 7. Latest regression verification

GitHub Actions run #295 (`45055846796`, head `0d20a0eb95bffc42f94563ebcaf0df0f832364fb`) passed **174 tests, 0 failures**. The test for CMD14 NUL termination versus CMD24 full QByteArray and the negative IMU signed-S32 scale test both appear as passing in the log. The same workflow restored compressed research artifacts, rebuilt the parameter catalog and ordered setup profiles, ran the suite and compiled Python sources.

Run: https://github.com/Estcool9/flipsky-esc-protocol-analysis/actions/runs/45055846796
