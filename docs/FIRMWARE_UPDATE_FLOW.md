# V1.7 firmware-update preflight and authentication flow

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Orchestrator:** `firmwareUpdatePro`, native `0x00486570`  
**File validator:** `0x00485130`  
**Analysis date:** 2026-11-22

## 1. Important distinction

The method named `firmwareUpdatePro` is not, by itself, the entire flash loop. Its decompiled body performs file validation and a UUID-based TEA challenge/response preflight. The separate UartComm methods issue boot-mode, erase and block-write commands.

## 2. Observed preflight sequence

1. The application validates the supplied firmware byte array through `FUN_00485130`.
2. It requests the ESC UUID using `ftescObtainUuid`, command `0x21`.
3. It waits for UartComm signal index 1, `ftescGetUuidAck`, using a local event-loop/timer path with a 2,000 ms timeout.
4. It constructs a fixed 16-byte challenge whose ASCII contents are `0123456789abcdef`.
5. It encrypts the 16-byte challenge using the UUID returned by the ESC as the TEA key:
   - block transform: `0x00481B30`;
   - buffer wrapper: `0x00481BC0`;
   - two 8-byte TEA blocks are processed because the challenge is 16 bytes.
6. It sends the resulting 16-byte ciphertext through `writeMcuEncrypt`, command `0x22`.
7. It waits for UartComm signal index 2, `writeEncryptSuccess`, again with a 2,000 ms timeout.
8. It validates the firmware image again before returning the result to the caller.

The UUID value itself is device-provided. No UUID, key value or device-specific secret is included in this report.

## 3. TEA implementation details

The block routine at `0x00481B30`:
- operates on two 32-bit words (64-bit block);
- performs 32 rounds;
- uses the standard TEA delta `0x9E3779B9` (decompiler displays the equivalent subtraction constant `0x61C88647`);
- reads four 32-bit key words from the supplied 16-byte key buffer.

The buffer wrapper at `0x00481BC0`:
- rounds the input length up to a multiple of 8;
- zero-pads the tail if required;
- applies the block transform to each 8-byte block.

This confirms TEA is used in the firmware authorization handshake. It does not prove ordinary telemetry or motor-control INFO messages are encrypted.

## 4. Separate firmware command methods

The UartComm request methods are separate native functions:

| Method | Command | Observed role |
|---|---:|---|
| `ftescObtainFwVerSlot` | `0x11` | Read firmware version/identity |
| `ftescJPMBootMode` | `0x13` | Enter boot mode |
| `ftescEraseFirmware` | `0x16` | Send erase request plus supplied bytes |
| `ftescWriteFirmware` | `0x18` | Send firmware block after bytewise XOR transform |

The CMD `0x18` writer starts its XOR state at `0xD0` and advances through a byte table at `0x00530F61`. This is a separate transformation from the TEA challenge/response. The table contents are intentionally not reproduced in this report.

The exact order, block numbering, retries, acknowledgement progression and bootloader transitions are not all recovered from the preflight method and remain separate work.

## 5. Firmware image validation

The validator at `0x00485130` inspects the image structure rather than accepting an arbitrary byte array. The first byte is checked against `0xE9`, followed by length/segment checks and a checksum-related path.

This is evidence for a structured firmware-image format. The exact vendor image specification has not been identified, so the report does not label it as a particular MCU vendor format.

The binary contains a file-size bound of `0x30F98` bytes in this validation path. A separate UI warning in the application mentions a smaller firmware-size limit; those two limits have not yet been reconciled and should not be treated as interchangeable.

## 6. Timeout and failure behaviour

- UUID acquisition timeout: 2,000 ms; the orchestrator returns an error path (decompiler result `-6`).
- Encryption acknowledgement timeout: 2,000 ms; the orchestrator returns an error path (decompiler result `-7`).
- Firmware-image validation failure is returned separately from those timeout paths.

The UartComm timer slot also maintains independent request/response counters; see [TRANSPORT_PIPELINE.md](TRANSPORT_PIPELINE.md).

## 7. Safety and scope

No firmware was flashed, no bootloader was entered and no ESC command was sent. This is static analysis of the desktop application plus offline tests. A valid cryptographic response does not imply that an arbitrary firmware image is compatible or safe.
