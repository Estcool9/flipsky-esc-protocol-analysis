# V1.7 CAN target selection and forwarding state

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Analysis date:** 2026-11-25

## 1. UartComm CAN state fields

The UartComm object contains two fields used by the CAN target UI:

| Object offset | Observed type | Accessor | Meaning |
|---:|---|---|---|
| `+0x0C` | byte/boolean | `FUN_00495510` | CAN-forward enabled state |
| `+0x10` | 32-bit integer | `FUN_00495520` | selected CAN target ID |

Setter `FUN_004954D0(enable, target)`:
- if `target >= 0`, stores it at `+0x10`;
- if `target < 0` while the current target is also negative, clears the enable flag and returns;
- otherwise stores the requested enable byte at `+0x0C`.

The accessors return these fields directly. The application UI validates selected IDs below `0xFF` before enabling a target.

## 2. UI call sites

### CAN target selection

The function at `0x0048CE90` contains the CAN target selection flow:
- when the selected target is cleared, it calls `FUN_004954D0(0, -1)`;
- when a target is selected, it parses the selected ID, rejects values `>= 0xFF`, then calls `FUN_004954D0(1, target_id)`;
- it invokes `FUN_00496BF0` to request motor-signal setup for the selected target and waits for the corresponding `ftescMotorSignalReadAck(QString,bool)` signal, with a 200 ms local wait in this UI path.

A related target-change handler at `0x0048D740` compares the new ID with the stored ID and updates the CAN target state before requesting setup again.

### Automatic ID discovery

The UI maintenance method at `0x004890C0`:
1. checks the connection state;
2. clears the current CAN-forward target;
3. calls `FUN_004992F0`.

`FUN_004992F0`:
- refuses to start if the pending-ID counter at object offset `+0x40` is positive;
- sets that counter to 200;
- builds an INFO payload beginning with command byte `0x01`;
- submits it through the common send path.

This is the V1.7 implementation of the request previously identified as `ftescObtainIdOverCan`. The 200 value is an internal counter; its time unit is not established here.

### Per-target setup iteration

The function at `0x00493B80` reads the current CAN-forward state and target ID, iterates over candidate IDs, temporarily selects a target with `FUN_004954D0(1, id)`, and calls `FUN_00496BF0` to request motor-signal setup. It restores the prior target state at the end of the iteration.

This is evidence for a multi-target setup discovery/read workflow in the desktop application, not proof that every control request is broadcast to every ESC.

## 3. Requests made while a target is selected

`FUN_00496BF0`:
- checks the pending setup-read counter at object offset `+0x2C`;
- if another request is pending, logs and skips the new read;
- otherwise copies the configured timeout value from object offset `+0x24` into `+0x2C`;
- builds an INFO payload beginning with `0x1C`;
- passes it to `FUN_00495910`.

`FUN_004972F0` is the corresponding TopFlow setup read:
- checks/clears pending factory-restore state;
- guards the pending counter at object offset `+0x44`;
- builds an INFO payload beginning with `0x3B`;
- sends it through the same logging/send path.

The send diagnostic helper `FUN_00495910` logs the first payload byte, CAN-forward flag, selected CAN ID, payload length and payload bytes, then activates the common send signal through `FUN_004BBC20`. Its decompiled body does not itself prepend or rewrite a CAN envelope.

## 4. Motor-identification request

The native implementation `0x00499180` is the request method `ftescIdentifyMotorOverCan`. It accepts five arguments and serializes byte-sized, 16-bit and scaled numeric fields before passing the payload through the common send helper. The request map identifies command `0x0F`; exact field names and all argument units are still being validated.

## 5. What is and is not established

**Established from V1.7 code:**
- CAN-forward enable state and target ID are stored in UartComm.
- UI selection validates a target ID below 255 and changes the state.
- Auto-discovery sends command 0x01 and uses a pending counter.
- The app uses selected CAN targets when requesting motor-signal and TopFlow setup.
- The shared send logger reports the active CAN state and ID.

**Not yet established from V1.7 code:**
- The exact bytes produced by the Enigma-protected CAN helper and the slave response correlation path.
- Whether send routes that bypass FUN_00495910 (for example already-framed low-level paths) use the same CAN helper.
- Slave response routing and how the returned CAN ID is correlated with pending request callbacks.
- The full timing unit and timeout/retry policy for all CAN-target requests.

The public V1.6 UART document describes CMD 0x10 as the CAN-forward envelope. The offline client now implements `build_can_forward_info()` and `parse_can_forward_response()`, and the direct-CAN layer has its own ID/CRC/telemetry/control codec. The third-party FT85BD implementation independently contains a CAN wrapper. These references define the protocol expected by an independent client, but they do not replace tracing the V1.7 desktop call path. See [EXTERNAL_IMPLEMENTATION_CROSSCHECK.md](EXTERNAL_IMPLEMENTATION_CROSSCHECK.md), [FTESC_UART_PROTOCOL_V1.6.md](FTESC_UART_PROTOCOL_V1.6.md) and [FTESC_CAN_PROTOCOL_V1.4.md](FTESC_CAN_PROTOCOL_V1.4.md).

