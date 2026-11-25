# Analysis checkpoint — 2026-11-25

**Repository:** `Estcool9/flipsky-esc-protocol-analysis`  
**Overall project progress: 72.6% unrounded (73% rounded)** (weighted full open-source desktop replacement; 79.9 / 110 points; scoring model and authoritative weights in [STATUS.md](STATUS.md)).  
**Executable SHA-256 (V1.7):** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Executable SHA-256 (V1.6 2026-09-12 active):** `051d57a776782ae8daaeaa45179f9b568f7e89b4a78ab8dd8e558ecd3e53b968`

This is the authoritative hand-off note. Update it at every significant milestone.

## Latest confirmed milestone: V1.6 CMD 0x10 CAN wrapper confirmed in TX helper (2026-11-25)

- REA/Ghidra 12.2 decompiled `FUN_00492ab0` (V1.6 2026-09-12 common TX send helper).
- **CONFIRMED:** UartComm offset `+0x0C` = CAN-forward enable (byte). UartComm offset `+0x10` = CAN slave target ID (byte).
- **CONFIRMED:** When canForward active, V1.6 TX helper calls UUID helper `PTR_FUN_00c53314` twice — first with the slave ID (from `+0x10`), then with the value `0x10` (CMD byte). This is the inline CAN-forward wrapper insertion.
- **CONFIRMED ARCHITECTURAL DIFFERENCE:** V1.6 inserts CMD 0x10 inline in its TX helper. V1.7's equivalent (`FUN_00495910`) does NOT insert any CAN envelope in the normal transmit chain.
- 229 evidence records, 148 MB retained in Ghidra checkpoint.
- Evidence IDs: `ev_9407521b152a83ed0c9eb9e261cdfff4faea8a455c2c11d9a5c1fbe5020ed0ca` (analyze_function summary), pseudocode in `ev_8bdacaa9c6eb4c4e31b3c9da89f2389f5dd77756f2f86b4b36a1d7f7cd97ca07` context.
- Commit: `7464055983d5de47cf25ea54f1e884b118c0e2fe`

## Previous milestone: 177 passing tests, V1.6/V1.7 cross-build comparison

- Fresh REA clone: 177 tests passed, zero failures; compileall passed. CI run #301.
- Flipsky VESC V1.0 UART/CAN codecs added and tested.
- Full bounded XML scan found 19 unique ValueSetup resources; catalog now has 1,152 rows, 286 distinct XML IDs, 1,135 ValueSeque entries and 17 omissions.
- The normal V1.7 UartComm transmit chain has been traced end-to-end; it does not prepend the public V1.6 CMD 0x10 wrapper at the standard insertion points examined.
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

Reconciliation note (2026-11-25): an earlier version of this table showed CAN/gateway at 65% and CI at 95% on a 100-point scale (the two changes offset, giving the same total). [STATUS.md](STATUS.md) is the authoritative scoring source (weights sum to 110), so this table now mirrors it. The V1.6 CMD 0x10 finding is verified evidence, but it concerns the V1.6 build; V1.7 gateway/slave routing is still unresolved, so no extra CAN progress is credited until the V1.7 path is located.

## Next tasks

1. Load V1.7 binary into REA (download from Nextcloud to CT107 `/data/analysis/pe/v1.7_20261029/`) and search for `TopFlowSetupValueTable` string.
2. Resolve the V1.7 CAN wrapper insertion path (may be in a Qt slot not in the normal transmit chain).
3. Complete firmware image/container, retries, bootloader transitions and recovery state machine.
4. Implement the desktop UI shell and safe read-only serial session/telemetry workflow.
5. Recover FTESC BLE UUIDs, MTU/chunk and write/notify behaviour; then implement transport.
6. Add authorized passive capture replay and controlled bench validation before enabling any writes or firmware operations.

## Tooling and constraints

- Ghidra 12.2 available in REA; checkpoint active on V1.6 2026-09-12.
- V1.7 binary NOT yet loaded in REA (path `/data/analysis/pe/v1.7_20261029/` does not exist on CT107 yet). Nextcloud source: `https://nextcloud.est1.dev/s/TijZe4XHNjkw4FQ` (public link, view only).
- Original EXE remains on REA (50,611,200 bytes); its identity is recorded in `docs/ARTIFACT_INVENTORY.md`.
- All 19 unique XML resources and derived catalogs are published as gzip/base64; restore with `python scripts/restore_payloads.py --root .`.
- No firmware image or passive serial capture was obtained in this session.
- No packets were sent to physical ESC hardware.
- REA regex risk: `case_sensitive: false` on `rea-search_strings` for large PE causes Ghidra timeout. Always use `case_sensitive: true` and `mode: "literal"` on large PEs.
- Session access note (2026-11-25): shell/git work runs on the remote open-terminal (git installed there, no push credentials); commits are published with the McpHub GitHub `push_files` tool and verified by `git fetch` plus diff.
