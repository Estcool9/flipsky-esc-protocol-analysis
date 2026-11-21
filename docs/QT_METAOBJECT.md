# FtescLowLevelFace Qt meta-object and UART method map

Reference binary: `Flipsky_ESC_Tool_V1.7_20261029.exe`  
SHA-256: `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
Analysis date: 2026-11-22  
Tools: REA integrated Rizin 0.9.1; Ghidra 12.2 was opened but the targeted Ghidra calls timed out.

## 1. Identify the owning Qt class

The routine at VA `0x00483910` initializes an object using `ECX` as the this pointer, writes a vtable pointer at `[this]`, initializes multiple members, creates serial/timer-related objects and registers Qt signal/slot connections.

The vtable pointer written at `[this]` is `0x00f282f0`. Its first entries include:

- `0x004b9500`: returns the static meta-object pointer `0x0051f218` in the observed no-extra-metaobject path.
- `0x004bac80`: compares the requested meta-class name against the string `FtescLowLevelFace`; this is consistent with the Qt `qt_metacast` path.
- `0x004bacd0`: Qt meta-call dispatcher path.

Together, these observations identify the object as **FtescLowLevelFace**, rather than the low-level UART class itself. The routine at `0x00483910` should therefore be treated as the FtescLowLevelFace constructor/initialization path, not as the UART parser.

## 2. Static meta-object

The observed static meta-object is at VA `0x0051f218`. Its principal pointers are:

| Field | Address/value |
|---|---|
| String-data table | `0x00f215c0` |
| Meta-data table | `0x00f20d60` |
| Static meta-call function | `0x004b98d0` |

The static meta-call function at `0x004b98d0` dispatches through a 64-entry jump table beginning at `0x00f20c58`. The Qt meta-object string table contains the following method/type names relevant to this work:

- `uartDataHandleAvailable`
- `lowLeveltimerSlot`
- `lowLevelSendDataToFtesc`
- `uartPackDataFromESC`
- `uartCommSendToFtesc`
- `firmwareVerRec`
- `tea_encrypt`
- `ftescMotorSignalSetupReceviedSlot`
- `ValueSecretKeyCheckedSlot`
- `bleUnintentionalDisconnect`
- `bleDataRx`
- `uartComms`, `UartComm*`, `motorValSetup`, `ValueSetups*`

The string `tea_encrypt` is confirmed as a name in this class's meta-object string table. **That alone does not prove that it is called by the UART protocol or that it encrypts serial frames.** Its dispatch index and call sites still need to be resolved.

## 3. Constructor wiring observed in assembly

At VA `0x00483bac`–`0x00483bcd`, the constructor registers the `QSerialPort::readyRead()` signal against `uartDataHandleAvailable()`.

Other connections in the same constructor include:

| Signal | Slot | Relevant address range |
|---|---|---|
| `uartPackDataFromESC(QByteArray&)` | `uartPackDataFromESC(QByteArray&)` | `0x00483cbb`–`0x00483cd6` |
| `uartCommSendToFtesc(QByteArray&)` | `sendDataToESC(QByteArray&)` | `0x00483cf0`–`0x00483d0b` |
| `lowLevelSendDataToFtesc(QByteArray&)` | `sendDataToESC(QByteArray&)` | `0x00483c86`–`0x00483ca1` |
| `firmwareVerRec(FTESC_FIRMWARE_NUMBER)` | `ftescFirmwareVerRec(FTESC_FIRMWARE_NUMBER)` | `0x00483d25`–`0x00483d40` |
| `ftescMotorSignalSetupReceviedSlot(QString,bool)` | `ftescMotorSignalReadAck(QString,bool)` | `0x00483d5a`–`0x00483d75` |
| `ValueSecretKeyCheckedSlot(int)` | `ftescMotorSignalSecretKeyCheckAck(int)` | `0x00483dc4`–`0x00483ddf` |

The constructor also initializes BLE state and registers BLE receive/disconnect connections. This confirms that the high-level FtescLowLevelFace object orchestrates UART and BLE-facing components.

## 4. What this adds to the protocol investigation

The architecture can now be described more accurately:

1. `FtescLowLevelFace` is the high-level Qt object coordinating transport components.
2. A QSerialPort `readyRead()` event reaches `uartDataHandleAvailable()`.
3. The high-level class routes byte-array signals through separate low-level and UART communication slots.
4. The class also exposes read-acknowledgement, firmware-version, secret-key callback and BLE-receive methods.

This is stronger than simply listing method names: the class ownership and static meta-call dispatch structure are now observed.

## 5. Remaining work

- Decode the QMetaObject method metadata and map each dispatch ID to the exact method implementation.
- Identify the dispatch slot corresponding to `tea_encrypt`; confirm its callers before assigning any cryptographic role.
- Trace `uartDataHandleAvailable` to the byte-buffer accumulation/dispatch logic.
- Trace `uartPackDataFromESC` to frame boundary, length, command, payload and checksum handling.
- Trace `sendDataToESC` and its callers to discover actual transmitted byte construction.

No packet framing, opcode, CRC, endianness or encryption use has been demonstrated yet.
