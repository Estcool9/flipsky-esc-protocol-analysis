# V1.7 outbound transmit chain — Qt signal map and CAN-wrapper negative finding

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Analysis date:** 2026-11-22  
**Provider:** Ghidra 12.2 through REA

## 1. Qt meta-object tables recovered

The Qt5 static meta-object records were read from the PE32 data section and their method tables decoded.

| Class | QMetaObject address | Metadata | String table | Static metacall | Relevant methods |
|---|---:|---:|---:|---:|---|
| `FtescLowLevelFace` | `0x0051F218` | `0x00F20D60` | `0x00F215C0` | `0x004B98D0` | index 15 `lowLevelSendDataToFtesc(QByteArray&)`; index 17 `uartCommSendToFtesc(QByteArray&)` |
| `UartComm` | `0x0051F248` | `0x00F22B40` | `0x00F232A0` | `0x004BC2B0` | index 0 signal `sendDataToESC(QByteArray&)` |
| `uartPackData` | `0x0051F260` | `0x00F23FC0` | `0x00F24080` | `0x004BDBA0` | index 0 signal `sendDataToESC(QByteArray&)`; index 1 signal `uartPackDataFromESC(QByteArray&)`; index 2 slot `uartPackDataHandle(QByteArray&)`; index 3 slot timer |

The `FtescLowLevelFace` table has 64 methods, `UartComm` has 58 and `uartPackData` has 4. This gives the exact Qt method IDs needed to trace the old string-based connections, rather than inferring them from the connection strings alone.

## 2. Recovered transmit graph

The normal UartComm INFO-request path is:

```text
UartComm request method (29 callers)
    -> FUN_00495910 (common TX log/send helper)
    -> FUN_004BBC20 (QMetaObject::activate on UartComm, signal index 0)
    -> FtescLowLevelFace::uartCommSendToFtesc (slot index 17)
    -> FUN_004819C0
    -> FUN_0049C5C0 (AA/BB UART frame builder)
    -> FUN_004BDB20 (QMetaObject::activate on uartPackData, signal index 0)
    -> FtescLowLevelFace::lowLevelSendDataToFtesc (slot index 15)
    -> FUN_00481850
    -> FUN_004050C0 (low-level transport write path)
```

Evidence for each part:

- `FUN_004BBC20` passes static-metaobject pointer `0x0051F248` and method index `0` to the Qt activation helper. This is `UartComm::sendDataToESC(QByteArray&)`.
- `FUN_004819C0` jumps directly to `FUN_0049C5C0`.
- `FUN_0049C5C0` builds the UART frame: short marker `0xAA` or extended marker `0xBB`, length, INFO, CRC and `0xDD`; it then calls `FUN_004BDB20`.
- `FUN_004BDB20` passes static-metaobject pointer `0x0051F260` and method index `0` to the Qt activation helper. This is `uartPackData::sendDataToESC(QByteArray&)`.
- `FUN_00481850` forwards the already-prepared byte array to `FUN_004050C0`; this path does not prepend a CAN target ID or command byte.

A separate already-framed send path uses the `uartPackData::sendDataToESC` signal and `FtescLowLevelFace::lowLevelSendDataToFtesc` slot. It is a transport path, not an INFO-to-UART frame builder.

## 3. Common TX helper inspected

`FUN_00495910` has 29 direct callers in the analyzed Ghidra function inventory, including:
- `FUN_00496BF0`: motor-signal setup read, INFO CMD `0x1C`;
- `FUN_004992F0`: ID-over-CAN discovery request, INFO CMD `0x01`;
- `FUN_00499180`: motor identification over CAN, INFO CMD `0x0F`;
- firmware-version, erase, write, control, setup and other UartComm request methods.

The helper reads the existing first INFO byte, and for setup command families logs:
- `TX setup frame command`;
- `canForward` boolean;
- `canId`;
- payload length;
- payload bytes.

The function does not write to the supplied QByteArray buffer. It finishes by passing the same pointer to `FUN_004BBC20`, the UartComm send signal wrapper. The numeric constant `0x10` appears in this diagnostic/log-building sequence; it is not appended to the INFO buffer by this function.

