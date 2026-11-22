# V1.7 BLE transport — shared parser and transmit chunk queue

**Reference date:** 2026-11-22  
**Artifact:** `Flipsky_ESC_Tool_V1.7_20261029.exe`  
**SHA-256:** `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`  
**Analysis:** REA 6.10.1 / Ghidra 12.2, PE32 x86  
**Scope:** static analysis only; no BLE device scan, connection, characteristic read/write, pairing or ESC command.

## Findings established

### Receive path: BLE enters the common framed-stream parser

The recovered Qt meta-call table maps the method named `bleDataRx` (method index 24 in the `FtescLowLevelFace` table) to native function `FUN_004828D0` at `0x004828D0`. Its complete decompilation shows that it takes the incoming `QByteArray` and calls `FUN_0049CA30` directly.

`FUN_0049CA30` is the incremental receive-buffer handler already mapped on the UART path. It feeds the AA/BB frame parser, retains incomplete candidates, supports concatenated frames and advances by one byte after an invalid candidate. Consequently, the V1.7 BLE receive callback reuses the same application-level AA/BB stream parser as UART. This is a direct static call-path observation, not a runtime capture.

### Transmit path: shared framed byte array and fixed 20-byte chunking

The shared lower-level send slot `FUN_00481850` (`0x00481850`) checks the BLE-connected state via `FUN_00401680`. When that state is true, it passes the same input `QByteArray` to `FUN_004050C0`. The surrounding transport-pipeline analysis identifies this shared send input as the framed packet emitted by the `uartPackData` layer.

`FUN_004050C0` iterates through the byte array in increments of `0x14` (20 decimal), constructing successive slices at offsets 0, 20, 40, and so on. It then invokes `FUN_00404E80` when the asynchronous queue is idle. The queue-pump function removes the next queued item, marks the transport busy, and constructs a completion callback that continues queue processing.

This establishes a static 20-byte application-level chunk stride and the shared outbound path. It does **not** establish that 20 bytes is a negotiated ATT MTU, an MTU-derived maximum payload, or the exact value submitted to the BLE stack at the lowest API boundary.

### Qt API evidence and limitations

The executable contains the mangled symbol string for `QLowEnergyService::writeCharacteristic(const QLowEnergyCharacteristic&, const QByteArray&, QLowEnergyService::WriteMode)`. However, the PE import descriptor at RVA `0xB9F000` could not be mapped unambiguously by the import inspector, and the protected/indirect dispatch path does not yet give a proven call-site-to-import edge. The symbol string alone is not sufficient to claim the exact write mode or call target.

## Evidence references

- `FUN_004828D0` analysis: `ev_0b96fa9d9daca6528da735c37d6a4fa85f5cede2be619f08d07cfa494e6da22b`
- `FUN_00481850` analysis: `ev_0863f4b9c9cbaa26854a9389f1d2d4f01af0cd11963bc5043a68b1b315c57def`
- `FUN_00404E80` analysis: `ev_26f4ad2230070fd6a96d3322a1e2c2fb5985d8d1c5709c228825789f669a36d1`
- `FUN_004050C0` decompilation summary: `ev_60b7bb46204767a08aee7256e4a4233174fa9e248e37f18ba3545bcc7de8fce0`
- `writeCharacteristic` symbol-string search: `ev_14bbb5c07a7e3c24e7f64e40abe36d4c543e0a8939b2ffd966061e649720f728`
- PE import inspection limitation: `ev_64791b4adf0065ca2f544059fa314ba5862bbfd4c675fb96244f53cd84e50c5e`
- Original GATT UUID/lifecycle and CCCD observations remain listed in [BLE_GATT_V1_7_REVERSE_ENGINEERED.md](BLE_GATT_V1_7_REVERSE_ENGINEERED.md).
- Shared UART framing and stream parser context: [TRANSPORT_PIPELINE.md](TRANSPORT_PIPELINE.md).

## Still unknown

1. Exact call target and arguments at the final Qt GATT write boundary.
2. Write-with-response versus write-without-response mode.
3. Exact CCCD `0x2902` value and notification sequencing.
4. Negotiated ATT MTU, any negotiation policy, and whether 20-byte chunking is an invariant or a fallback.
5. BLE-side retry, failure, timeout and reconnect behavior.
6. Independent passive BLE capture and model/firmware applicability.

## Progress accounting

The static BLE transport sub-workstream rises from 60% to **75%**: the receive-to-common-parser route and the transmit queue's 20-byte segmentation are now statically established. The complete-product weighted score stays at **72.2%** (79.4 / 110 points). No live transport or desktop functionality has been added, and hardware validation remains 0%.

## Acquisition and environment note

Four V1.6 source artifacts were authorized for temporary Nextcloud checkout, but they could not yet be staged on the REA host. The only registered Gateway target is a different LXC host and it cannot reach the REA MCP endpoint or workspace. No Nextcloud source file was modified. REA's configured Apktool and ADB launchers were verified; no Android device was contacted. The caller-supplied JADX MCP JAR path remains to be verified.
