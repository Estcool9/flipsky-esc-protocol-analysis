# V1.6 Android native ValueSetup codec and firmware protocol analysis

**Analysis date:** 2026-11-22  
**APK SHA-256:** `26404ff6467971ff7c0fedbe1f326c6b0ccb5722571b7309d9913818960b4d7e`  
**ARM64 application library SHA-256:** `7fba6a69f3719b70dfb7eee87c97e41aad2d8f48d1feec7058a0e5975a5ea2fc`  
**Method:** static ARM64 disassembly and relocation resolution with Rizin 0.9.1; no binary or firmware execution.

## 1. ValueSetup XML parser: the wire order is explicitly ValueSeque

The native parser `ValueSetups::configValueStreamXml(QXmlStreamReader&)` is at `0x002539E8` (7,740 bytes). Its control flow establishes the division between data definitions, serialization order and presentation groups.

- It reads the XML element name using `QXmlStreamReader::name()` / `QStringRef::toString()`.
- At `0x00254C30–0x00254C3C`, it compares the current element name to the literal `ValueSeque` at VA `0x00296BAA`.
- It clears the native sequence list at `ValueSetups + 0x28` through the resolved QList helper.
- It advances through each child start element; at `0x00254CCC–0x00254CD8` it compares the child name to literal `seque` at VA `0x00296BB5`.
- For each `seque` element it calls `QXmlStreamReader::readElementText()` at `0x00254D08`, then calls the resolved `QList<QString>::append(QString const&)` relocation at `0x00254D18` (PLT stub `0x000F9C20`, GOT slot `0x00886458`).

This directly proves that XML `ValueSeque` order populates the QList at object offset `+0x28`. That is the exact list later traversed by the serializer and response decoder. It is not inferred from the XML child order or parameter names.

The following `Clustering` branch is separate: the parser compares `Clustering` at `0x00254E00`, clears a different group list at `+0x30` (`0x00254E48`), and calls `ValueSetups::incValueCluster(QString)` at `0x00254F9C`. Subsequent nested-group parsing populates presentation metadata, not the wire-order list.

The ValueSetup object maintains both a name-keyed hash (at `+0x18`) and the explicit ordered QList (at `+0x28`). `Values` supplies the keyed metadata/objects; `ValueSeque` decides which IDs are serialized and in what order; `Clustering` supplies UI grouping.

## 2. Marker-prefixed setup block construction and validation

Native functions:

| Function | Address | Size |
|---|---:|---:|
| `ValueSetups::valueArralize(ValueByteArr&, unsigned int)` | `0x0025324C` | 172 |
| `ValueSetups::valueDeArralize(ValueByteArr&, unsigned int)` | `0x002532F8` | 400 |
| `ValueSetups::obtainValuesArray(ValueByteArr&, QString const&)` | `0x002519B4` | 1,212 |
| `ValueSetups::setValuesArray(ValueByteArr&, QString const&, QObject*)` | `0x00251E70` | 1,936 |
| `ValueSetups::loadValueStreamXml(QString)` | `0x00256434` | 708 |
| `ValueSetups::saveValueStreamXml(QString)` | `0x002566F8` | 588 |

`valueArralize` first appends its caller-supplied marker through `ValueByteArr::valueDecomposeU32`, then iterates the QList at `this+0x28` in index order and calls `obtainValuesArray` for each ID.

`valueDeArralize` reads the first four bytes through `valueComposeU32`, compares that decoded marker with the expected marker argument, and only then iterates the same ordered QList and calls `setValuesArray`. This is a marker comparison, not a data-length comparison.

Therefore, an ordered setup block is:

1. caller-selected 32-bit marker, encoded big-endian;
2. the encoded parameter values resolved from the Values map, following the exact `ValueSeque` list order;
3. no automatic alphabetical sorting and no implicit serialization of Values entries absent from ValueSeque.

The offline Python implementation in `scripts/ftesc_setup_serializer.py` already follows this design through `encode_profile_block` and `decode_profile_block`.

## 3. Native ValueByteArr primitive codec

Native primitive functions:

| Method | Address | Bytes |
|---|---:|---:|
| `valueComposeI8` / `valueDecomposeI8` | `0x24DB0C` / `0x24E060` | 1 |
| `valueComposeU8` / `valueDecomposeU8` | `0x24DB38` / `0x24E0D8` | 1 |
| `valueComposeI16` / `valueDecomposeI16` | `0x24DB64` / `0x24E150` | 2 |
| `valueComposeU16` / `valueDecomposeU16` | `0x24DC18` / `0x24E1F8` | 2 |
| `valueComposeI32` / `valueDecomposeI32` | `0x24DCCC` / `0x24E2A0` | 4 |
| `valueComposeU32` / `valueDecomposeU32` | `0x24DDA0` / `0x24E38C` | 4 |
| `valueComposeD16` / `valueDecomposeD16` | `0x24DF10` / `0x24E4AC` | 2 |
| `valueComposeD32` / `valueDecomposeD32` | `0x24DE74` / `0x24E478` | 4 |
| `valueComposeDA32` / `valueDecomposeDA32` | `0x24DF5C` / `0x24E4E8` | 4 |

