# Analysis checkpoint — 2026-11-25

**Repository:** `Estcool9/flipsky-esc-protocol-analysis`  
**Overall project progress: 72.6% unrounded (73% rounded)** (weighted full open-source desktop replacement; 79.9 / 110 points; authoritative weights in [STATUS.md](STATUS.md)).  
**Executable SHA-256 (V1.7):** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Executable SHA-256 (V1.6 2026-09-12 active):** `051d57a776782ae8daaeaa45179f9b568f7e89b4a78ab8dd8e558ecd3e53b968`

This is the authoritative hand-off note. Update it at every significant milestone. The latest V1.7 findings below supersede the earlier V1.7 CAN-wrapper negative conclusion.

## Previous milestone: V1.6 CMD 0x10 CAN wrapper confirmed in TX helper (2026-11-25)

- REA/Ghidra 12.2 decompiled `FUN_00492ab0` (V1.6 2026-09-12 common TX send helper).
- **CONFIRMED:** UartComm offset `+0x0C` = CAN-forward enable (byte). UartComm offset `+0x10` = CAN slave target ID (byte).
- **CONFIRMED:** When canForward active, V1.6 TX helper calls UUID helper `PTR_FUN_00c53314` twice — first with the slave ID (from `+0x10`), then with the value `0x10` (CMD byte). This is the inline CAN-forward wrapper insertion.
- **CONFIRMED ARCHITECTURAL DIFFERENCE:** V1.6 inserts CMD 0x10 inline in its TX helper. V1.7's equivalent (`FUN_00495910`) does NOT insert any CAN envelope in the normal transmit chain.
- 229 evidence records, 148 MB retained in Ghidra checkpoint.
- Evidence IDs: `ev_9407521b152a83ed0c9eb9e261cdfff4faea8a455c2c11d9a5c1fbe5020ed0ca` (analyze_function summary), pseudocode in `ev_8bdacaa9c6eb4c4e31b3c9da89f2389f5dd77756f2f86b4b36a1d7f7cd97ca07` context.
- Commit: `7464055983d5de47cf25ea54f1e884b118c0e2fe`

## Latest milestone: V1.7 TopFlow read path and CAN-forward TX helper traced (2026-11-25)

### Artifact staging and session preservation

- Verified the V1.7 executable on CT107 at /data/samples/Flipsky_ESC_Tool_V1.7_20261029.exe: 50,611,200 bytes, SHA-256 dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38.
- Created a separate read-only analysis copy at /data/analysis/pe/v1.7_20261029/Flipsky_ESC_Tool_V1.7_20261029.exe; its SHA-256 and size match the expected artifact identity. The original /data/samples file was preserved.
- Before switching the live Ghidra target, exported the V1.6 investigation to /data/analysis/reports/evidence-v1.6-pre-v1.7-20261125.json (232 evidence records, 19,440,198 bytes), then closed V1.6 normally so its owned checkpoint was saved.
- Opened the staged V1.7 copy in REA/Ghidra 12.2. The active target hash is the expected V1.7 SHA-256.
- REA inspect_pe_resources rejects this custom PE with “PE section raw bytes overlap headers”; Ghidra itself loads the PE. Qt resource bytes still need a separate bounded extraction path.

### TopFlow table and controller selection

