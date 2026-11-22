# Flipsky ESC Tool V1.7 — BLE GATT reconstruction

**Artifact:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Static analysis:** Ghidra 12.2 / REA, PE32 x86  
**Status:** partial static reconstruction; no BLE device was connected and no GATT operation was executed.

## Confirmed GATT identifiers

The native `BleUart` constructor initializes three distinct UUID values and stores them in separate object fields:

| Role in the Flipsky implementation | UUID | Native field |
|---|---|---|
| BLE UART service | `0000fff0-0000-1000-8000-00805f9b34fb` | `this + 0x28` |
| TX characteristic | `0000fff2-0000-1000-8000-00805f9b34fb` | `this + 0x2C` |
| RX characteristic | `0000fff1-0000-1000-8000-00805f9b34fb` | `this + 0x30` |

The constructor's string references are at VAs `0x005206A0`, `0x005206C8`, and `0x005206F0`. The code assigns the first UUID to the service member and the latter two to distinct characteristic members. The corresponding string/xref/decompile observations are retained in the REA investigation; the regex UUID search is evidence `ev_c20b6860d554e3552d2dc6b82cebf19613220d0aa60f1a9439454420eac9ed7c`.

## Recovered control flow

The following native functions were decompiled and correlated with the Qt meta-object strings:

| Function | Observed responsibility | Confidence |
|---|---|---|
| `FUN_004051C0` | Constructs the `BleUart` object and initializes service/TX/RX UUID members | High |
| `FUN_00402ED0` | Initializes the `QLowEnergyController`, resets state flags, and connects controller signals including service discovery, connected/disconnected, error, state change and connection update | High |
| `FUN_004016B0` | Handles a discovered service and sets the service-found flag after matching its UUID | High |
| `FUN_004023D0` | Creates the `QLowEnergyService` object from the service UUID and connects service state/error/characteristic/descriptor signals | High |
| `FUN_00401920` | Handles service state; checks that the TX and RX characteristics exist; reports explicit missing-characteristic errors | High |
| `FUN_00402000` | Receives the `characteristicChanged(QLowEnergyCharacteristic,QByteArray)` callback | High for callback identity; payload handling is not yet fully resolved |
| `FUN_00401810` | Handles/logs controller connection | High |
| `FUN_00402120` | Handles/logs connection-parameter updates | High |
| `FUN_00401EB0` / `FUN_00402830` | Service/controller error paths | High |
| `FUN_00402A30` / `FUN_00402390` | Service-disconnect and cleanup paths | High |
| `FUN_00403810` | Qt meta-call destination associated with the `BleUart` method table; its exact relationship to the public `writeData` / `sendNextPacket` names still needs caller and payload tracing | Partial |

The binary contains Qt Bluetooth imports/types for `QBluetoothDeviceDiscoveryAgent`, `QBluetoothDeviceInfo`, `QBluetoothUuid`, `QLowEnergyController`, `QLowEnergyService`, `QLowEnergyCharacteristic`, and `QLowEnergyDescriptor`. It also contains explicit strings for:

- `BLE UART service not found`
- `BLE Tx characteristic not found`
- `BLE Rx characteristic not found`
- `BLE device connected`
- `BLE service disconnected`
- `BLE connection parameters updated`

The service-state handler looks up descriptor UUID `0x2902` (the Client Characteristic Configuration Descriptor). This is consistent with a characteristic-notification setup path, but the exact descriptor value/write mode has **not** yet been established from a passive GATT capture. Do not hard-code a notification value solely from this static observation.

The controller setup contains a timer call with literal argument `70000`; its exact units and semantic timeout should be cross-checked against the called Qt timer wrapper before treating it as a protocol timing constant.

## Transport direction and current unknowns