## 6. Safety and validation

No CAN or UART command was transmitted. No physical ESC was connected. Do not infer that a target ID, setup read, or generic control operation is safe merely because the UI offers it.


## 7. Direct CAN protocol is a separate layer

The user's Nextcloud contains the official Flipsky **FTESC CAN Communication Protocol V1.4** (document FT-CM-CAN-20250423-04, issue date 2025-04-23, 22 pages). It defines direct 29-bit extended CAN identifiers with ESC ID in bits 8–15 and CAN command in bits 0–7, separate from the UART INFO command byte.

The V1.4 CAN command namespace includes direct-CAN current/duty/eRPM/position commands (0x00–0x05, 0x12–0x14), periodic telemetry commands (0x0B–0x0D), and non-CRC variants (0x15–0x1B). This is not the UART command namespace: direct CAN command 0x00 is current-with-gear, whereas UART INFO command 0x00 is realtime telemetry.

A separate offline decoder is implemented in `scripts/ftesc_can.py`; see [FTESC_CAN_PROTOCOL_V1.4.md](FTESC_CAN_PROTOCOL_V1.4.md). It decodes identifiers and read-only telemetry, but it does not prove where V1.7 inserts its UART CMD 0x10 forwarding envelope.


## 8. Older C reference cross-check

The user's V1.4–V1.6 C reference declares `UART_CAN_FWARD=0x10` but does not implement the CAN-forward wrapper. This confirms the command's existence but does not reveal the payload envelope. The V1.7 wrapper insertion and slave response routing remain unresolved; see [V1_6_C_REFERENCE_CROSSCHECK.md](V1_6_C_REFERENCE_CROSSCHECK.md).


## 9. Official FTESC Gateway product cross-check

Flipsky's official FTESC Gateway product page describes:
- firmware V1.6 or above;
- USB, CAN, UART, PPM and ADC ports;
- USB passthrough that lets the host directly access, identify and configure a specific ESC by CAN ID;
- unique CAN IDs for multiple ESCs and a uniform CAN baud rate.

