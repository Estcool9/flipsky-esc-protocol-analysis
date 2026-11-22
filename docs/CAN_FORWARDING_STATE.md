# V1.7 CAN target selection and forwarding state

**Binary:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Analysis date:** 2026-11-22

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
- The exact native instruction path that inserts the public protocol's CAN wrapper (CMD 0x10 + CAN ID + nested command/data) into the outgoing INFO payload.
- Whether all generic UartComm requests are wrapped when the flag is enabled, or only selected operations.
- Slave response routing and how the returned CAN ID is correlated with pending request callbacks.
- The full timing unit and timeout/retry policy for all CAN-target requests.

The public V1.6 UART document describes CMD 0x10 as the CAN-forward envelope, and the third-party FT85BD implementation independently contains a CAN wrapper. Those references are useful cross-checks, but they do not replace tracing the V1.7 call path. See [EXTERNAL_IMPLEMENTATION_CROSSCHECK.md](EXTERNAL_IMPLEMENTATION_CROSSCHECK.md) and [FTESC_UART_PROTOCOL_V1.6.md](FTESC_UART_PROTOCOL_V1.6.md).

## 6. Safety and validation

No CAN or UART command was transmitted. No physical ESC was connected. Do not infer that a target ID, setup read, or generic control operation is safe merely because the UI offers it.
