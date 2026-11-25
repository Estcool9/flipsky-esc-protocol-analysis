# V1.7 TopFlow setup selection and CAN-forward request path

**Binary:** Flipsky_ESC_Tool_V1.7_20261029.exe  
**SHA-256:** dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38  
**Provider:** REA 6.10.1 / Ghidra 12.2  
**Analysis date:** 2026-11-25

## Artifact identity and preservation

The original V1.7 sample was found on CT107 at `/data/samples/Flipsky_ESC_Tool_V1.7_20261029.exe`. Its size is 50,611,200 bytes and its SHA-256 matches the inventory value above. A separate working copy was staged at `/data/analysis/pe/v1.7_20261029/Flipsky_ESC_Tool_V1.7_20261029.exe`, re-hashed and verified. The original sample was not overwritten.

Before opening V1.7, the V1.6 retained Evidence was exported to `/data/analysis/reports/evidence-v1.6-pre-v1.7-20261125.json` and the V1.6 Ghidra program was closed normally to save its owned checkpoint.

## Resource-name evidence

Case-sensitive literal Ghidra string search returned:

| Address | Value | Encoding |
|---|---|---|
| `0x52ed00` | `ftesc/1.7/TopFlowSetupValueTable.xml` | ASCII |
| `0x530557` | `/TopFlowSetupValueTable.xml` | ASCII |
| `0x5e52a5` | `TopFlowSetupValueTable.xml` | UTF-16 |

The first two addresses have Ghidra xrefs from `0x488048` and `0x492aa6` respectively. The UTF-16 object's xrefs were empty in this analysis; that does not prove it has no use.

## Selector and controller name

FUN_00488010 is a small selector helper. Its second argument controls a resource/controller label:

- If the selector equals 1, it returns `ftesc/1.7/TopFlowSetupValueTable.xml`.
- Otherwise, it returns the combined name `ftesc/1.7/MotorSetupValueTable_official.xml + ftesc/1.7/ControlSetupValueTable.xml`.

FUN_00487FC0 uses the same selector convention:

- Selector 1 returns `TopFlowMainController`.
- Other selector values return a protected/obfuscated constant that Ghidra does not resolve to a reliable name.

## Read Setup event path

FUN_0048C700 is the Read Setup button handler. It reads the selector from object offset `+0x40`, marks a read operation active and writes a log entry. It calls FUN_0048AFA0 with the selector. If selector is not 1, it follows the automatic realtime-data ACK path. If selector equals 1, it enters the `manual read setup` branch and calls FUN_004880C0.

FUN_004880C0 is a preflight helper. It returns 0 when the device/target field at object offset `+0x1C` is absent. Otherwise it logs `Prepare config target communication`, emits target/reason diagnostics and returns 1. This is not itself the setup payload sender.

FUN_0048AFA0 records `Read config target type`, `Current target ID` and `Current config XML` diagnostics and calls the table/controller selection helpers with the supplied selector.

## Automatic TopFlow setup read

FUN_004891D0 is an automatic setup dispatcher. It reads the same selector at object offset `+0x40` and, after its connection/pending-state guards:

- dispatches selector 1 to FUN_004972F0;
- dispatches other selector values to FUN_00496BF0.

FUN_004972F0 is explicitly labelled by its embedded log string `Send TopFlow setup read command`. It:

1. guards a pending TopFlow setup response using object offset `+0x44`;
2. clears a pending TopFlow factory-restore ACK flag at `+0x48` when that state is set;
3. copies the configured timeout from `+0x24` into the pending counter;
4. calls the command factory helper FUN_0049CE30 with argument `0x3B`;
5. logs canForward at `+0x0C` and CAN target ID at `+0x10`;
6. submits the created payload to FUN_00495910.

This directly ties the TopFlow setup read path to INFO command byte `0x3B` and the shared V1.7 TX helper. It is a static call-path result, not a captured UART frame.

## V1.7 CAN-forward helper path

FUN_00495910 reads the first byte of the supplied QByteArray. When UartComm canForward (`+0x0C`) is enabled, it calls PTR_FUN_00F591C0:

1. with the selected CAN ID from UartComm `+0x10`;
2. then with literal `0x10`.

It then forwards to FUN_004BBC20, which activates the UartComm send signal. The helper has 29 request-method callers in the active Ghidra function inventory. TopFlow FUN_004972F0 is one of its callers, so command 0x3B traverses this canForward logic.

The helper has a diagnostic branch for first-byte command ranges `0x1B–0x1D` and `0x3A–0x3D`; 0x3B is inside this range. The helper-call pair is also present in its common path outside that diagnostic branch when canForward is enabled.

### Protected-code limitation

PTR_FUN_00F591C0 points to `0x00B5AADC`; Ghidra reports invalid/truncated instructions at that location. The lower send pointer PTR_FUN_00F591F0 points to `0x00B5AC7C`, which is similarly undecodable. Thus the function-call order is confirmed, but the actual bytes appended/emitted by the protected function and the exact wire envelope remain unknown. Do not claim the final byte sequence without resolving the helper or obtaining an authorized passive capture.

## Facts, inferences and unknowns

**Confirmed:** selector 1 selects TopFlowMainController and the TopFlow XML resource name; the Read Setup handler chooses the manual path for selector 1; the automatic dispatcher routes selector 1 to FUN_004972F0; FUN_004972F0 requests command 0x3B and calls FUN_00495910; the shared TX helper calls the CAN helper with canId then 0x10 when canForward is set.

**Strong inference, not byte-level proof:** the two protected calls build the CAN-forward wrapper in the same functional pattern observed in the V1.6 TX helper.

**Unknown:** actual TopFlow XML resource bytes; exact product/SKU represented by selector 1; exact bytes produced by PTR_FUN_00F591C0; slave response correlation and retry semantics; whether all non-UartComm transports share this helper.

## Evidence IDs

- string search: `ev_8af1e4554c4ea676dc76a0ef18e14f0ef77a04d6c76e5242cb4802ee51b2d4f3`
- FUN_00488010: `ev_235d3fba5a5d3ea3a0063220e75e6dcf0ce439b7948bf7a6c176853bae419996`
- FUN_00487FC0: `ev_a82cc7b9bf1948d1816ecf5567a313c838d888e60a92b01e7a317d3f3a080e2f`
- FUN_0048C700: `ev_3c9d8b16b9747ab4221f94a6c1b0a053881cc6edb97777dc54e20dea8c07b554`
- FUN_004880C0: `ev_e2339b727737a8cf52ceb8d17ddf62e09389d75d6b92163a67a1e95d688a4b60`
- FUN_004891D0: `ev_c27bf81fea929e1d3069e6b0484aec9fc1b055a2d27fe81beb77b183f5ae48f9`
- FUN_004972F0: `ev_3459543a9785d2fb17b4791c0aa3d262101352745b8df0e697175642abe9b634`
- FUN_00495910: `ev_5577ccc5290ab681440823555f6ab93ba5406f09896f8c684001c6f96e6b6b4b`
- protected helper target 0x00B5AADC: `ev_f1e0c84aed38e694a28b7b208a1650f038ce257411ee5d7d2b28186525799143`

## Next work

1. Recover or independently characterize the two Enigma-protected helper targets without executing the PE.
2. Extract the actual TopFlow RCC/XML bytes using a bounded raw-resource scanner appropriate for the malformed/overlapping PE section mapping.
3. Trace the selector `+0x40` writers and map its values to actual device families/SKUs.
4. Trace TopFlow response/ACK parsing and slave response correlation.

No executable was run, no ESC was connected, and no UART/CAN/BLE command or firmware write was transmitted.
