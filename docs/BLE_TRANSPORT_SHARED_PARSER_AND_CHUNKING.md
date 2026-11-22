# V1.7 BLE transport — shared parser and transmit chunk queue

**Reference date:** 2026-11-22  
**Artifact:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Analysis:** REA 6.10.1 / Ghidra 12.2, PE32 x86  
**Scope:** static analysis only; no BLE device scan, connection, characteristic read/write, pairing or ESC command.

## Findings established

### Receive path: BLE enters the common framed-stream parser

The recovered Qt meta-call table maps the method named `bleDataRx` (method index 24 in the `FtescLowLevelFace` table) to native function `FUN_004828D0` at `0x004828D0`. Its complete decompilation shows that it takes the incoming `QByteArray` and calls `FUN_0049CA30` directly.

`FUN_0049CA30` is the incremental receive-buffer handler already mapped on the UART path. It feeds the AA/BB frame parser, retains incomplete candidates, supports concatenated frames and advances by one byte after an invalid candidate. Consequently, the V1.7 BLE receive callback reuses the same application-level AA/BB stream parser as UART. This is a direct static call-path observation, not a runtime capture.

### Transmit path: shared framed byte array and fixed 20-byte chunking

The shared lower-level send slot `FUN_00481850` (`0x00481850`) checks the BLE-connected state via `FUN_00401680`. When that state is true, it passes the same input `QByteArray` to `FUN_004050C0`. The surrounding transport-pipeline analysis identifies this shared send input as the framed packet emitted by the `uartPackData` layer.

`FUN_004050C0` iterates through the byte array in increments of `0x14` (20 decimal), constructing successive slices at offsets 0, 20, 40, and so on. It then invokes `FUN_00404E80` when the asynchronous queue is idle. The queue-pump function removes the next queued item, marks the transport busy, and constructs a completion callback that continues queue processing.

This establishes a static 20-byte application-level chunk stride and the shared outbound path. It does **not** establish that 20 bytes is a negotiated ATT MTU, an MTU-derived maximum payload, or the exact value submitted to the BLE stack at the lowest API boundary.

### Likely Qt GATT write call site — strong candidate, not fully proven

Assembly of `FUN_00404E80` shows an indirect call at `0x00404FEC`. At that call, ECX contains the BLE service object; the stack contains a local characteristic-like object, the queued `QByteArray`, and a final integer argument `1`. Ghidra resolves the computed call reference to `0x00B5A1D0`.

The call signature and argument shape strongly resemble `QLowEnergyService::writeCharacteristic(const QLowEnergyCharacteristic&, const QByteArray&, QLowEnergyService::WriteMode)`, whose mangled symbol string is present in the executable. However, `0x00B5A1D0` is within the protected Enigma region; Ghidra's decompilation reports bad instruction data and does not recover a valid Qt thunk body. A proven edge from that protected target to the mangled Qt method is still missing. Therefore the third argument value `1` is observed, but its `WriteMode` meaning is **not established**.

Evidence:
- Queue-pump assembly: `ev_c6c574f4a7ccf94925be53eafce0df3c280bdcd98d789a023f7cbfe863da9949`.
- Computed call target resolution for `0x00404FEC`: `ev_090dc82edec65beddd376fa5846a60d42657cb3321d854ee86984a3165050b51`.
- Protected target decompilation: `ev_7a13690a90241ef5b49b36e0b1b571472b9aa6f90edb1f4d180a109a5eaaf10b`.

## Qt API evidence and limitations

The executable contains the mangled symbol string for `QLowEnergyService::writeCharacteristic(const QLowEnergyCharacteristic&, const QByteArray&, QLowEnergyService::WriteMode)`. However, the PE import descriptor at RVA `0xB9F000` could not be mapped unambiguously by the import inspector, and the protected/indirect dispatch path does not yet give a proven call-site-to-import edge. The symbol string alone is not sufficient to claim the exact write mode or call target.

## Evidence references

- `FUN_004828D0` analysis: `ev_0b96fa9d9daca6528da735c37d6a4fa85f5cede2be619f08d07cfa494e6da22b`
- `FUN_00481850` analysis: `ev_0863f4b9c9cbaa26854a9389f1d2d4f01af0cd11963bc5043a68b1b315c57def`
- `FUN_00404E80` analysis: `ev_26f4ad2230070fd6a96d3322a1e2c2fb5985d8d1c5709c228825789f669a36d1`
- `FUN_004050C0` decompilation summary: `ev_60b7bb46204767a08aee7256e4a4233174fa9e248e37f18ba3545bcc7de8fce0`
- `writeCharacteristic` symbol-string search: `ev_14bbb5c07a7e3c24e7f64e40abe36d4c543e0a8939b2ffd966061e649720f728`
- PE import inspection limitation: `ev_64791b4adf0065ca2f544059fa314ba5862bbfd4c675fb96244f53cd84e50c5e`
- Original GATT UUID/lifecycle and CCCD observations remain listed in [BLE_GATT_V1_7_REVERSE_ENGINEERED.md](BLE_GATT_V1_7_REVERSE_ENGINEERED.md).
- Shared UART framing and stream parser context: [TRANSPORT_PIPELINE.md](TRANSPORT_PIPELINE.md).

