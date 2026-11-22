# V1.7 one-shot CMD 0x02: unresolved path and negative evidence

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Analysis date:** 2026-11-22

## 1. Public V1.6 protocol definition

The public V1.6 UART specification defines command `0x02` as `UART_CONTROL_AND_OBTAIN_DATA_ONCE` in UART input mode:
- INFO/DLEN = 0x0F;
- CMD = 0x02;
- 14 DATA bytes;
- current request is a big-endian 16-bit value at DATA offsets 2–3 (V1.6; V1.4 used offsets 0–1);
- response INFO/DLEN = 0x1C, with 27 DATA bytes of telemetry.

The same numeric command is also a mode-dependent PAS alias. The input-signal mode determines which DATA interpretation applies. See [FTESC_UART_PROTOCOL_V1.6.md](FTESC_UART_PROTOCOL_V1.6.md) and [V1_4_TO_V1_6_PROTOCOL_CHANGES.md](V1_4_TO_V1_6_PROTOCOL_CHANGES.md).

## 2. V1.7 response-side findings

The V1.7 response dispatcher at `0x004997A0` has a large switch on the first INFO byte. The recovered switch cases include 0x00, 0x01, 0x0D, 0x0E, 0x0F, 0x11, 0x14, 0x16, 0x18, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x21, 0x22, 0x24, 0x29 and 0x3A–0x3D. **No case 0x02 is present in this dispatcher.**

The `UartComm` Qt meta-object has 58 methods. Its decoded request methods (indexes 22–57) map to the outbound methods in [V1_7_REQUEST_DISPATCH_MAP.md](V1_7_REQUEST_DISPATCH_MAP.md). None of the mapped methods is an explicit CMD 0x02 request builder.

## 3. The similarly named Qt signal is not a request builder

The UartComm signal `ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA)` exists in the meta-object as signal index 13. Its Qt signature strings are referenced by the connection-setup function at `0x0040B220`, alongside `ftescSignalReadAckToRtData(QString,bool)`.

The evidence establishes a Qt signal and a connection path. It does not establish that this signal constructs or sends UART command 0x02. The signal's name alone must not be treated as proof of the request opcode.

## 4. Current conclusion

- Public V1.6 CMD 0x02 layout is known and documented.
- V1.7 response switch `0x004997A0` does not contain a CMD 0x02 branch.
- The mapped UartComm outbound method table does not expose a direct CMD 0x02 builder.
- A similarly named UartComm signal exists, but it is not itself proof of a request builder.
- Therefore V1.7 CMD 0x02 support remains **unresolved**. It may be implemented through a different class, a QML/native bridge, a separate transport path, or not exposed in this build. None of those possibilities is asserted as fact.

## 5. Next static-analysis targets

1. Trace all references and connections involving the UartComm signal index 13.
2. Inspect QML/resource handlers associated with `onFtescGetRealtimeDataOnce`.
3. Trace the native callers of `ToolLib::waitResponseWithTimeout`, `identifyMotorPara` and `ftescMotorSignalReadAckWaitTimeout`.
4. Search for any byte-append sequence that produces INFO command 0x02 outside the UartComm request table.
5. If no native path is found, record V1.7 CMD 0x02 as not exposed in this build rather than implementing an unsupported request.

No command was sent to an ESC.