The example `FUN_00496BF0` constructs only INFO CMD `0x1C`, then calls the common helper. `FUN_004992F0` constructs only INFO CMD `0x01`; `FUN_00499180` constructs INFO CMD `0x0F`. None of these builders prepends a `0x10 | SlaveID | SlaveCMD` envelope.

## 4. Conclusion: no generic CMD 0x10 wrapper in the traced V1.7 send path

This is now a strong negative static finding for the **normal UartComm transmit path**:

- the 29 request methods converge on `FUN_00495910`;
- that function logs CAN state but forwards the original byte array;
- the subsequent Qt signal chain adds only the UART `0xAA/0xBB` envelope and sends the resulting frame;
- the already-framed low-level send path also does not add a CMD 0x10 envelope.

Therefore the V1.7 binary does **not** visibly insert the documented V1.6 UART CAN-forward envelope (`0x10 | SlaveID | SlaveCMD | SlaveDATA`) into the normal outbound INFO request path examined here.

The UartComm object still stores CAN-forward state at object offset `+0x0C` and target ID at `+0x10`. The UI can set and clear this state, and the common TX helper prints it. The state does not appear in the outgoing INFO bytes in the traced chain.

This does **not** prove that no alternate path exists elsewhere in the program or in the external USB/CAN gateway. It means the common V1.7 command send path does not implement the generic wrapper at the observed insertion points. The public-protocol offline function `build_can_forward_info()` remains an implementation of the published envelope for a separate client; it must not be described as reproducing V1.7's native send chain.

## 5. What this implies for the UI's CAN selection

The UI's CAN target selection and the low-level transmission behavior are not the same thing. The app:
- stores a CAN-forward enable flag and target ID;
- checks/changes the selected ID in UI handlers;
- iterates candidate IDs during setup discovery;
- logs the CAN-forward state and target ID;
- sends the normal INFO requests through the common TX path.

The exact mechanism by which the UI's target ID is supposed to affect the external gateway, or whether this V1.7 build has a missing/unused feature path, remains unresolved. No live capture is available to show the bytes observed on USB/UART.

## 6. REA evidence anchors

The following retained evidence IDs refer to this exact executable hash in the REA investigation session:
- Qt connection-registration function: `ev_0c9477b94389059396d7b327f6d4197a1d22a1106f624aafd20aa64ab9f03c57`;
- UartComm common TX logger `FUN_00495910`: `ev_0ef35578015ec049fd7540aea7916b1b8295e780ca30081d5895223b4ebdf525`;
- request method CMD 0x1C `FUN_00496BF0`: `ev_2f621b675f398513cd1db5a022ae8ab99809c1726b10f4b60c2e5daff7f87bd3`;
- ID discovery CMD 0x01 `FUN_004992F0`: `ev_4259dc4a181018a667dc85828086970d27eebc8502ccd7d49dcb60738e17f687`;
- motor identify CMD 0x0F `FUN_00499180`: `ev_6af9d2451f9298eeb4193a2f85845aacb88c308b5c61f859e8435f06029c5ec0`;
- UartComm signal `FUN_004BBC20`: instructions show metaobject `0x51F248`, signal index 0;
- uartPackData signal `FUN_004BDB20`: instructions show metaobject `0x51F260`, signal index 0;
- frame builder `FUN_0049C5C0`: `ev_c2a0ba1d4ee64ab2038626044123af160a15cb37f99344123fda4ab8720113c8`;
- low-level send slot `FUN_00481850`: `ev_42f82ca47f2d6ef3fa95d9f4d34f38f2b378bde1d855d761ebb5bdc23a5271a6`;
- common INFO request methods: 29 callers of `FUN_00495910`, evidence `ev_b7db9a7566727058155188ade36e5013c7804266a836bab6ab65387b6022e975`.

## 7. Remaining probes

1. Inspect all QML/ToolLib call paths that change or consume the CAN target, especially any non-UartComm or BLE transport route.
2. Inspect the external USB/CAN gateway protocol/manual for a target-selection side channel.
3. If authorized, compare the V1.6 desktop executable to determine whether the wrapper was present in an earlier build.
4. Capture a passive, non-control UART trace from a known-safe bench setup, then compare the observed frame with the public V1.6 protocol. Do not issue motor control commands as a discovery probe.

No ESC was connected and no control or firmware command was transmitted.