The class metadata includes the method names `writeData` and `sendNextPacket`, plus the signal names `dataRx(QByteArray)` and `unintentionalDisconnect()`. The FtescLowLevelFace constructor FUN_00483910 explicitly connects BleUart::bleDataRx(QByteArray) (string at 0x0052DF35) to dataRx(QByteArray) (string at 0x0052DF4C) around call-site 0x0048456D. This establishes the BLE byte-array ingress handoff to an application-level receiver. The constructor-level `dataRx(QByteArray)` receiver body remains unresolved. Separately, the recovered Qt meta-call table maps `bleDataRx` to native `FUN_004828D0`; this callback is now proven to forward its QByteArray to the shared UART frame/stream handler `FUN_0049CA30` (see below). These are two distinct static observations and should not be conflated. The UI/runtime path that invokes the write methods is not yet fully mapped.

Still unresolved:

1. The exact native call chain from `writeData` / `sendNextPacket` to `QLowEnergyService::writeCharacteristic`.
2. Whether the characteristic is written with response or without response.
3. The exact application-level chunk size, BLE MTU negotiation, and fragmentation/reassembly rules.
4. The exact value written to descriptor `0x2902` and notification-enable/disable sequencing.
5. The exact `characteristicChanged` → `dataRx` → shared UART stream-parser call chain, including ordering and thread/timer behavior.
6. Reconnect, retry, timeout and error propagation behavior under real BLE conditions.
7. Model/firmware applicability across all FTESC revisions.

## Progress update

The Windows V1.7 BLE static sub-workstream remains **85%**: service/TX/RX UUIDs, controller/service signal flow, common parser handoff and 20-byte application chunking are mapped. The exact Windows call target/write mode, CCCD payload, negotiated MTU and live behavior remain unresolved. Separately, the V1.6 Android native implementation now provides a direct cross-platform reference: WriteWithoutResponse, CCCD bytes 01 00 (notifications), 20-byte chunking and the same FTESC stream parser. This corroborates the likely V1.7 choices but does not by itself prove the protected Windows call's enum argument.

The whole-product score remains **72.2% (displayed 72%)**. This static reverse-engineering milestone does not create a desktop application, implement a live BLE transport, or validate a real controller, so it does not increase the weighted product-completion score.

## Safety and verification

All conclusions here are static observations from the named V1.7 executable. No BLE device was scanned or connected, no characteristic was read/written, and no ESC control data was sent. The open-source implementation should remain disabled for control writes until the TX/RX/notification path has been independently captured and verified on a safe, known hardware setup.

## REA evidence references

- UUID string inventory: `ev_c20b6860d554e3552d2dc6b82cebf19613220d0aa60f1a9439454420eac9ed7c`
- BLE-related strings and callback names: `ev_7835a85225d762c87de7b9860c87cdfb403da27dd47164414c9e8789300ff685`
- Qt/BleUart metadata string bytes: `ev_b916cb75bc14727e78b83f0b8ff0c6aba0cc33fe8e9e2d2729e558ade7a52b84`
- Service-state handler dossier: `ev_3feb0512635b349f450a5ea25919bedf24032ad311879124761ef69557d31e5e`
- Service setup / signal registration dossier: `ev_a8c247ff6f88ad41db5404f895e9dac4e89b515f10c4bc39760c6635077ed985`
- Controller initialization dossier: `ev_4aeaf50320792a55be39923e9659a5d8b29a4351d13bb721aae8f1806253cb12`
- `characteristicChanged` callback incoming reference: `ev_9c95801b699f876f5f04a72012ccdab2c9a91c1aeafbdd3f494b31e38eb6fd9f`
- Qt `BleUart` static meta-call decompilation: `ev_7be243cc6465b5cd705b2bd3c40cdb13db0554d3d45bf7256e1f21315f27ff4f`


## BLE ingress connection evidence update