## Still unknown

1. Exact call target and arguments at the final Qt GATT write boundary.
2. Write-with-response versus write-without-response mode.
3. Exact CCCD `0x2902` value and notification sequencing.
4. Negotiated ATT MTU, any negotiation policy, and whether 20-byte chunking is an invariant or a fallback.
5. BLE-side retry, failure, timeout and reconnect behavior.
6. Independent passive BLE capture and model/firmware applicability.

## Progress accounting

The static BLE transport sub-workstream rises from 60% to **80%**: the receive-to-common-parser route and the transmit queue's 20-byte segmentation are now statically established. At the time of the BLE analysis the complete-product weighted score was 72.2%; after the separate CI verification later in this session, the current score is **72.6%** (79.9 / 110 points). No live transport or desktop functionality has been added, and hardware validation remains 0%.

## Acquisition and environment note

Four V1.6 source artifacts were authorized for temporary Nextcloud checkout, but they could not yet be staged on the REA host. The only registered Gateway target is a different LXC host and it cannot reach the REA MCP endpoint or workspace. No Nextcloud source file was modified. REA's configured Apktool and ADB launchers were verified; no Android device was contacted. The caller-supplied JADX MCP JAR path remains to be verified.


## V1.6 Android cross-check — exact app-level BLE choices

The extracted V1.6 Android ARM64 application library independently implements the same 20-byte BLE chunking and shared FTESC parser:

- `BleUart::writeData` (`0x000FE09C`) loads `0x14` (20) and queues successive `QByteArray::mid` fragments.
- `BleUart::sendNextPacket` (`0x000FE1A8`) passes C++ `WriteMode=1` to a direct `QLowEnergyService::writeCharacteristic` call at `0x000FE2C4`. In Qt 5.15, this is `WriteWithoutResponse`.
- `BleUart::serviceStateChanged` (`0x000FF648`) resolves CCCD UUID `0x2902`, converts literal `0100` at `0x002851C9` to bytes and writes the descriptor. The payload `01 00` enables notifications, not indications.
- `BleUart::updateData` (`0x000FFB8C`) reaches the `BleUart::dataRx` signal thunk via the relocation at GOT `0x00881578`; the thunk (`0x0025ACD8`) calls `QMetaObject::activate`.
- `FtescLowLevelFace::bleDataRx` (`0x00234730`) copies its input then invokes `uartPackData::uartPackDataHandle(QByteArray)` via resolved relocation target GOT `0x0087D728`. This is the same application stream-parser entry used in the UART path. Signal/slot names are in the Qt metadata, but the precise constructor `QObject::connect` call site is still unresolved.

This confirms application-level behavior for Android V1.6. It strongly corroborates, but does not conclusively prove, the corresponding Windows V1.7 write mode because the Windows indirect call still lands in protected code at `0x00B5A1D0`. Do not infer an ATT MTU of 23 from 20-byte chunks; the Qt backend merely attempts MTU 512 and falls back to 23 on failure, and the negotiated outcome was not observed.

Artifact provenance:
- APK SHA-256: `26404ff6467971ff7c0fedbe1f326c6b0ccb5722571b7309d9913818960b4d7e`.
- Android ARM64 application library SHA-256: `7fba6a69f3719b70dfb7eee87c97e41aad2d8f48d1feec7058a0e5975a5ea2fc`.
- Android static reverse-engineering report: [ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md](ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md).


## ARMv7 Android cross-check

The ARMv7 app library `libFilpsky_ESC_Tool_V1.6_20251014_armeabi-v7a.so` (SHA-256 `8ba92821d1310762ae582a9cbb07918e7e1d416238ac8110be6a04063d8b0562`) confirms the same key behavior as ARM64:

- `BleUart::writeData` (`0x000C6FAC`) sets chunk size 20 at `0x000C6FD0` and calls `QByteArray::mid` at `0x000C701C`.
- `BleUart::sendNextPacket` (`0x000C70BC`) sets C++ `WriteMode=1` at `0x000C71C8` and calls Qt `writeCharacteristic` at `0x000C71F0`: `WriteWithoutResponse`.
- `BleUart::serviceStateChanged` (`0x000C8694`) constructs UUID `0x2902`, calls `QByteArray::fromHex` at `0x000C89FC`, then `writeDescriptor` at `0x000C8A10`. The ELF contains a unique `0100` literal at `0x0026F7D9`, but a direct literal xref was not recovered; treat exact ARMv7 CCCD bytes as a high-confidence cross-check, while the ARM64 `01 00` value remains the direct proof.
- `FtescLowLevelFace::bleDataRx` (`0x00202DC8`) resolves first to the QByteArray copy constructor (GOT `0x00809294`) and then to `uartPackData::uartPackDataHandle(QByteArray)` (GOT `0x0080E13C`).

Thus both Android ABIs share 20-byte chunking, WriteWithoutResponse and the common FTESC stream parser. This still does not prove the Windows V1.7 protected indirect call target, the signal-slot connection site, negotiated ATT MTU or live behavior.
