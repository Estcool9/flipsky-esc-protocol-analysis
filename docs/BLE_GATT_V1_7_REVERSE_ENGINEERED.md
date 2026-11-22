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

The class metadata includes the method names `writeData` and `sendNextPacket`, plus the signal names `dataRx(QByteArray)` and `unintentionalDisconnect()`. The FtescLowLevelFace constructor FUN_00483910 explicitly connects BleUart::bleDataRx(QByteArray) (string at 0x0052DF35) to dataRx(QByteArray) (string at 0x0052DF4C) around call-site 0x0048456D. This establishes the BLE byte-array ingress handoff to an application-level receiver. The receiver body and downstream handoff to the shared UART frame/stream parser are still not proven. The UI/runtime path that invokes the write methods is not yet fully mapped.

Still unresolved:

1. The exact native call chain from `writeData` / `sendNextPacket` to `QLowEnergyService::writeCharacteristic`.
2. Whether the characteristic is written with response or without response.
3. The exact application-level chunk size, BLE MTU negotiation, and fragmentation/reassembly rules.
4. The exact value written to descriptor `0x2902` and notification-enable/disable sequencing.
5. The exact `characteristicChanged` → `dataRx` → shared UART stream-parser call chain, including ordering and thread/timer behavior.
6. Reconnect, retry, timeout and error propagation behavior under real BLE conditions.
7. Model/firmware applicability across all FTESC revisions.

## Progress update

The BLE reverse-engineering sub-workstream is raised from **40% to 60%**: the service and both characteristic UUIDs are identified, the controller/service signal flow is mapped, and the notification descriptor lookup is located. The transmit implementation, write mode, chunk/MTU behavior and hardware capture remain unresolved.

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