- FUN_00483910 contains a Qt connect call at 0x0048456D registering 1bleDataRx(QByteArray) to 2dataRx(QByteArray).
- Signal string: 0x0052DF35; receiver slot string: 0x0052DF4C.
- This closes the static byte-array ingress handoff from the BleUart object into the application receiver, but not the parser handoff or receive buffering semantics.
- BLE sub-workstream estimate: 55% to 60%; whole-product progress unchanged at 72.2% because there is still no live transport implementation or hardware validation.
- Additional REA evidence: constructor assembly ev_48b77f16a200f240b408090beb0e346d37a46411cd19201282043055d8cc9e21, signal xref ev_9c95801b699f876f5f04a72012ccdab2c9a91c1aeafbdd3f494b31e38eb6fd9f, slot xref ev_499d842f955f91515d02843ae36178e872668e44098d657a6a0a195b717f9962, string inventory ev_63e64d98826b5c804fe70b6c398031928f0f6295d8c6b7c3d8c17038747f8103.


## Shared BLE/UART parser and transmit chunking — 2026-11-22

- The Qt meta-call map identifies `bleDataRx` (index 24) at native `FUN_004828D0` / `0x004828D0`.
- Its decompilation forwards the incoming `QByteArray` directly to `FUN_0049CA30`, the same incremental AA/BB frame-stream handler used by the UART receive path. BLE RX therefore reuses the common application-level framed-stream parser.
- The shared low-level send slot `FUN_00481850` checks the BLE-connected flag and, when active, passes the same framed byte array to `FUN_004050C0`.
- `FUN_004050C0` slices the byte array at successive offsets with stride `0x14` (20 bytes), and feeds an asynchronous queue pump `FUN_00404E80`.
- This is a fixed application-level chunk stride, not proof of a negotiated 20-byte ATT MTU. The exact final `writeCharacteristic` call, its `WriteMode`, CCCD value and MTU negotiation are unresolved. The PE import-table inspection is partial because descriptor RVA `0xB9F000` has ambiguous/non-contiguous mapping.
- Evidence: `ev_0b96fa9d9daca6528da735c37d6a4fa85f5cede2be619f08d07cfa494e6da22b`, `ev_0863f4b9c9cbaa26854a9389f1d2d4f01af0cd11963bc5043a68b1b315c57def`, `ev_26f4ad2230070fd6a96d3322a1e2c2fb5985d8d1c5709c228825789f669a36d1`, `ev_14bbb5c07a7e3c24e7f64e40abe36d4c543e0a8939b2ffd966061e649720f728` and `ev_64791b4adf0065ca2f544059fa314ba5862bbfd4c675fb96244f53cd84e50c5e`.
- Detailed call-path report: [BLE_TRANSPORT_SHARED_PARSER_AND_CHUNKING.md](BLE_TRANSPORT_SHARED_PARSER_AND_CHUNKING.md).
- No BLE scan, pairing, connection, characteristic read/write or ESC command was performed.


### Candidate final GATT write call — 2026-11-22

The asynchronous queue pump `FUN_00404E80` contains an indirect call at `0x00404FEC`. Assembly shows the BLE service object in ECX, followed by a characteristic-like object, queued `QByteArray` and third argument `1`. The static computed reference resolves to protected address `0x00B5A1D0`.

This call shape strongly matches the mangled `QLowEnergyService::writeCharacteristic(const QLowEnergyCharacteristic&, const QByteArray&, QLowEnergyService::WriteMode)` symbol string found in V1.7. The resolved target lies in the protected Enigma region and its decompilation is invalid; there is no proven target-to-symbol edge. Treat this as a strong candidate only. The integer value `1` is observed at the call site, but is not yet mapped to write-with-response or write-without-response.

Evidence IDs:
- Assembly: `ev_c6c574f4a7ccf94925be53eafce0df3c280bdcd98d789a023f7cbfe863da9949`
- Computed target: `ev_090dc82edec65beddd376fa5846a60d42657cb3321d854ee86984a3165050b51`
- Protected target decompilation: `ev_7a13690a90241ef5b49b36e0b1b571472b9aa6f90edb1f4d180a109a5eaaf10b`
- [Detailed BLE transport note](BLE_TRANSPORT_SHARED_PARSER_AND_CHUNKING.md).


