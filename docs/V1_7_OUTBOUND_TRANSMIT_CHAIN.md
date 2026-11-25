# V1.7 outbound transmit chain — Qt signal map and CAN-forward helper calls

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Analysis date:** 2026-11-25  
**Provider:** Ghidra 12.2 through REA

## 1. Qt meta-object tables recovered

| Class | QMetaObject address | Metadata | String table | Static metacall | Relevant methods |
|---|---:|---:|---:|---:|---|
| `FtescLowLevelFace` | `0x0051F218` | `0x00F20D60` | `0x00F215C0` | `0x004B98D0` | index 15 `lowLevelSendDataToFtesc(QByteArray&)`; index 17 `uartCommSendToFtesc(QByteArray&)` |
| `UartComm` | `0x0051F248` | `0x00F22B40` | `0x00F232A0` | `0x004BC2B0` | index 0 signal `sendDataToESC(QByteArray&)` |
| `uartPackData` | `0x0051F260` | `0x00F23FC0` | `0x00F24080` | `0x004BDBA0` | index 0 signal `sendDataToESC(QByteArray&)`; index 1 signal `uartPackDataFromESC(QByteArray&)`; index 2 slot `uartPackDataHandle(QByteArray&)`; index 3 slot timer |

`FtescLowLevelFace` has 64 methods, `UartComm` has 58 and `uartPackData` has 4.

## 2. Transmit graph

```text
UartComm request method
    -> FUN_00495910 (common TX helper; conditionally invokes CAN helper)
    -> FUN_004BBC20 (UartComm::sendDataToESC signal index 0)
    -> FtescLowLevelFace::uartCommSendToFtesc (slot index 17)
    -> FUN_004819C0
    -> FUN_0049C5C0 (AA/BB UART frame builder)
    -> FUN_004BDB20 (uartPackData::sendDataToESC signal index 0)
    -> FtescLowLevelFace::lowLevelSendDataToFtesc (slot index 15)
    -> FUN_00481850
    -> FUN_004050C0 (low-level transport write path)
```

- FUN_004BBC20 activates UartComm meta-object `0x0051F248`, signal index 0.
- FUN_004819C0 calls the UART frame builder FUN_0049C5C0.
- FUN_0049C5C0 builds the AA/BB UART frame (marker, length, INFO, CRC, DD), then activates uartPackData signal index 0 through FUN_004BDB20.
- FUN_00481850 forwards the already-framed byte array to FUN_004050C0; no additional CAN insertion was observed at this later transport layer.

## 3. V1.7 CAN-forward calls in FUN_00495910

The earlier negative conclusion that this function forwarded the QByteArray unchanged is superseded. Re-analysis of the complete pseudocode shows that, when the UartComm CAN-forward flag at object offset `+0x0C` is non-zero, FUN_00495910 calls PTR_FUN_00F591C0 twice before the UartComm signal:

1. With the CAN target ID read from object offset `+0x10`.
2. With literal `0x10`.

After this path the helper reaches FUN_004BBC20(param_1). The calls occur in the common helper, which has 29 request-method callers in the current Ghidra function inventory.

The helper also has a diagnostic branch when the first INFO byte is in ranges `0x1B–0x1D` or `0x3A–0x3D`. It logs the setup command byte, CAN-forward flag, CAN ID, payload length and payload bytes. The CAN helper calls also exist in the common path outside that diagnostic branch when canForward is enabled.

### Enigma limitation

The pointer at `0x00F591C0` resolves to `0x00B5AADC`. Ghidra reports invalid/truncated instructions there, consistent with the protected Enigma region. The lower send pointer at `0x00F591F0` resolves to `0x00B5AC7C` and is similarly undecodable. Therefore the invocation order is confirmed, but the exact byte-level result of those helper calls is **not** established by the current static pseudocode. Do not translate the calls directly into a claimed literal `[0x10][CAN_ID]` byte sequence without the helper semantics or a passive frame capture.

## 4. TopFlow setup read uses this CAN-capable helper

- Read Setup selector is stored at object offset `+0x40`. FUN_00488010 selects the TopFlow XML path for selector value 1; FUN_00487FC0 selects `TopFlowMainController` for the same value.
- Automatic dispatch FUN_004891D0 uses selector 1 to call FUN_004972F0; other selector values use FUN_00496BF0.
- FUN_004972F0 logs `Send TopFlow setup read command`, calls the command factory helper FUN_0049CE30 with `0x3B`, records canForward/canId and sends via FUN_00495910.
- Command `0x3B` is in the TX helper's diagnostic setup-command range `0x3A–0x3D`. Thus the TopFlow setup read enters the same V1.7 canForward helper path.

This is static evidence of the code path, not a live frame capture. Selector value 1's exact product/SKU meaning and the TopFlow XML payload remain unresolved.

## 5. V1.6 comparison

The V1.6 common TX helper FUN_00492AB0 calls its own protected helper with CAN ID (`UartComm +0x10`) then `0x10` when canForward (`+0x0C`) is set, before the standard UART frame builder. V1.7 FUN_00495910 now shows the same ordered helper-call pattern. The protected helper implementations and resulting bytes are not yet compared at instruction level.

## 6. Evidence anchors

- V1.7 common TX helper FUN_00495910: `ev_5577ccc5290ab681440823555f6ab93ba5406f09896f8c684001c6f96e6b6b4b`.
- TopFlow request FUN_004972F0: `ev_3459543a9785d2fb17b4791c0aa3d262101352745b8df0e697175642abe9b634`.
- protected CAN helper target 0x00B5AADC: `ev_f1e0c84aed38e694a28b7b208a1650f038ce257411ee5d7d2b28186525799143`.
- lower send target 0x00B5AC7C: `ev_8accd59be9997c704d43f6deae64be031d3ad4dec78ae3a9964b4ab8ef4cc14a`.
- TopFlow selector helper FUN_00488010: `ev_235d3fba5a5d3ea3a0063220e75e6dcf0ce439b7948bf7a6c176853bae419996`.
- Read Setup event handler FUN_0048C700: `ev_3c9d8b16b9747ab4221f94a6c1b0a053881cc6edb97777dc54e20dea8c07b554`.
- Qt connection-registration and UART framing/transport evidence remain as recorded in earlier versions of this document; those paths were not modified by this re-analysis.

## 7. Remaining work

1. Recover the protected helper semantics and exact CAN envelope bytes without guessing from argument order.
2. Resolve slave response routing and pending callback correlation.
3. Extract TopFlowSetupValueTable.xml and map the selector to actual product/SKU profiles.
4. Validate only with authorized passive traces and a safe, isolated bench plan; no control commands or firmware writes during reverse engineering.

No ESC was connected and no control or firmware command was transmitted.
