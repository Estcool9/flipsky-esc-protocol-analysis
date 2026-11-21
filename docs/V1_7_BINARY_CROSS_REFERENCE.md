
# V1.7 binary cross-reference against the public V1.6 UART specification

**V1.7 executable:** Flipsky_ESC_Tool_V1.7_20261029.exe  
**SHA-256:** dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38

## Confirmed in V1.7 binary

### Outer UART frame

The private parser at VA 0x0049C830 and frame builder at VA 0x0049C5C0 independently demonstrate the public V1.6 envelope:
- 0xAA + one-byte INFO length for lengths through 255;
- 0xBB + 16-bit big-endian INFO length for larger frames;
- INFO bytes copied unchanged;
- CRC high byte then low byte;
- trailing 0xDD.

The parser calculates CRC over INFO and compares the two-byte big-endian trailer. Tables at 0x005310C0 and 0x005311C0 match split CRC-16/MODBUS lookup tables.

### Receive path

    QSerialPort::readyRead()
      -> UartComm::uartDataHandleAvailable()  VA 0x00481030
         -> uartPackDataHandle()              VA 0x0049CA30
            -> outer frame parser             VA 0x0049C830

The parser call occurs at 0x0049CC8D. The caller continues through the buffer, advances one byte after an invalid candidate, or uses a separate incomplete-input path. See RECEIVE_BUFFER_STATE.md.

### Numeric readers

The private V1.7 reader helpers assemble 16-bit values big-endian at VA 0x0049D3B0 and 32-bit values big-endian at VA 0x0049D450.

### Qt façade and method strings

Previously recovered method names include:
- ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA);
- ftescAutoGetRealtimeDataAck();
- ftescGetIDResAck(QVector<int>,bool);
- ftescMotorSignalReadAck(QString,bool);
- ftescTopFlowSetupReadAck(QString,bool);
- ftescMotorSignalSecretKeyCheckAck(int).

These method names help target future call-graph analysis. They are not, by themselves, proof of numeric command IDs.

## Public-spec mappings not yet confirmed in the V1.7 binary

The public V1.6 document defines command IDs and payloads in FTESC_UART_PROTOCOL_V1.6.md. The V1.7 static analysis has not yet mapped all numeric command IDs to the app's individual outbound builders and response handlers.

Still to trace end-to-end:
- CMD 00 one-shot and auto-telemetry response decoding;
- CMD 02 UART-control request field order and PAS-mode alias;
- CMD 10 CAN forwarding and slave-response dispatch;
- CMD 11 firmware/hardware identity;
- CMD 19 keepalive and CMD 1A periodic telemetry scheduling;
- CMD 1E master/slave ID enumeration;
- CMD 20 telemetry response;
- CMD 25-27 position, D-axis current and speed request construction.

Do not treat the public V1.6 command list as proof that each command is exposed by the V1.7 GUI or implemented identically.

## V1.6 comparison binaries in Nextcloud

The user's Nextcloud directory contains:
- V1.6 2025-10-14 Windows executable — 97,949,184 bytes;
- V1.6 2026-08-06 Windows executable — 44,867,072 bytes;
- V1.6 2026-09-12 Windows executable — 45,582,336 bytes;
- V1.7 2026-10-29 Windows executable — 50,611,200 bytes.

Only the V1.7 executable is currently staged in /data/samples on REA. The V1.6 binaries have been inventoried but not transferred to the REA host, so binary-to-binary diffing remains open. The V1.6 protocol PDF and associated ECU sample C source were read from Nextcloud and documented here.

## Next steps

1. Trace outbound ftescObtain*/ftescGet* request builders into the frame builder.
2. Find V1.7 response dispatch handlers for command IDs 00, 02, 10, 11, 19, 1A and 1E.
3. Resolve the actual command 02 byte offsets in V1.7 against the public V1.4/V1.6 delta.
4. Trace BLE-specific framing separately; do not assume BLE sends the same raw bytes as UART.
5. Compare the latest V1.6 Windows build with V1.7 after the V1.6 binary is staged locally.
6. Keep hardware interaction out of scope until payload meanings and safety conditions are understood.
