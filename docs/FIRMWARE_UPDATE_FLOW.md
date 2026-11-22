# V1.7 firmware update: authentication, erase, block transfer and retries

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**QML invokable:** `firmwareUpdatePro`, native `0x00486570`  
**Flash orchestrator:** `FUN_00485130`  
**Erase-and-wait helper:** `FUN_00484C50`  
**Analysis date:** 2026-11-22

> Correction to the earlier revision of this report: `0x00485130` is **not** a firmware-image validator. It is the erase-and-block-write orchestrator. The traced update path does not show the previously claimed ESP-style `0xE9` image-magic check. That claim is withdrawn.

## 1. Firmware selection and preflight gates

The `firmwareUpdatePro` function:
- requires an active connection;
- rejects a second argument other than `0xAC` (the API sentinel's meaning is not established);
- supports a built-in resource path `:/ftescFw/%1` and a custom firmware file path;
- checks that the loaded image size does not exceed `0x30F98` bytes (200,600 bytes);
- contains a UI warning saying firmware must not exceed 150 Kbyte (153,600 bytes).

The native size bound and UI warning do not match. The smaller UI limit is what the user sees; the native guard is a separate implementation fact. Neither number is a statement of firmware compatibility.

The app warns that incorrect firmware can damage the ESC. Its UI also says firmware updates cannot be completed while targeting a CAN slave; to update a slave, connect USB directly to that ESC. The update instructions require entering bootloader, reconnecting the ESC, starting the flash, and reconnecting after completion.

## 2. UUID / TEA authorization preflight

The orchestrator:
1. Sends `ftescObtainUuid`, CMD `0x21`.
2. Waits up to 2,000 ms for the UUID acknowledgement signal.
3. Builds the 16-byte ASCII challenge `0123456789abcdef`.
4. Encrypts it with the device-returned UUID as the 16-byte TEA key:
   - TEA block transform: `0x00481B30`;
   - buffer wrapper: `0x00481BC0`;
   - 16-byte challenge = two 8-byte TEA blocks.
5. Sends the 16-byte ciphertext using `writeMcuEncrypt`, CMD `0x22`.
6. Waits up to 2,000 ms for the encryption-success acknowledgement.
7. On successful authorization, calls `FUN_00485130` to erase and flash.

The TEA routine performs 32 rounds with delta `0x9E3779B9` and reads four 32-bit key words. This confirms TEA in the firmware authorization handshake; it does not establish that normal telemetry or motor-control messages are encrypted.

Timeout return values observed in the orchestrator:
- UUID wait timeout: `-6`;
- encrypted-response wait timeout: `-7`.

No UUID or device-specific key material is stored in this repository.

## 3. Erase request

The flash orchestrator calls `FUN_00484C50(image_size)`. That helper calls the UartComm request builder `FUN_00495FE0`, which constructs:
- command byte `0x16`;
- 32-bit big-endian firmware image size.

The helper then waits for the erase response and updates the UI with “Erase done”, “Erase timed out” or “Erasing buffer failed”.

The response dispatcher maps CMD `0x16` to UartComm signal index 4, `ftescFirmwareEraseRespenseFlag` (the misspelling is present in the binary's symbol/signature string).

## 4. Block transfer

After erase succeeds, `FUN_00485130` processes the image in sequential chunks:

| Property | Observed V1.7 value |
|---|---:|
| Maximum block data | `0xF0` = 240 bytes |
| Write command | `0x18` |
| Timeout per attempt | 2,000 ms |
| Retry count | Up to 3 attempts per block |
| Retry condition | Timeout; non-timeout failure exits the retry loop |
| Block index in CMD 0x18 payload | No explicit index observed |
| Sequence | Sequential chunks from the image |

Each chunk is passed to `FUN_004960E0`, which:
1. starts a fresh per-block XOR sequence;
2. uses `0xD0` for byte 0;
3. XORs later bytes with the table at image VA `0x00530F61`, starting at table index 0 for byte 1;
4. prepends command byte `0x18`;
5. sends the INFO payload through the shared UartComm send path.

The XOR mask table required for the 240-byte block has 239 bytes. It has been recovered into the offline codec; no table index beyond byte 238 is needed because the block limit is 240 bytes.

The response dispatcher maps CMD `0x18` to UartComm signal index 6, `ftescFirmwareWriteBlockSuccessFalg` (the spelling is as present in the binary). The flash loop advances progress after a successful block. Three consecutive timeouts result in “Flashing Timed out”; a negative block result produces “Flashing failed”.

## 5. Whole-image CRC observation

The updater calls `FUN_0049C7A0(image_bytes, image_size)`, which computes CRC-16/MODBUS over the entire firmware image. It then constructs a temporary big-endian size-plus-CRC byte array.

The exact downstream consumer of this temporary buffer is not yet resolved. It is **not** currently assigned to the erase request or any other transmitted field in the offline codec. The observed erase builder `FUN_00495FE0` sends the size field only.

## 6. Offline implementation added

The repository now contains:
- `scripts/ftesc_firmware.py`
  - `build_erase_info(image_size)`;
  - `transform_firmware_block(block)` (symmetric XOR encode/decode);
  - `build_write_info(block)`;
  - `iter_firmware_write_info(image)`;
  - `iter_firmware_write_frames(image)`;
  - `firmware_image_crc16(image)`.
- `tests/test_ftesc_firmware.py`: 11 tests for size encoding, 240-byte blocks, per-block XOR reset, exact first mask bytes, transform symmetry, CRC and outer framing.

These functions only construct offline byte arrays/frames. They do not open serial/BLE, enter bootloader, erase flash or transmit firmware.

## 7. Remaining unknowns

- Exact semantics of the API sentinel `0xAC`.
- Exact meaning/consumer of the temporary whole-image size+CRC buffer.
- Whether the bootloader uses any additional state outside the observed desktop update flow.
- Full firmware-image container format and compatibility checks (no `0xE9` magic check was established in the traced path).
- Whether the 150-Kbyte UI limit or 200,600-byte native bound applies to every model/build.
- Runtime acknowledgement behavior, block ordering and retry behavior on real hardware.
- The XOR table may differ across app versions or ESC firmware versions; this table is from the analyzed V1.7 executable only.

## 8. Safety and scope

No firmware was flashed, no bootloader was entered and no ESC command was sent. A successful TEA authorization does not imply an arbitrary firmware image is compatible or safe. Never use the offline frame builders as a reason to flash unverified firmware.


## 8. Official update procedure cross-check

Flipsky's official [FT Series V1.6 update guide](https://flipsky.net/blogs/vesc-tool/how-to-update-ft-series-esc-to-v16) describes entering bootloader, reconnecting after the bootloader LED indication, then starting the flash. For dual-drive controllers it says the master and slave are updated independently through their respective USB connections.

This matches the application-level separation between boot-mode, erase and block-write commands. It also supports keeping CAN-slave firmware flashing out of the inferred normal path. The official guide is V1.6; it is used as procedural context, not as proof of the exact V1.7 bootloader implementation.
