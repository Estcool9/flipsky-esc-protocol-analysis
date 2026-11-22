# V1.6 Android BLE native implementation and Windows cross-version marker audit

**Analysis date:** 2026-11-22  
**Scope:** static analysis of the V1.6 BLE APK and three V1.6 Windows PE32 builds, compared at marker/symbol level with V1.7. No sample was executed and no ESC/BLE hardware was contacted.

## Acquired artifacts and hashes

All four files were checked out read-only from Nextcloud, copied through the Gateway SSH path to CT 107, and SHA-256 checked before and after transfer. They are retained under version-specific read-only analysis folders.

| Artifact | Size | SHA-256 |
|---|---:|---|
| V1.6 Android BLE APK | 44,167,894 | `26404ff6467971ff7c0fedbe1f326c6b0ccb5722571b7309d9913818960b4d7e` |
| V1.6 Windows 2026-09-12 | 45,582,336 | `051d57a776782ae8daaeaa45179f9b568f7e89b4a78ab8dd8e558ecd3e53b968` |
| V1.6 Windows 2026-08-06 | 44,867,072 | `94cfd851a5ccce38b8c42c9f154128e10fa2906ce9efc9cddfa39c4a00361a03` |
| V1.6 Windows 2025-10-14 | 97,949,184 | `1dc93bd84f4dab1a3ee7b3946fa0522c78fc870227523d8d5fe6d6e187ea2b07` |

The Android APK contains 149 inventoried occurrences (148 unique artifact nodes) with no integrity contradictions. Relevant extracted, hash-verified components:

| APK entry | Extracted size | SHA-256 |
|---|---:|---|
| `lib/arm64-v8a/libFilpsky_ESC_Tool_V1.6_20251014_arm64-v8a.so` | 8,998,672 | `7fba6a69f3719b70dfb7eee87c97e41aad2d8f48d1feec7058a0e5975a5ea2fc` |
| `lib/armeabi-v7a/libFilpsky_ESC_Tool_V1.6_20251014_armeabi-v7a.so` | 8,491,756 | `8ba92821d1310762ae582a9cbb07918e7e1d416238ac8110be6a04063d8b0562` |
| `lib/arm64-v8a/libQt5Bluetooth_arm64-v8a.so` | 494,736 | `33556cf19fabec510ae03092a84d491eb17e5fc97729e9f55001a2f0486e8196` |
| `lib/armeabi-v7a/libQt5Bluetooth_armeabi-v7a.so` | 281,844 | `2688ea1de01e32dfc776f959e83f882935383ff8d7ceb911083935a1cc5a4139` |
| `assets/android_rcc_bundle.rcc` | 2,361,554 | `d272ad2fffa1a187d82f6d146d9505ab8f769184ce54373ba44be36c0d9ba896` |

## APK manifest and runtime envelope

JADX/REA reports package `org.qtproject.example`, version name `1.6`, version code `1`, min SDK 21 and target SDK 28. The launcher is Qt's `QtActivity`; the application uses `QtApplication`. The manifest marks the application `debuggable=true` and declares `com.ftesc.VForegroundService` enabled and exported. Bluetooth, Bluetooth Admin, scan/connect, fine/coarse/background location, foreground service, storage, network, wake-lock and vibration permissions appear in the manifest.

The Qt Bluetooth broadcast receiver is listed as a static-init class, and the bundled JAR list includes `QtAndroidBluetooth.jar`. The declared foreground-service class was not found by the available JADX class-name search; its implementation and runtime behavior are unresolved. Manifest declarations are not evidence that the service was started or that any permission was exercised.

The package includes both `arm64-v8a` and `armeabi-v7a` native libraries. The APK-signature inspector observed signature material for v1/v2 and a common certificate fingerprint, but cryptographic signature verification was **not performed**.

## Flipsky native Android implementation

Rizin's ELF dynamic-symbol inventory identifies the native application as C++/Qt and exposes a substantial set of Flipsky symbols despite the file being reported as stripped (no ordinary static symbol table). The ARM64 application library has 7,180 dynamic exports in the static export inventory.

### BLE layer

The native `BleUart` class is registered as a QML type. Selected observed function entries (ARM64 ELF virtual addresses):

