# FtescLowLevelFace Qt static meta-call dispatch map

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Class meta-object:** `0x0051F218`  
**Meta-data:** `0x00F20D60`  
**String-data:** `0x00F215C0`  
**Static meta-call:** `0x004B98D0`  
**Analysis:** Ghidra 12.2 / REA 6.10.1, 2026-11-22

This report resolves the 64 Qt method indexes for the `FtescLowLevelFace` meta-object. It is a Qt method-dispatch map, **not** an ESC wire-command map.

## 1. Method table recovered from Qt metadata

The metadata header at `0x00F20D60` reports revision 8, 64 methods and method-table offset 14 (32-bit words). Each method record provides a name-string index, argument count, parameter-data offset, tag and flags. The corresponding string entries were decoded from the Qt string-data table at `0x00F215C0`.

Flags observed:
- `0x06`: public signal in this table.
- `0x08`: public slot.
- `0x02`: public invokable method/property accessor.

The labels are based on the Qt 5 method flag encoding and the static meta-call branch behaviour.

## 2. Signal indexes (0–11)

These cases call Qt's signal-activation helper with the corresponding method index.

| Index | Signal name | Args |
|---:|---|---:|
| 0 | `messageDialog` | 3 |
| 1 | `sendFwUpdateMessageStatus` | 2 |
| 2 | `sendSetupReadSuccessFlag` | 2 |
| 3 | `sendmessDialog` | 4 |
| 4 | `sendUpdateFwStatus` | 3 |
| 5 | `ftescFwReceviedVaried` (overload 1) | 1 |
| 6 | `ftescFwReceviedVaried` (overload 2) | 2 |
| 7 | `usbconnect_flag` | 1 |
| 8 | `usbconnect_flag_1` | 1 |
| 9 | `unintentionalBleDisconnect` | 0 |
| 10 | `portConnectedChanged` | 0 |
| 11 | `requestCanCheck` | 0 |

## 3. Slot indexes (12–24)

The switch in `FUN_004B98D0` directly dispatches these indexes to native functions.

| Index | Slot | Native target | Notes |
|---:|---|---:|---|
| 12 | `uartPortError` | `0x004810D0` | Serial-port error slot |
| 13 | `uartDataHandleAvailable` | `0x00481030` | Receive-ready handler |
| 14 | `lowLeveltimerSlot` | `0x00481290` | Low-level timer slot |
| 15 | `lowLevelSendDataToFtesc` | `0x00481850` | Routes outgoing byte array |
| 16 | `uartPackDataFromESC` | `0x00481930` | Routes received byte array |
| 17 | `uartCommSendToFtesc` | `0x004819C0` | Routes outgoing byte array |
| 18 | `firmwareVerRec` | `0x00481C60` | Firmware-version callback |
| 19 | `tea_encrypt` | `0x00481B30` | TEA 64-bit block transform |
| 20 | `encrypt` | `0x00481BC0` | Zero-pad and encrypt a buffer in 8-byte blocks |
| 21 | `ftescMotorSignalSetupReceviedSlot` | `0x00482550` | Thin forwarding wrapper |
| 22 | `ValueSecretKeyCheckedSlot` | `0x00482560` | Updates an internal key-check state flag |
| 23 | `bleUnintentionalDisconnect` | `0x004B9520` (thunk) | BLE disconnect callback |
| 24 | `bleDataRx` | `0x004828D0` | BLE receive callback |

The receive and transmit methods are now linked from Qt method index through the static dispatcher to their native entry points, complementing the previously recovered UART parser and frame builder.

## 4. Remaining invokable methods / accessors (25–63)