- Case-sensitive literal search found ftesc/1.7/TopFlowSetupValueTable.xml at 0x52ed00, /TopFlowSetupValueTable.xml at 0x530557, and the UTF-16 name at 0x5e52a5. Xrefs from the first two resolve to 0x488048 and 0x492aa6 respectively.
- FUN_00488010 selects ftesc/1.7/TopFlowSetupValueTable.xml when its second argument equals 1; other values select the combined MotorSetupValueTable_official.xml + ControlSetupValueTable.xml path.
- FUN_00487fc0 maps selector 1 to the controller name TopFlowMainController.
- Read Setup handler FUN_0048c700 reads the selector from object offset +0x40. Selector 1 follows the manual read setup path; other values follow the automatic realtime-data ACK path.
- FUN_004880c0 is a target-communication preflight: it returns 0 if the device/target field at +0x1c is absent; otherwise it logs “Prepare config target communication”, the target and reason, and returns 1.
- FUN_004891d0's automatic setup dispatcher reads the same +0x40 selector; selector 1 dispatches FUN_004972f0, otherwise it dispatches FUN_00496bf0.
- FUN_004972f0 is explicitly logged as “Send TopFlow setup read command”. It clears/guards pending TopFlow factory-restore/read state, calls FUN_0049ce30(0x3B), logs canForward and canId, then calls FUN_00495910. This identifies INFO command 0x3B as the TopFlow setup-read request path in this binary.
- Selector value 1 is confirmed to choose the TopFlow controller/table and manual setup path. Its exact product/SKU meaning is still unknown; the actual XML resource payload has not yet been extracted.

### V1.7 CAN-forward wrapper: correction to the earlier negative finding

- Re-analysis of FUN_00495910 shows that when the UartComm CAN-forward flag at this+0x0C is non-zero, the function calls PTR_FUN_00f591c0 first with the CAN target ID at this+0x10 and then with literal 0x10 before calling FUN_004bbc20(param_1).
- This branch is present on the shared V1.7 TX helper used by the TopFlow 0x3B request. The function has 29 callers. The debug branch recognizes command-byte ranges 0x1B–0x1D and 0x3A–0x3D; 0x3B is in the latter range.
- The previous conclusion that V1.7 FUN_00495910 simply passed the QByteArray unchanged was too broad and is superseded by this direct re-analysis. The helper calls are visible in pseudocode; do not keep the old “no CAN wrapper in the V1.7 common helper” conclusion.
- Exact byte-level output is not yet established: PTR_FUN_00f591c0 resolves to 0x00b5aadc and the lower send pointer PTR_FUN_00f591f0 resolves to 0x00b5ac7c, both in the Enigma-protected region where Ghidra reports invalid/truncated instructions. The order of helper calls (canId, then 0x10) is observed, but the actual resulting byte sequence and wire capture remain unknown.

### Bounded Qt/RCC and raw-resource scan (2026-11-25)

- Rizin recognizes the V1.7 file as PE32 x86. Its parsed .rdata section maps raw file offsets 0x11DA00–0xB28E00 (size 0xA0B200); no .rsrc section is listed and `rz-bin -U` returns an empty standard PE resource list.
- A bounded read-only zlib scan of .rdata tested signatures 78 01, 78 5E, 78 9C and 78 DA: 1,197 candidate headers, 41 complete streams, 36 unique decompressed payloads, and 19 valid XML roots. Those 19 XML documents are ValueSetups resources; none contains TopFlowSetupValueTable.
- The same signature scan over the remaining file regions found 2,648 candidate headers and zero complete streams. This only rules out the tested zlib signatures in those regions; it does not rule out Enigma-protected, transformed or differently encoded resources.
- Raw byte search finds additional XML-declaration candidates at file offsets 0xD8E14A, 0xDA0A20 and 0x22A50CF. Their surrounding bytes are garbled/non-UTF-8 and do not parse as XML; treat them as protected or otherwise undecoded candidates, not extracted resources.
- Rizin strings include qResourceFeatureZlib and qRegisterResourceData at VAs 0xF5A81A and 0xF5A836. Ghidra reports no xrefs for those strings, so their presence alone does not prove the resource-registration routine or specific table bytes.
- V1.7 Evidence bundle exported to `/data/analysis/reports/evidence-v1.7-topflow-can-20261125-final.json`: 308 records, 32,692,246 bytes, 0 unknowns, SHA-256 `3b94f6ae5e3ab59b9031c517ab33c4e642f876e612490bc7c23aa1f0fce25413`.

### Evidence anchors