| Function | Address | Size |
|---|---:|---:|
| `BleUart::BleUart(QObject*)` | `0x000fd468` | 456 |
| `BleUart::init()` | `0x000fd84c` | 600 |
| `BleUart::startScan()` | `0x000fd7b0` | 156 |
| `BleUart::startConnect(QString)` | `0x000fdaa4` | 1,044 |
| `BleUart::writeData(QByteArray)` | `0x000fe09c` | 268 |
| `BleUart::sendNextPacket()` | `0x000fe1a8` | 428 |
| `BleUart::updateData(QLowEnergyCharacteristic const&, QByteArray const&)` | `0x000ffb8c` | 316 |
| `BleUart::serviceStateChanged(...)` | `0x000ff648` | 1,088 |
| `BleUart::confirmedDescriptorWrite(...)` | `0x000ffcc8` | 408 |
| `BleUart::dataRx(QByteArray)` | `0x0025acd8` | 124 |

These names establish that Android V1.6 has a native Flipsky BLE wrapper with scan/connect, outgoing packet, next-packet, received-data, service-state and descriptor-write callbacks. Function bodies at these addresses were not successfully decompiled in this pass: REA's targeted Ghidra function requests timed out, so the symbol table alone does not establish chunk size, reassembly or callback routing.

### Application protocol, setup and firmware functions

The same native library exposes these application symbols:

- `FtescLowLevelFace::lowLevelSendDataToFtesc(QByteArray&)` — `0x00232648`, size 188.
- `FtescLowLevelFace::uartPackDataFromESC(QByteArray&)` — `0x00232704`, size 156.
- `FtescLowLevelFace::enterBootMode()` — `0x0023108c`, size 40.
- `FtescLowLevelFace::firmwareWriteToFtesc(QByteArray&)` — `0x002310b4`, size 1,396.
- `FtescLowLevelFace::obtainUpdateStatus()` — `0x002316e0`, size 52.
- `FtescLowLevelFace::firmwareUpdatePro(...)` — `0x0023316c`, size 2,868.
- `FtescLowLevelFace::obtainFwInfNow()` — `0x002342e0`, size 52.
- `ToolLib::obtainFtescFirmwareVerOverCan(...)` — `0x00245f4c`, size 224.
- `ftescValueTable::incQWidget(...)` — `0x001470e4`, size 1,140.

The library also contains the application names `frameFwUpdate`, `UartComm`, `ftescValueTable`, `frameMotorSetup`, `frameRealtime`, `frameSignalSetup`, and `FtescLowLevelFace`. This proves those native code structures are present in the APK; it does not yet map their full command semantics or prove a firmware update was executed.

### Qt Android BLE bridge semantics

JADX reconstructed Qt's bundled `org.qtproject.qt5.android.bluetooth.QtBluetoothLE` class. Its `writeCharacteristic(int, byte[], int)` creates a queued write job; the third integer is mapped as follows:

- `1` → Android `BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT` (numeric 1).
- `2` → Android `WRITE_TYPE_NO_RESPONSE` (numeric 4).
- Other values → Android `WRITE_TYPE_SIGNED` (numeric 2).

The queued write is later executed by setting the characteristic write type, assigning the byte array, and calling `BluetoothGatt.writeCharacteristic`. This is a fact about the bundled Qt Android bridge. It does **not** tell us which argument the Flipsky native application actually passes at runtime.

The Qt Android bridge also:

- Serializes read/write jobs in a `LinkedList`, with an in-flight flag and a 3,000 ms timeout runnable.
- Schedules an MTU job that attempts `requestMtu(512)` on supported Android API levels; on failure it records the default MTU as 23 bytes.
- For a descriptor matching its client-characteristic-configuration UUID, interprets bit 0 or bit 1 in the first descriptor byte as enabling local characteristic notifications before writing the descriptor.

The native Flipsky application code resolves two of the application-selected values directly (see the next section). The negotiated MTU and actual connection result remain runtime facts and are still unverified.

## Application-level Android BLE transport — exact V1.6 values

This section is based on direct Rizin disassembly and ELF dynamic relocation resolution in the extracted ARM64 app library (SHA-256 `7fba6a69f3719b70dfb7eee87c97e41aad2d8f48d1feec7058a0e5975a5ea2fc`). These are application-level choices, not merely Qt backend capabilities.

### TX segmentation: fixed 20-byte application chunks

In `BleUart::writeData(QByteArray)` at `0x000FE09C`:

- `0x000FE0BC` loads the constant `0x14` (20) into the chunk-size local.
- The loop calls `QByteArray::mid(int, int)` at `0x000FE10C` for successive slices.
- `0x000FE138` advances the offset by the stored 20-byte stride.
- Each slice is added to the outgoing queue and the send routine is scheduled.

This is an explicit 20-byte application chunk size; it is not itself proof of the actual negotiated ATT MTU.

### TX GATT mode: WriteWithoutResponse

In `BleUart::sendNextPacket()` at `0x000FE1A8`:

- The routine resolves the target `QLowEnergyCharacteristic` from the configured UUID.
- `0x000FE2A8` loads integer `1`.
- `0x000FE2C0` places that value in the fourth AArch64 argument register (`w3`) for the C++ member call.
- `0x000FE2C4` directly calls the resolved `QLowEnergyService::writeCharacteristic(const QLowEnergyCharacteristic&, const QByteArray&, QLowEnergyService::WriteMode)` symbol.

For the Qt 5.15 C++ enum, `WriteMode=1` is `WriteWithoutResponse` (the zero value is `WriteWithResponse`). Thus the V1.6 Android Flipsky code explicitly requests **WriteWithoutResponse** for its queued 20-byte slices. This direct call and constant remove the uncertainty left by the Windows V1.7 protected indirect-call candidate, for Android V1.6 only.

### CCCD: notifications selected with payload 0x0100

In `BleUart::serviceStateChanged` at `0x000FF648`:

- The code constructs the Bluetooth descriptor UUID `0x2902` and retrieves that descriptor from the characteristic.
- It loads the string literal `"0100"` at virtual address `0x002851C9`.
- It converts that string using `QByteArray::fromHex` and calls `QLowEnergyService::writeDescriptor`.

The actual descriptor bytes are therefore `01 00` (CCCD value `0x0001` in little-endian byte order). This selects **notifications** (bit 0), not indications (bit 1). This is the app's direct payload, not the generic Qt bridge's description of both possible bits.

### Receive: BLE callback feeds the shared FTESC stream parser

- `BleUart::updateData(QLowEnergyCharacteristic const&, QByteArray const&)` at `0x000FFB8C` checks the characteristic UUID and calls the PLT entry at `0x000EFE60`.
- The ELF `R_AARCH64_JUMP_SLOT` relocation at GOT slot `0x00881578` resolves that entry to `BleUart::dataRx(QByteArray)`.
- `BleUart::dataRx(QByteArray)` at `0x0025ACD8` invokes `QMetaObject::activate`, emitting the Qt signal.
- The application slot `FtescLowLevelFace::bleDataRx(QByteArray)` exists at `0x00234730`. Its first PLT call at `0x000EA080` resolves via GOT slot `0x0087E688` to `QByteArray::QByteArray(QByteArray const&)`, copying the incoming bytes.
- Its second PLT call at `0x000E81C0` resolves via GOT slot `0x0087D728` to `uartPackData::uartPackDataHandle(QByteArray)`. The receiver object is the `uartPackData` member at `FtescLowLevelFace+0x30`.

This shows the Flipsky BLE slot routes the received byte array into the application's shared `uartPackDataHandle` stream parser, rather than implementing a distinct BLE frame parser. The Qt metaobject metadata contains `2dataRx(QByteArray)` and `1bleDataRx(QByteArray)`; the exact constructor-level `QObject::connect` call site between those methods remains to be mapped, so the signal emission and slot body are established separately from the connection edge.

### Evidence quality and remaining runtime unknowns

The function bodies, literal, and relocation targets above were recovered from the hash-identified extracted library. The APK is not executed and no device was contacted. Still unknown: negotiated ATT MTU, controller-specific behavior, queue retry/timeout outcomes on real links, actual notifications observed over the air, and whether other APK versions use identical values.

## ARMv7 cross-ABI verification — 2026-11-22

The same application-level BLE behavior was checked in the ARMv7 library `lib/armeabi-v7a/libFilpsky_ESC_Tool_V1.6_20251014_armeabi-v7a.so` (SHA-256 `8ba92821d1310762ae582a9cbb07918e7e1d416238ac8110be6a04063d8b0562`).

### TX chunk size

- `BleUart::writeData(QByteArray)` is at `0x000C6FAC`.
- At `0x000C6FD0`, `movw r2, 0x14` sets a 20-byte chunk length.
- The loop calls `QByteArray::mid(int,int)` at `0x000C701C` and repeats using the fixed 20-byte value.

