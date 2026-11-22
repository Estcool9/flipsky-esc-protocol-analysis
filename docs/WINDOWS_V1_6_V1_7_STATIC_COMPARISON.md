# Windows V1.6 builds vs V1.7 — static marker and dispatch comparison

**Reference date:** 2026-11-22  
**Scope:** static PE32 inspection only; no executable was run. Ghidra 12.2 was used through REA 6.10.1, with Rizin 0.9.1 for independent reference/disassembly cross-checks.

## Artifacts and identities

| Build | SHA-256 | REA evidence |
|---|---|---|
| V1.6 2025-10-14 | `1dc93bd84f4dab1a3ee7b3946fa0522c78fc870227523d8d5fe6d6e187ea2b07` | `ev_11a0a4201fc8bea258cdf0bcad2f673335fff8791974ba55b2015ee4bd064560` |
| V1.6 2026-08-06 | `94cfd851a5ccce38b8c42c9f154128e10fa2906ce9efc9cddfa39c4a00361a03` | `ev_9fd2415bc833f0f477996603edce21c999c80aaa528fb8fa74252e7aef7c20f5` |
| V1.6 2026-09-12 | `051d57a776782ae8daaeaa45179f9b568f7e89b4a78ab8dd8e558ecd3e53b968` | `ev_b7dc4354f176f2ada1f33bbab669f691357c0a18766d9fff96493ed685d24ca3` |
| V1.7 2026-10-29 | `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38` | `ev_516d45d45d3512ce3738c2818929fdd005070a58b5be317fc4e752c347c85a3a` |

All three Windows V1.6 files were already staged under `/data/analysis/pe/` on CT107; V1.7 is under `/data/samples/`. Nextcloud originals were not modified.

## Stable marker set across Windows builds

The same targeted Ghidra string search found the following in all three V1.6 builds and V1.7:

- BLE UART discovery marker: `BLE UART service found!`
- Firmware/bootloader UI markers: `Enter bootloader`, `:/icon/bootloader.png`, update-step instructions and master/slave warning text.
- Firmware size guard text: `Firmware is too large, cannot exceed 150Kbyte`.
- Qt meta-object/API strings: `ftescEraseFirmware`, `ftescWriteFirmware`, `ftescJPMBootMode`, `ftescIdentifyMotorOverCan`, `setCanForwardSendFlag`, `uartPackData`, `uartPackDataFromESC`, `uartPackDataHandle`, `uartPackDataTimerSl`.
- Qt BLE API import string: `QLowEnergyService::writeCharacteristic(..., WriteMode)`.

Representative addresses:

| Marker | V1.6 2025-10-14 | V1.6 2026-08-06 | V1.6 2026-09-12 | V1.7 2026-10-29 |
|---|---:|---:|---:|---:|
| `ftescEraseFirmware` | `0xb483ca` | `0xba592a` | `0xc1f1ea` | `0xf23c41` |
| `ftescWriteFirmware` | `0xb483e4` | `0xba5944` | `0xc1f204` | `0xf23c5b` |
| `ftescJPMBootMode` | `0xb483f7` | `0xba5957` | `0xc1f217` | `0xf23c6e` |
| `ftescIdentifyMotorOverCan` | `0xb485dc` | `0xba5b3c` | `0xc1f3fc` | `0xf23ed1` |
| `setCanForwardSendFlag` | `0xb48662` | `0xba5bc2` | `0xc1f482` | `0xf23f57` |
| `uartPackData` | `0xb48810` | `0xba5d70` | `0xc1f630` | `0xf24110` |
| `uartPackDataFromESC` | `0xb4883d` | `0xba5d9d` | `0xc1f65d` | `0xf2413d` |
| `uartPackDataHandle` | `0xb48858` | `0xba5db8` | `0xc1f678` | `0xf24158` |
| `uartPackDataTimerSl` | `0xb4886b` | `0xba5dcb` | `0xc1f68b` | `0xf2416b` |
| `writeCharacteristic` import | `0xb7d13a` | `0xbda7c2` | `0xc547c2` | `0xf5a1d2` |

The repeated method strings and import names are static metadata. They do not by themselves prove that the same methods execute, that the BLE write mode is the same, or that the protocol behavior is identical.

## V1.7 bootloader state markers

The V1.7 targeted search additionally returned these explicit UI/status strings:

