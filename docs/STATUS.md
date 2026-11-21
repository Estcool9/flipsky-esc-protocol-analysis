# Project status

**Reference date:** 2026-11-22  
**Overall estimated progress: 33%** toward a sufficiently evidenced protocol specification and an independently testable offline client.

These percentages are milestone estimates, not measurements of certainty.

## Workstream progress

| Workstream | Progress |
|---|---:|
| Binary inventory and integrity | 100% |
| Embedded XML extraction and validation | 100% |
| Parameter catalog generation | 100% |
| Qt/QML architecture and class ownership | 90% |
| UART/Qt signal-slot and meta-object mapping | 75% |
| UART implementation analysis | 32% |
| Frame format, command IDs, CRC and responses | 5% |
| VESC compatibility assessment | 25% |
| Offline parser / independent client | 0% |
| Hardware validation | 0% |
| **Overall estimate** | **33%** |

## Confirmed evidence

### Executable
- `Flipsky_ESC_Tool_V1.7_20261029.exe`, 50,611,200 bytes.
- SHA-256: `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`.
- PE32 x86 native Windows executable; no CLR/.NET header observed.
- Unusual `.enigma1` and `.enigma2` sections; protection/packing remains a hypothesis, not an identified protector.

### Embedded resources and parameter catalog
- 13 embedded XML resources recovered and validated.
- 736 catalog rows across profile variants; 222 unique parameter IDs; 13 resource/profile variants.
- Extraction and catalog-generation scripts are present in the repository.
- Complete catalogs, manifest and all XML files are published as gzip/base64 payloads. Run [scripts/restore_payloads.py](../scripts/restore_payloads.py) to reconstruct them and verify the printed SHA-256 values against [ARTIFACT_INVENTORY.md](ARTIFACT_INVENTORY.md).

### Qt architecture
- Qt 5, C++/QML, QtSerialPort and QtBluetooth are observed.
- VA `0x00483910` initializes a `FtescLowLevelFace` object. Its vtable and Qt meta-cast path establish class identity.
- Static meta-object: VA `0x0051f218`; string table `0x00f215c0`; meta-data `0x00f20d60`; static meta-call `0x004b98d0`.
- A 64-entry dispatch jump table begins at `0x00f20c58`.
- The class meta-object includes `uartDataHandleAvailable`, `uartPackDataFromESC`, `uartCommSendToFtesc`, `lowLevelSendDataToFtesc`, BLE callbacks and `tea_encrypt`.

### UART and BLE wiring
- `QSerialPort::readyRead()` is connected to `uartDataHandleAvailable()`.
- `uartPackDataFromESC(QByteArray&)` and `uartCommSendToFtesc(QByteArray&)` are wired through byte-array signal/slot connections.
- `lowLevelSendDataToFtesc(QByteArray&)` is connected to `sendDataToESC(QByteArray&)`.
- Firmware-version and motor-configuration acknowledgement slots are registered.
- BLE receive/disconnect callbacks are registered in the same high-level façade.

## Open technical questions

Not yet demonstrated:
- packet start/end markers and frame boundaries;
- length field and encoding;
- command IDs / opcodes;
- payload layouts;
- CRC/checksum algorithm;
- integer and floating-point endianness;
- fragmentation, escaping, retry and timeout behaviour;
- whether `tea_encrypt` is actually invoked in the UART path;
- exact BLE transport framing;
- wire-level compatibility with VESC.

## Tool requirements

No additional REA installation is currently required for static analysis: integrated Rizin 0.9.1 and Ghidra 12.2 are available. A Windows debugger (x64dbg or WinDbg in an isolated VM) could help later if runtime observation becomes necessary. A passive UART/USB capture from a known-good read-only session would be more valuable than installing more analysis packages.

## Safety boundary

No physical ESC has been tested and no firmware was flashed. XML parameter defaults and limits are not safe-tuning recommendations. Unknown packets must not be sent to a controller connected to a motor.