- TopFlow string search: ev_8af1e4554c4ea676dc76a0ef18e14f0ef77a04d6c76e5242cb4802ee51b2d4f3.
- TopFlow selector helper FUN_00488010: ev_235d3fba5a5d3ea3a0063220e75e6dcf0ce439b7948bf7a6c176853bae419996.
- TopFlow controller-name helper FUN_00487fc0: ev_a82cc7b9bf1948d1816ecf5567a313c838d888e60a92b01e7a317d3f3a080e2f.
- Read Setup handler FUN_0048c700: ev_3c9d8b16b9747ab4221f94a6c1b0a053881cc6edb97777dc54e20dea8c07b554.
- Manual preflight FUN_004880c0: ev_e2339b727737a8cf52ceb8d17ddf62e09389d75d6b92163a67a1e95d688a4b60.
- Automatic TopFlow request FUN_004972f0: ev_3459543a9785d2fb17b4791c0aa3d262101352745b8df0e697175642abe9b634.
- V1.7 TX helper FUN_00495910: ev_5577ccc5290ab681440823555f6ab93ba5406f09896f8c684001c6f96e6b6b4b.
- Protected pointer target at 0x00b5aadc: ev_f1e0c84aed38e694a28b7b208a1650f038ce257411ee5d7d2b28186525799143; lower send target at 0x00b5ac7c: ev_8accd59be9997c704d43f6deae64be031d3ad4dec78ae3a9964b4ab8ef4cc14a.

Detailed report: [V1.7 TopFlow selection and CAN-forward trace](V1_7_TOPFLOW_CAN_FORWARD_TRACE.md).

### Next probes

1. Determine the Enigma-protected helper semantics and exact serialized CAN envelope without assuming the two calls equal a particular byte layout.
2. Extract the actual TopFlow Qt resource payload with a bounded raw/RCC-aware scan; then map table IDs and product/SKU selector values.
3. Trace TopFlow response parsing, ACK correlation and slave response routing.
4. Continue the V1.7 CMD 0x02 and firmware/bootloader paths, then update tests/docs only when supported by evidence.

## Previous milestone: 177 passing tests, V1.6/V1.7 cross-build comparison

- Fresh REA clone: 177 tests passed, zero failures; compileall passed. CI run #301.
- Flipsky VESC V1.0 UART/CAN codecs added and tested.
- Full bounded XML scan found 19 unique ValueSetup resources; catalog now has 1,152 rows, 286 distinct XML IDs, 1,135 ValueSeque entries and 17 omissions.
- The initial V1.7 negative finding on CMD 0x10 was superseded on 2026-11-25: FUN_00495910 calls its CAN helper with canId then 0x10 when canForward is active. Exact emitted bytes remain obscured by Enigma; see the latest milestone and CAN_FORWARDING_STATE.md.
- V1.6/V1.7 static marker comparison published, three-build UUID helper trace, VirtualProtect call mapping.
- TopFlow metadata, full firmware state machine, BLE transport V1.7 and desktop client remain incomplete.

## Outer framing and CRC

- Short: `AA | LEN8 | PAYLOAD | CRC16_BE | DD`.
- Extended: `BB | LEN16_BE | PAYLOAD | CRC16_BE | DD`.
- Sender uses AA for payload lengths 1–255, BB above 255.
- Receiver rejects empty AA payloads and BB lengths <=254.
- Constructor at `0x0049C460` initializes max payload at `this+0x20` to `0x2710` = 10,000.
- CRC-16/MODBUS: reflected polynomial A001, init FFFF, xorout 0000; payload only; serialized big-endian.
- Tables at `0x005310C0` and `0x005311C0` match generated split MODBUS tables; standard vector 123456789 gives 4B37.

## Code path (V1.6)

- Receive: `0x00481030` → `0x0049CA30` (`uartPackDataHandle`) → `0x0049C830` (frame parser), call at `0x0049CC8D`.
- Transmit: wrapper `0x004819C0` → `0x0049C5C0` (frame builder).
- Common TX send helper: `FUN_00492ab0` (25 callers). Checks `+0x0C`, inserts CMD 0x10 wrapper when active, then calls frame builder.
- Numeric readers: 16-bit big-endian at `0x0049D3B0`; 32-bit big-endian at `0x0049D450`.