- `isBootloader:`
- `Switch to Firmware Update: bootloader target selected:`
- `Warning: Bootloader CAN ID`

These are useful new search anchors for the V1.7 state-selection path. Treat them as UI/state labels only until their caller paths and state transitions are decompiled. Earlier V1.6 builds already contain the `Bootloader` label and `Enter bootloader` action text.

## Cross-version dispatch stub around uartPackData

Rizin found a code reference to the `uartPackData` string in each of the latest V1.6/V1.7 PE builds:

| Build | Rizin stub | Loaded string address | Called thunk | Final indirect jump |
|---|---:|---:|---:|---:|
| V1.6 2026-09-12 | `0x004b74bc` | `0x00c1f630` | `0x004bc0dc` | `[0x00c53474]` |
| V1.7 2026-10-29 | `0x004bdd7c` | `0x00f24110` | `0x004c299c` | `[0x00f59320]` |

The stub shapes are similar: load the Qt string address, prepare arguments, call a short indirect thunk, test the result, then jump through a global pointer. Ghidra recognizes the called thunks:

- V1.6 `FUN_004bc0dc`: six-byte `JMP dword ptr [0x00c53180]`; evidence `ev_2c71b965f6ceb1c828c445a60198293a7dc7697873f3c50541793632064cf231`.
- V1.7 `FUN_004c299c`: six-byte `JMP dword ptr [0x00f59fa8]`; evidence `ev_209f39c2afcd5add8214d8ed83b234e30c5f3cfe9aa58d7f0dc6f7f8992d9b69`.

Ghidra reports 46 incoming references for each generic thunk, but its caller inventory is explicitly partial for computed/indirect calls. The string-loading stubs themselves were not recognized as function entries by Ghidra at the supplied addresses. This is evidence of a recurring Qt dispatch pattern, not a recovered UART codec or a proof that the underlying methods are identical.

Rizin emitted warnings that some large PE string-search regions exceeded its configured maximum and were skipped. Empty Rizin xref output for other strings is therefore not proof that no references exist.

## Android V1.6 cross-check

The existing Android V1.6 native report independently establishes the app-selected BLE write mode (`WriteWithoutResponse`), CCCD notifications value `01 00`, 20-byte application chunks and routing into the shared FTESC parser on ARM64 and ARMv7. Windows V1.6/V1.7 marker presence and Qt API imports are consistent with a related BLE UART path, but the Windows protected write call is not yet proven equivalent to the Android call.

See:
- [ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md](ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md)
- [BLE_GATT_V1_7_REVERSE_ENGINEERED.md](BLE_GATT_V1_7_REVERSE_ENGINEERED.md)
- [V1_7_OUTBOUND_TRANSMIT_CHAIN.md](V1_7_OUTBOUND_TRANSMIT_CHAIN.md)

## Conclusions and unresolved work

1. The three Windows V1.6 builds and V1.7 share the same high-level FTESC, BLE UART, CAN and firmware-update marker families.
2. The Qt `uartPackData` dispatch stub pattern is structurally similar between the latest V1.6 and V1.7, but the actual function bodies behind the indirect dispatch remain unresolved.
3. V1.7 exposes additional bootloader-target state labels in the targeted string search; their functional meaning is not yet established.
4. A full function-level PE diff is still open. PE import descriptors are partially obscured by unusual/packed sections, and Ghidra has not yet resolved the dynamic dispatch targets.
5. No codec or protocol implementation was changed from these marker-only results; no new tests were appropriate until a byte-level behavior is recovered.
6. The project-wide weighted progress remains 72.6% (79.9/110). This investigation improves artifact coverage, but does not complete a weighted functional milestone: no desktop integration, live transport, firmware recovery or hardware validation was added.

## Safety

All operations were static analysis of immutable binaries. No Windows/Android application was launched, no ESC was connected, no UART/CAN/BLE command was sent and no firmware was flashed. Cryptographic secrets are not included.


## Function-level UART follow-on

The targeted marker pass was followed by static decompilation of the V1.6 UART frame builder, candidate parser and stream handler, including their Qt wrappers. See [WINDOWS_V1_6_UART_FRAME_PARSER.md](WINDOWS_V1_6_UART_FRAME_PARSER.md) for exact function addresses and behavior. This closes the main V1.6 UART framing/parser role comparison, but not the complete PE function diff or protected BLE write path.