All integer methods operate big-endian/network byte order. For example, I/U16 read or append the most-significant byte first; I/U32 read or append bytes in 24,16,8,0 bit order.

### Complete native valueTET mapping

| valueTET | Native value codec | Wire representation |
|---:|---|---|
| 1 | U8 | unsigned 8-bit |
| 2 | I8 | signed 8-bit, two's complement |
| 3 | U16 | unsigned 16-bit, big-endian |
| 4 | I16 | signed 16-bit, big-endian |
| 5 | U32 | unsigned 32-bit, big-endian |
| 6 | I32 | signed 32-bit, big-endian |
| 7 | D16 | signed I16 divided/multiplied by `evalScl` |
| 8 | D32 | signed I32 divided/multiplied by `evalScl` |
| 9 | DA32 | IEEE-754 binary32, big-endian |

In the native `ValueSetup` object, the outer value type is at offset `+0x00`, current double at `+0x18`, current integer at `+0x20`, transmit-type (`valueTET`) at `+0x58`, and numeric scaling factor at `+0x60`. `obtainValuesArray` and `setValuesArray` dispatch on these fields and call the matching primitive methods.

The DA32 encoder/decode routines manually pack/unpack IEEE-754 binary32 sign, exponent and mantissa; the float is not a bespoke 16-bit format. The Python implementation uses `struct.pack(">f")` / `unpack(">f")`, which matches the native binary32 representation.

### Exact scaling and rounding rule

The native helper at `0x24DEBC` rounds scaled values to nearest integer with half-way cases **away from zero**:

- for non-negative inputs it adds 0.5 then rounds down;
- for negative inputs it subtracts 0.5 then rounds up.

Thus `+123.5 → +124` and `-123.5 → -124`. The existing Python `_round_away_from_zero` helper matches this. New regression tests now explicitly exercise negative halfway cases and IEEE negative-zero preservation.

## 4. Firmware authorization preflight: TEA and secret-key ACK

Native functions:

| Function | Address | Size |
|---|---:|---:|
| `FtescLowLevelFace::firmwareUpdatePro(...)` | `0x0023316C` | 2,868 |
| `FtescLowLevelFace::encrypt(unsigned char*, unsigned short, unsigned char*)` | `0x00233048` | 292 |
| `FtescLowLevelFace::tea_encrypt(unsigned int*, unsigned int*)` | `0x00232F08` | 320 |
| `UartComm::writeMcuEncrypt(ValueByteArr&)` | `0x0024AFE0` | 280 |
| `UartComm::ftescMotorSignalSecretKeyCheckAck(int)` | `0x002814A4` | 132 |
| `FtescLowLevelFace::ValueSecretKeyCheckedSlot(int)` | `0x0023428C` | 84 |

The `encrypt` function zero-pads to an 8-byte multiple, then applies TEA to 64-bit blocks (two 32-bit words), using a four-word/128-bit key, 32 rounds and delta `0x9E3779B9`. `firmwareUpdatePro` calls this function at `0x00233978` with a 16-byte input and a 16-byte key loaded from static native data. The static key bytes are intentionally not reproduced in this repository report.

The result is handed to `UartComm::writeMcuEncrypt(ValueByteArr&)` at `0x0024AFE0`. That method constructs a one-byte `0x22` value prefix, replaces the following 16-byte region with the encrypted buffer, and passes the resulting byte array to `UartComm::uartSendDataToFtesc`. This establishes a distinct authorization/preflight request before the firmware erase/write stages; it is not itself the firmware image block transfer.

The native Qt metaobject contains signal `2ftescMotorSignalSecretKeyCheckAck(int)` and slot `1ValueSecretKeyCheckedSlot(int)`. The preflight path uses a 2,000 ms timer and waits for this ACK. The slot sets its internal secret-valid flag only when the ACK integer equals **0**; `-1` and other non-zero values leave the flag invalid. The UI exposes an `Invalid SecretKey` failure string.

The full challenge generation and device-side validation semantics remain unresolved. In particular, the presence of a static application-side TEA key does not prove the key is universal across ESC models or firmware families.