Source: [Flipsky FTESC Gateway Interface Module](https://flipsky.net/collections/new-arrival/products/flipsky-ftesc-gateway-interface-module-multi-esc-networked-cooperative-control-for-ftesc-series).

This confirms the product-level USB-to-CAN passthrough use case and explains why the V1.7 application stores a selected CAN ID. It does **not** reveal the exact CMD 0x10 envelope or prove that the V1.7 desktop binary emits CMD 0x10. The wire-level wrapper remains unresolved.


## 10. V1.7 common TX helper re-analysis — CAN helper calls confirmed (2026-11-25)

The earlier negative conclusion that FUN_00495910 forwarded the QByteArray unchanged was too broad and is superseded by a direct re-analysis of its full pseudocode.

FUN_00495910 reads the first INFO byte from the supplied QByteArray. When UartComm canForward at offset +0x0C is non-zero, it invokes PTR_FUN_00f591c0 twice before sending:

1. First with the selected CAN ID read from UartComm offset +0x10.
2. Then with literal 0x10.

It then reaches FUN_004bbc20(param_1), whose body dispatches through PTR_FUN_00f591f0. The helper has 29 callers in the active V1.7 Ghidra inventory. The calls are present in the common TX function, not only in a UI diagnostic.

For non-empty payloads, the function contains a separate diagnostic path for first-byte commands 0x1B–0x1D and 0x3A–0x3D. The TopFlow read command 0x3B is in that range. The CAN helper invocations also exist on the common path outside that diagnostic range when canForward is enabled.

### TopFlow path into the helper

- FUN_004972f0 is explicitly labelled by the embedded log string “Send TopFlow setup read command”.
- It calls the command factory helper FUN_0049ce30 with value 0x3B, logs canForward and canId from the UartComm object, then calls FUN_00495910.
- Thus the TopFlow 0x3B read request reaches the V1.7 CAN helper when forwarding is enabled.

### What is confirmed and what remains unknown

**Confirmed from decompiled code:** the common V1.7 TX helper calls a protected function pointer with canId followed by 0x10 before the common send signal whenever canForward is enabled. This supersedes the earlier statement that FUN_00495910 did not insert any CAN wrapper operation.

**Not yet confirmed:** the exact resulting byte sequence. The pointer at 0x00F591C0 resolves to 0x00B5AADC; Ghidra sees invalid/truncated instructions in this Enigma-protected area. The lower send pointer at 0x00F591F0 resolves to 0x00B5AC7C and is similarly undecodable. The order of calls is observed, but do not infer a final literal byte layout from those calls alone. No passive USB/UART capture has been made.

REA evidence: FUN_00495910 parent `ev_5577ccc5290ab681440823555f6ab93ba5406f09896f8c684001c6f96e6b6b4b`; TopFlow request FUN_004972f0 parent `ev_3459543a9785d2fb17b4791c0aa3d262101352745b8df0e697175642abe9b634`; pointer target analysis `ev_f1e0c84aed38e694a28b7b208a1650f038ce257411ee5d7d2b28186525799143`.

---
## 11. V1.6 TX helper — CMD 0x10 insertion confirmed in-band (2026-11-25)

**Binary:** V1.6 2026-09-12 (`051d57a7…`)  
**Function:** `FUN_00492ab0`  
**Evidence:** `ev_8bdacaa9c6eb4c4e31b3c9da89f2389f5dd77756f2f86b4b36a1d7f7cd97ca07` (search_strings), `ev_9407521b152a83ed0c9eb9e261cdfff4faea8a455c2c11d9a5c1fbe5020ed0ca` (analyze_function summary)

The V1.6 common TX send helper `FUN_00492ab0` was decompiled via REA/Ghidra 12.2. Its pseudocode shows:

```c
void FUN_00492ab0(undefined4 param_1)  // param_1 = QByteArray* payload
{
  // in_ECX = 'this' pointer (UartComm object)
  if (*(char *)(in_ECX + 0x0C) != '\0') {       // canForward enable at +0x0C
    PTR_FUN_00c53314((int)*(char *)(in_ECX + 0x10));  // push CAN slave ID (+0x10)
    PTR_FUN_00c53314(0x10);                           // push CMD 0x10 wrapper byte
  }
  // ... Qt-locked log "Sending to ESC:" ...
  PTR_FUN_00c535b0(param_1);    // frame builder: wraps payload → UART INFO frame
  // ... cleanup ...
  FUN_004b55f0(param_1);
}
```

**Confirmed facts (DIRECT CODE EVIDENCE):**
- UartComm offset `+0x0C` = CAN-forward enable flag (byte, non-zero = active). REA evidence ev_9407521b.
- UartComm offset `+0x10` = CAN slave target ID (byte/char). REA evidence ev_9407521b.
- When canForward is active, V1.6 calls the UUID helper (`PTR_FUN_00c53314`) twice:
  1. With the slave target ID from `+0x10`.
  2. With the literal value `0x10` (CMD byte for CAN-forward wrapper).
- The standard UART frame builder (`PTR_FUN_00c535b0`) is called with the original payload afterward.
- String `"Sending to ESC:"` is embedded in this function (address in V1.6 2026-09-12 string table, found by procedure_pseudo_code).
- 25 callers, 11 direct callees, 14 computed call sites.

**Architectural difference V1.6 vs V1.7 (CONFIRMED):**
- **V1.6:** CMD 0x10 wrapper inserted inline in the common TX send helper `FUN_00492ab0` by calling the UUID helper with the slave ID then with `0x10`.
- **V1.7:** The equivalent send logger `FUN_00495910` does **not** insert any CAN envelope; it passes the QByteArray unmodified to the frame builder signal. The CAN fields (`+0x0C`, `+0x10`) are stored in V1.7's UartComm but not observed being used to prepend CMD 0x10 in the normal transmit chain.

**Remaining unknowns:**
- The exact byte-level sequence produced by the two `PTR_FUN_00c53314` calls (Enigma-protected, Ghidra reports 1-byte body, unresolvable).
- Whether V1.7 performs the CMD 0x10 insertion in a separate path not yet traced (e.g., through a different signal or BLE transport).
- Slave response routing in both versions.

## 12. V1.7 TopFlow table/controller selection (2026-11-25)

- Selector object offset +0x40 is passed to FUN_00488010 and FUN_00487FC0. Selector value 1 selects `ftesc/1.7/TopFlowSetupValueTable.xml` and controller name `TopFlowMainController`; other values select the combined Motor/Control setup table route.
- Read Setup handler FUN_0048c700 reads +0x40. Value 1 follows the manual setup path; the automatic setup dispatcher FUN_004891D0 sends selector 1 to FUN_004972F0 and other values to FUN_00496BF0.
- FUN_004972F0 creates the TopFlow setup read command using 0x3B, guards pending response/factory-restore state, logs CAN state, and forwards through FUN_00495910.
- This establishes TopFlow request selection and that CMD 0x3B uses the shared CAN-forward helper when enabled. The exact model/SKU represented by selector 1 and the XML bytes remain unknown.
- The file is staged and open in REA at `/data/analysis/pe/v1.7_20261029/`; SHA-256 matches the inventory. The V1.6 Evidence bundle was exported and its checkpoint saved before switching targets.