| Index | Method | Native target / behaviour |
|---:|---|---|
| 25 | `uartComms` | `0x00480C80` |
| 26 | `motorValSetup` | `0x00480C90` |
| 27 | `signalValSetup` | `0x00480CA0` |
| 28 | `topFlowValSetup` | `0x00480CB0` |
| 29 | `firmwareValSetup` | `0x00480CC0` |
| 30 | `sendMessageDialog` (4 args) | `0x00480CD0` |
| 31 | `sendMessageDialog` (3 args) | `0x00480CD0` |
| 32 | `emitUsbconnect_flag` | `0x00480E00` |
| 33 | `emitUsbconnect_flag_1` | `0x00480E10` |
| 34 | `wasReceivedFirmwareInf` | `0x00480E20` |
| 35 | `emitMessageDialog` | `0x00480E30` |
| 36 | `refreshFwVer` | `0x00482600` |
| 37 | `enterBootMode` | `0x00480E40` |
| 38 | `obtainUpdateProgress` | `0x00480E50` |
| 39 | `obtainUpdateStatus` | `0x00480E60` |
| 40 | `wasUSBPortConnected` | `0x00480E90` |
| 41 | `disConnectUSBPort` | `0x00480EC0` |
| 42 | `easyConnect` | `0x00485980` |
| 43 | `ignoChangeCanID` | `0x00481020` |
| 44 | `getAllowScreenRotation` | `0x00482750` |
| 45 | `setAllowScreenRotation` | `0x00482760` |
| 46 | `obtainFwInfNow` | `0x00482590` |
| 47 | `obtainFwWasCompatible` | `0x004825F0` |
| 48 | `preserveEscFirmware` | `0x004826F0` |
| 49 | `obtainEscFirmware` | `0x00482710` |
| 50 | `obtainEscHardwareName` | `0x00482720` |
| 51 | `connectBle` | `0x00482960` |
| 52 | `qmlfirmwareList` | `0x004819D0` |
| 53 | `qmlrefreshFirmwareName` | `0x00483170` |
| 54 | `firmwareUpdatePro` | `0x00486570` |
| 55 | `qmlfirmwareData` | `0x004863C0` |
| 56 | `motorSetupreloadValues` | `0x00482870` |
| 57 | `bleDevice` | `0x00482880` |
| 58 | `storeBleName` | `0x00482BA0` |
| 59 | `getBleName` | `0x00482A00` |
| 60 | `getLastBleAddr` | `0x00482890` |
| 61 | `storeBlePreferred` | `0x00482DC0` |
| 62 | `getBlePreferred` | `0x00482CB0` |
| 63 | `hasBluetooth` | Returns constant `1` in the observed dispatcher |

For indexes 25–63, the table records the direct function called by the dispatcher. Accessor semantics should be refined from each getter/setter body before assigning a higher-level data meaning.

## 5. TEA and firmware-update relationship — now confirmed

The earlier string-only evidence for `tea_encrypt` has now been resolved to executable code:

- Qt method index 19 dispatches `tea_encrypt` to `0x00481B30`.
- `0x00481B30` performs 32 TEA rounds over two 32-bit words. The delta is `0x9E3779B9` (shown by the decompiler as subtraction of `0x61C88647`), and the loop executes 32 rounds.
- Qt method index 20 dispatches `encrypt` to `0x00481BC0`.
- `0x00481BC0` pads the supplied byte count with zero bytes to an 8-byte boundary, then calls the TEA block transform for each 8-byte block.
- The `firmwareUpdatePro` implementation at `0x00486570` contains a direct call to `0x00481BC0` at `0x00486C1F`.

This is direct static evidence that the firmware-update path uses the TEA-based buffer transform. It does **not** establish that ordinary telemetry/control UART frames are encrypted. No key material is published in this report.

## 6. Interpretation and limits

- The 64 Qt method IDs are now mapped for this one FtescLowLevelFace meta-object.
- These indexes are Qt meta-object method indexes, **not** UART command IDs.
- The high-level methods `ftescControlDuty`, `ftescControlCurrent`, `ftescGetRealtimeDataOnce`, and related operations belong to a different API surface/string group; their payload-building paths still need separate tracing.
- The BLE receive callback is identified, but the BLE packet envelope is not yet recovered.
- No device was connected and no command was transmitted.

## 7. Next analysis targets

1. Trace `0x00486570` and its adjacent firmware helpers in detail, while keeping key material out of public documentation.
2. Map the separate ToolLib / FtescLowLevelFace high-level request methods to actual frame payloads and numeric command bytes.
3. Resolve the response dispatch function at `0x004997A0` against the public V1.6 command IDs.
4. Trace `0x004828D0` and BLE helper methods to determine whether BLE uses the same frame parser.
5. Stage a V1.6 Windows executable for binary comparison.