### TX write mode

- `BleUart::sendNextPacket()` is at `0x000C70BC`.
- `0x000C71C8` loads integer 1 and `0x000C71CC` stores the byte into the WriteMode argument local.
- `0x000C71E0` places that value in the fourth AAPCS argument slot; the call at `0x000C71F0` is directly resolved by Rizin to `QLowEnergyService::writeCharacteristic(..., QLowEnergyService::WriteMode)`.
- Therefore ARMv7 also requests C++ `WriteMode=1` = Qt 5.15 `WriteWithoutResponse`.

### CCCD path

- `BleUart::serviceStateChanged` is at `0x000C8694`.
- At `0x000C8950`, it constructs descriptor UUID `0x2902`; at `0x000C89FC`, it calls `QByteArray::fromHex`; at `0x000C8A10`, it calls `QLowEnergyService::writeDescriptor`.
- The ARMv7 library contains a single ASCII literal `0100` at `0x0026F7D9`. The same method contains the fromHex/writeDescriptor sequence. Rizin did not recover a direct cross-reference from this literal to the call in this pass, so the ARMv7 payload is recorded as a strong match to the ARM64-proven `01 00` value rather than an independently complete literal-to-call proof.

### RX routing to the common parser

- `BleUart::updateData` is at `0x000C8C38` and checks the characteristic UUID before its signal/dispatch path.
- `BleUart::dataRx(QByteArray)` is at `0x0022AF34` and is the corresponding Qt signal thunk.
- `FtescLowLevelFace::bleDataRx(QByteArray)` is at `0x00202DC8`.
- The ARM ELF JUMP_SLOT relocations resolve PLT `0x000B159C` through GOT `0x00809294` to `QByteArray::QByteArray(QByteArray const&)`, and PLT `0x000C0194` through GOT `0x0080E13C` to `uartPackData::uartPackDataHandle(QByteArray)`.
- This independently confirms the ARMv7 Android receive slot forwards the incoming bytes to the shared FTESC stream parser, rather than a separate BLE framing parser.

**Cross-ABI conclusion:** ARM64 and ARMv7 both statically establish 20-byte application chunking, the direct Qt writeCharacteristic call with `WriteMode=1` (WriteWithoutResponse), and BLE receive-slot routing to the shared FTESC stream parser. The ARM64 CCCD payload `01 00` is directly tied to the descriptor write; ARMv7 has the same `0100` literal and equivalent descriptor construction/write sequence, but the direct literal reference remains a minor unresolved detail. The exact Qt signal-to-slot connection call site is still unresolved on both ABIs, as are negotiated MTU and all runtime outcomes.

## Windows V1.6 and V1.7 marker comparison

All four Windows PE32 x86 builds (V1.6 dated 2025-10-14, 2026-08-06, 2026-09-12 and V1.7 dated 2026-10-29) produced the same targeted printable marker set:

- `BleUart`, `FtescLowLevelFace`, `frameFwUpdate`, `UartComm`, `ftescValueTable`
- `bleDataRx(QByteArray)`, `uartCommSendToFtesc(QByteArray&)`, `uartPackDataFromESC(QByteArray&)`
- `uartPackData`, `uartPackDataHandle`, `uartPackDataTimerSl`, `enterBootMode`
- The mangled Qt `QLowEnergyService::writeCharacteristic(..., WriteMode)` symbol.

The 2025-10-14 V1.6 EXE additionally exposes a mangled `QLowEnergyControllerPrivateWin32::writeCharacteristic(..., WriteMode)` string in this targeted scan; the three later builds did not return that string in the same scan. This is an **observed string delta only**, not proof the code path was added or removed (packed, obfuscated or unscanned regions may contain further references).

For each Windows V1.6 PE, the import inspector encountered an unreadable descriptor due to ambiguous/non-contiguous virtual mapping (V1.6 2026-09-12 at RVA `0x899000`, V1.6 2026-08-06 at RVA `0x81F000`, V1.6 2025-10-14 at RVA `0x7C2000`). The reported import lists are therefore **partial and empty**, not evidence that no imports exist. The same general limitation has already been recorded for V1.7.

## ELF hardening observations (Android ARM64 app library)