## Cross-platform V1.6 Android corroboration — 2026-11-22

The V1.6 Android BLE APK embeds a native Flipsky ARM64 application library with the exported symbols `BleUart::writeData`, `BleUart::sendNextPacket`, `BleUart::dataRx`, `BleUart::updateData`, `BleUart::confirmedDescriptorWrite`, and `FtescLowLevelFace::lowLevelSendDataToFtesc`. The APK also includes Qt5Bluetooth for ARM64 and ARMv7. This confirms that the Android release has its own native BLE transport wrapper and the same major FTESC application family as Windows.

The bundled Qt Android Java bridge gives concrete backend semantics: its `writeCharacteristic(handle, bytes, type)` maps `type=1` to Android `WRITE_TYPE_DEFAULT`, `type=2` to `WRITE_TYPE_NO_RESPONSE`, and other values to `WRITE_TYPE_SIGNED`. It attempts an ATT MTU request of 512 and falls back to 23 on failure. Asynchronous operations are serialized with a 3-second timeout. For the client-characteristic-configuration descriptor, notification handling checks the first byte's bit 0 or bit 1 before calling Android's local `setCharacteristicNotification`.

These facts describe the Qt Android backend included in the APK. The application-selected type value, actual MTU, exact CCCD payload and notification/indication choice are not yet proven. They must not be inferred from the Windows protected indirect-call candidate.

Detailed report: [ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md](ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md). The BLE static sub-workstream rises from 80% to **85%**; overall weighted project score remains 72.6%.


## Android V1.6 direct transport confirmation — 2026-11-22

The staged V1.6 Android ARM64 app library provides direct application-level values:

- `BleUart::writeData` at `0x000FE09C` loads chunk size `0x14` (20) at `0x000FE0BC`, slices successive `QByteArray::mid` segments at `0x000FE10C`, and advances the offset by 20 at `0x000FE138`.
- `BleUart::sendNextPacket` at `0x000FE1A8` loads third C++ API argument `1` at `0x000FE2A8`, moves it into `w3` at `0x000FE2C0`, and directly calls Qt `QLowEnergyService::writeCharacteristic` at `0x000FE2C4`. In the Qt 5.15 C++ `WriteMode` enum, `1` is `WriteWithoutResponse`.
- `BleUart::serviceStateChanged` at `0x000FF648` looks up descriptor UUID `0x2902`, converts the literal `0100` (VA `0x002851C9`) from hex, and writes it using `writeDescriptor`. The resulting bytes `01 00` select notifications (CCCD bit 0), not indications.
- `BleUart::updateData` at `0x000FFB8C` dispatches matching characteristic data through the PLT relocation at GOT `0x00881578` to `BleUart::dataRx(QByteArray)`; that signal thunk at `0x0025ACD8` invokes `QMetaObject::activate`.
- The application slot `FtescLowLevelFace::bleDataRx(QByteArray)` at `0x00234730` copies its input via `QByteArray::QByteArray(QByteArray const&)` (PLT `0x000EA080`, GOT `0x0087E688`) and calls `uartPackData::uartPackDataHandle(QByteArray)` (PLT `0x000E81C0`, GOT `0x0087D728`). This is the common FTESC stream parser used by the serial transport.
- The Android Qt metaobject includes signal string `2dataRx(QByteArray)` and slot string `1bleDataRx(QByteArray)`; the exact constructor-level `QObject::connect` site remains unresolved.

This direct Android evidence corroborates the V1.7 Windows 20-byte chunking and makes `WriteWithoutResponse` a strong cross-platform hypothesis for Windows. It does not upgrade the Windows indirect-call target at `0x00404FEC` into a proven symbol mapping. Android artifact SHA: `26404ff6467971ff7c0fedbe1f326c6b0ccb5722571b7309d9913818960b4d7e`; extracted ARM64 library SHA: `7fba6a69f3719b70dfb7eee87c97e41aad2d8f48d1feec7058a0e5975a5ea2fc`.