## Component ownership

The meta-object string table near `0x00F24080` names the helper object `uartPackData` and lists:

0. `sendDataToESC`
1. `uartPackDataFromESC`
2. `uartPackDataHandle`
3. `uartPackDataTimerSl`

The handler dispatch is `0x0049CA30`; it calls `0x0049C830`. The framing/parser helper is the `uartPackData` object. Keep `UartComm` distinct.

## Whole-product workstream estimate

| Work package | Weight (points) | Progress | Weighted (points) |
|---|---:|---:|---:|
| Binary inventory and static application mapping | 10 | 100 | 10.0 |
| FTESC UART framing, parser and stream handling | 10 | 100 | 10.0 |
| V1.7 request/response command coverage | 20 | 87 | 17.4 |
| Setup metadata, ValueSeque ordering and typed serializer | 10 | 95 | 9.5 |
| Direct CAN and V1.7 gateway/slave routing | 10 | 60 | 6.0 |
| Firmware authorization, transfer and bootloader flow | 10 | 55 | 5.5 |
| Separate VESC/FSESC profile and source comparison | 10 | 85 | 8.5 |
| Open-source desktop UI and real serial/BLE integration | 15 | 20 | 3.0 |
| Reproducible extraction, tests and CI | 10 | 100 | 10.0 |
| Hardware validation | 5 | 0 | 0.0 |
| **Total** | **110** | | **79.9 / 110 = 72.64% (72.6%)** |

Reconciliation note (2026-11-25): an earlier version of this table showed CAN/gateway at 65% and CI at 95% on a 100-point scale (the two changes offset, giving the same total). STATUS.md is the authoritative scoring source (weights sum to 110), so this table mirrors it. No extra CAN progress is credited until the emitted V1.7 CAN-forward bytes are verified.

## Next tasks

1. Load V1.7 binary into REA (download from Nextcloud to CT107 `/data/analysis/pe/v1.7_20261029/`) and search for `TopFlowSetupValueTable` string.
2. Resolve the V1.7 CAN wrapper insertion path (may be in a Qt slot not in the normal transmit chain).
3. Complete firmware image/container, retries, bootloader transitions and recovery state machine.
4. Implement the desktop UI shell and safe read-only serial session/telemetry workflow.
5. Recover FTESC BLE UUIDs, MTU/chunk and write/notify behaviour; then implement transport.
6. Add authorized passive capture replay and controlled bench validation before enabling any writes or firmware operations.

## Tooling and constraints

- Ghidra 12.2 available in REA; the current live target is V1.7 at /data/analysis/pe/v1.7_20261029/. The V1.6 2026-09-12 target was normally closed after exporting its Evidence bundle; its owned checkpoint is retained.
- V1.7 is staged and opened in REA at `/data/analysis/pe/v1.7_20261029/Flipsky_ESC_Tool_V1.7_20261029.exe`; size 50,611,200 and SHA-256 matches the inventory. Original `/data/samples/Flipsky_ESC_Tool_V1.7_20261029.exe` was preserved. Nextcloud source share: `https://nextcloud.est1.dev/s/TijZe4XHNjkw4FQ`.
- Original EXE remains on REA (50,611,200 bytes); its identity is recorded in `docs/ARTIFACT_INVENTORY.md`.
- All 19 unique XML resources and derived catalogs are published as gzip/base64; restore with `python scripts/restore_payloads.py --root .`.
- No firmware image or passive serial capture was obtained in this session.
- No packets were sent to physical ESC hardware.
- REA regex risk: `case_sensitive: false` on `rea-search_strings` for large PE causes Ghidra timeout. Always use `case_sensitive: true` and `mode: "literal"` on large PEs.