Static ELF inspection reported: NX enabled, full RELRO, stack canary present, PIE enabled, no RPATH/RUNPATH, and static symbol table stripped. BTI/PAC property was not declared. These are metadata observations, not a security audit or exploitability finding.

## Evidence IDs

- APK complete package / manifest summary: `ev_1cb15f994a26ec2e08619e9cfd84ba478f1f9018b5af37b77521b2cca1cb3cda`
- APK resource extraction: `ev_66f7abfccd26855576e9f5249f723df2bebb412e0f2d97b465a21a12510a12cb`
- Full APK inventory: `ev_ec72f3dc0f3e29f8c63679515b26d5e485222bd5456cc41c7cdd14ed2045376d`
- APK native extraction manifest: `aex_6d36095ce58801547f39783508849206faa21b4906f3dcd88062209f0848dbe8`
- Qt Android Bluetooth class summary: `ev_59e21014f4b6523fbdfccb1385d57ba345bcd7dfcb36087289db5cde0d900181`
- Qt Android `executeWriteJob`: `ev_3f1fe108b6322a041aa3fef51d17f60ee6a2cb6a10a6279838d4afce5c64ebdf`
- Qt Android `writeCharacteristic`: `ev_cb6c611cbba60fda4120e64ebc57f40b7c4073b1a83a1a6e29bea2d70b2a90fb`
- Qt Android `executeMtuExchange`: `ev_3d9b44ace6a1bde09ed81310da41dff78c298d96ea9c0941f5a392db128182bd`
- Qt Android queue pump: `ev_433ff5c5aee12a8aea226702e7bf865a5c1dfcf3dd958825934dc6f2fd3b3d69`
- JNI binding inventory: `ev_35a40922f2fa5e40ad9e74bfa24f00a1ca608d7bbe8a4bb2581717b5a905ea94`
- ARM64 app ELF dependencies: `ev_07b7ff1e85282e1184b76cf84f05ad319aa6a93958eb0812a331fa13a0783898`
- ARM64 app dynamic exports: `ev_1f03e16d344586e3e7b8ab0edd8982dfdda87c0c80f5d90ec338b6192e88015a`
- ARM64 app ELF hardening: `ev_b6f9ec225ba290692cd81abd1f276c35c30a9081dcf798ac00b581aaa380ea7b`
- ARM64 app ELF notes / Android NDK identification: `ev_c528b293c772c981a08c279e59ad933166069f9b553b7e14e99465d34da96a13`
- ARM64 Qt Bluetooth dependencies: `ev_ed6224332ec0e7bc90d6bcfaf56eb9eec8598a3219e58ab1cd39c510454a2688`
- ARM64 Qt Bluetooth dynamic exports: `ev_8de2d9a649d691b9df676a308215becd70b31f3a3ab68ed1f2ecfe87dd4a2e2f`

## Current limits and next probes

1. Decompile the Android `BleUart::writeData`, `sendNextPacket`, `dataRx`, `updateData`, and `confirmedDescriptorWrite` bodies in smaller REA/Rizin sessions.
2. Compare ARM64 and ARMv7 app functions and their Qt Bluetooth adapters.
3. Decode the Qt `.rcc` bundle and inspect application QML call sites for BleUart invocations.
4. Resolve which WriteMode and CCCD payload Flipsky requests on Android and compare it with Windows V1.7.
5. Recover the complete Windows PE import table and compare code-level behavior, not only printable markers.
6. Complete static diffs of all three V1.6 builds, especially the 2025-10-14 Win32 Qt BLE symbol delta.
7. Verify manifest service implementation and signature cryptographically.

The V1.6 Android BLE static workstream advances from 85% to **95%**: exact 20-byte chunking, C++ WriteWithoutResponse mode, CCCD notifications payload, and BLE receive handoff into the shared FTESC stream parser are now recovered. Remaining work is the Qt signal connection edge, negotiated MTU/runtime outcomes, the exact ARMv7 literal-to-CCCD reference and resource/UI mapping. The complete-product score remains **72.6%** (79.9 / 110 points): no desktop or live transport feature was implemented and no hardware validation was performed.

## Safety / execution record

- No APK or EXE was executed.
- No Android handset was queried; ADB was not used to contact a device.
- No BLE scan, pairing, connection, GATT read/write, UART/CAN transmission, motor command or firmware operation was performed.
- Original Nextcloud source files were not modified; only read-only downloaded copies were staged on CT 107.
