# Qt UART wiring recovered from static code references

## Scope

Static-only targeted disassembly with Rizin 0.9.1. No target process was launched. The original PE remains unchanged (SHA-256 `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`).

## Evidence

The Qt method-name strings reside in `.rdata`; their virtual addresses are loaded as immediate operands by code in `.text`. Rizin disassembly shows repeated argument setup followed by indirect/direct calls, using paired Qt connection signatures. Prefixes `1` and `2` correspond to the legacy Qt signal and slot signature notation. This is code-reference evidence for application event wiring, not just an isolated string inventory.

## Serial receive and error path

At VA `0x00483bac`, code supplies `1uartDataHandleAvailable()` and `2readyRead()` to a Qt connection helper. In context, this is consistent with `QSerialPort::readyRead()` being connected to `UartComm::uartDataHandleAvailable()`.

At VA `0x00483bed`, code supplies `1uartPortError(QSerialPort::SerialPortError)` and `2error(QSerialPort::SerialPortError)` to the same connection pattern. This ties serial-port errors to the application's error handler.

Nearby pairs observed in this connection-registration block:

- `1lowLeveltimerSlot()` / `2timeout()`: timer timeout routed to the low-level UART timer slot.
- `1lowLevelSendDataToFtesc(QByteArray&)` / `2sendDataToESC(QByteArray&)`.
- `1uartPackDataFromESC(QByteArray&)` / `2uartPackDataFromESC(QByteArray&)`.
- `1uartCommSendToFtesc(QByteArray&)` / `2sendDataToESC(QByteArray&)`.
- A related record contains `1ValueSecretKeyCheckedSlot(int)` and `2ftescMotorSignalSecretKeyCheckAck(int)`; direction needs fuller caller-context validation.

These pairs identify a send/receive wiring surface. The exact receiver object identities and all intermediate helper semantics still need fuller reconstruction.

## Realtime path

A second call-site block at VA `0x0040b251` registers:

- `1ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA)` / `2ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA)`.
- `1read_app_to_rtdata(QString,bool)` / `2ftescSignalReadAckToRtData(QString,bool)`.

This is evidence of a separate realtime-data dispatch/acknowledgement path. It does not identify any UART opcode or data-frame format.

## What this proves and does not prove

Supported by the disassembly: serial readyRead is routed to a UART data handler; serial errors are handled; timer events feed the low-level communication routine; Qt connections are present for `lowLevelSendDataToFtesc`, `uartPackDataFromESC`, `uartCommSendToFtesc`, `sendDataToESC`, and realtime-data acknowledgements.

Not yet recovered: packet boundary markers, length fields, command IDs/opcodes, byte order, CRC/checksum, escaping, retransmit rules, and payload structure. Do not implement a protocol from these method names alone.

## Next probes

1. Recover the complete owning function for the Qt connection-setup block and confirm object ordering and helper targets.
2. Follow references into the implementations or dispatch wrappers for `uartDataHandleAvailable`, `uartPackDataFromESC`, `lowLevelSendDataToFtesc`, and `sendDataToESC`.
3. Identify any post-unpack command switch/table and map each branch to named ACK handlers.
4. Cross-check any recovered frame format against matching official firmware or a passive UART capture from a test ESC before implementing writes.