## 5. Firmware erase and block-write pipeline

Native functions:

| Function | Address | Size |
|---|---:|---:|
| `FtescLowLevelFace::eraseFirmware(unsigned int)` | `0x00230BF0` | 692 |
| `FtescLowLevelFace::firmwareWriteToFtesc(QByteArray&)` | `0x002310B4` | 1,396 |
| Per-block helper | `0x00231628` | 156 |
| `UartComm::ftescEraseFirmware(unsigned int)` | `0x0024A558` | 232 |
| `UartComm::ftescWriteFirmware(QByteArray&)` | `0x0024A640` | 544 |
| `UartComm::ftescFirmwareEraseRespenseFlag(bool)` | `0x00281280` | 136 |
| `UartComm::ftescFirmwareWriteBlockSuccessFalg(bool)` | `0x0028138C` | 136 |

### Erase phase

The UartComm erase message builder uses byte/tag `0x16` and dispatches through `uartSendDataToFtesc`. The higher-level `FtescLowLevelFace::eraseFirmware` waits on a separate boolean erase-response signal using a 20,000 ms timeout. Its response path distinguishes success, timeout (`-10`) and link/error cases. This is not a single fire-and-forget function call.

### Write phase and transform

The UartComm firmware writer starts its write message using byte/tag `0x18`, transforms input bytes with a 256-byte static XOR lookup table, then appends the transformed stream to a message sent through the common FTESC transport. The table index is based on the low eight bits of the input offset, so the transform repeats every 256 bytes. This is recorded as a bytewise XOR/obfuscation layer; it is not described as modern cryptographic encryption or as an integrity/authentication mechanism.

The actual lookup table values are not reproduced here. The remaining message fields/secondary type tags in the native writer still require correlation with the matching receive/ACK logic.

### Block sizing and retries

`FtescLowLevelFace::firmwareWriteToFtesc` first calls the erase routine, then divides the input into chunks of at most **240 bytes** (`0xF0`) using `QByteArray::mid`. Each chunk is passed to the per-block helper at `0x00231628`.

The helper makes at most **three total attempts**. It waits for the block response (the associated response wait helper uses a 2,000 ms timer), checks the response handler at `0x00234CFC`, and:
- repeats only when the response result is `-10`;
- returns other response codes immediately;
- returns `-20` once all three attempts have been consumed.

The response flag is exposed through `UartComm::ftescFirmwareWriteBlockSuccessFalg(bool)`. The exact on-wire ACK payload and the semantics of every non-`-10` status are not fully mapped yet.

## 6. Confirmed vs unresolved

**Statically established for Android V1.6 ARM64:**
- XML `ValueSeque` is copied into the native ordered QList used by setup serialization/deserialization.
- Setup blocks use a caller-supplied big-endian U32 marker, which the decoder checks before parsing the ordered values.
- All nine `valueTET` encodings, their signedness/widths, big-endian order and scaled rounding rule are mapped.
- Firmware preflight uses TEA with 16-byte input and embedded 128-bit key material, then a `0x22` request and integer ACK validation.
- Firmware erase is a separate `0x16` operation with a response wait.
- The writer uses a `0x18` path with bytewise XOR transform, 240-byte maximum chunks and at most three total attempts per block.

**Still unresolved:**
- exact plaintext/challenge source and device-side secret-check protocol semantics;
- how the static key is provisioned/selected for each model or firmware generation;
- complete erase envelope, flash sectors/addressing and success response mapping;
- all write envelope fields and the meaning of secondary tags;
- exact ACK payload correlation, sequence/block numbering and progress accounting;
- whole-image integrity/signature/authentication beyond the static TEA preflight and XOR layer;
- mapping of the 17 embedded images to exact MCU, ESC model, SKU and board revision;
- partial-update recovery, resume/rollback and bootloader recovery semantics;
- V1.6 Android vs Windows V1.7 firmware behavior differences and real hardware outcomes.

The static firmware-analysis sub-workstream is estimated at **75%**: the main client-side preflight, erase/write path, block size, retry ceiling and obfuscation layer are now mapped, while the device-side validation, model mapping, complete frame schema and failure recovery remain open. The whole-product project score remains **72.6%** (79.9 / 110) because this is analysis evidence, not a tested open-source firmware-updater implementation or hardware validation.

## Safety and execution record

- No APK/native library was executed.
- No Android handset was contacted.
- No BLE scan, pairing, connection, GATT read or write was performed.
- No UART/CAN traffic was sent and no ESC command was issued.
- No bootloader operation or firmware flash was attempted.
- The embedded TEA key bytes and XOR lookup table contents are not reproduced.
