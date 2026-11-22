# Technical roadmap — open-source Flipsky client

**Reference date:** 2026-11-22  
**Overall project progress: 72.6% unrounded (73% rounded)** (weighted whole-product estimate; scoring table in [STATUS.md](STATUS.md); 79.9 / 110 = 72.64%).

## Phase A — Artifact intake and static reverse engineering

- [x] Inventory and SHA-256 verify the V1.7 PE32 executable.
- [x] Identify native x86 / Qt 5 / C++ / QML architecture and transport modules.
- [x] Inventory Ghidra 12.2 and Rizin 0.9.1 tools on REA.
- [x] Map key Qt meta-objects, signals/slots and static meta-call indexes.
- [x] Map the main UART receive and transmit paths.
- [x] Trace the normal UartComm transmit path end-to-end and document the scoped CMD 0x10 negative finding.
- [x] Add a generic bounded Zlib/XML resource scanner and regression tests.
- [ ] Finish QML resource tree and all remaining UI/property dynamic behaviour.
- [x] Inventory the complete Nextcloud Software tree and identify three dated V1.6 Windows builds plus Android BLE and macOS V1.6 packages.
- [x] Stage the three V1.6 Windows EXEs and BLE APK; verify SHA-256 before/after transfer.
- [x] Perform first-pass PE32 identity and BLE/FTESC marker comparison across all V1.6 EXEs and V1.7.
- [ ] Complete function-level V1.6-to-V1.7 comparison; import tables are partial due Enigma/virtual-span mapping.

## Phase B — FTESC protocol reconstruction

- [x] Recover AA/BB UART framing, payload length semantics, CRC-16/MODBUS and DD terminator.
- [x] Implement frame decoding, encoder and incremental receive stream/resynchronization tests.
- [x] Map the majority of V1.7 request builders and response dispatch/ACK signals.
- [x] Implement offline request/response codecs for discovered control, identity, telemetry, setup and string operations.
- [x] Recover typed setup value serialization and response decoding for observed types.
- [x] Extract 19 unique ValueSetup resources and generate reproducible catalogs and ValueSeque order files.
- [ ] Recover TopFlow ValueSetup XML and exact model/SKU mapping. The FTESC Android XML parser now proves ValueSeque is copied into the native wire-order list; do not substitute FTESC tables for TopFlow.
- [ ] Validate all V1.7 command response layouts against passive captures.
- [ ] Resolve remaining V1.7 request-schema and unknown command cases.

## Phase C — CAN, BLE and gateway behaviour

- [x] Implement and test FTESC direct CAN V1.4 ID, CRC and periodic telemetry decoders.
- [x] Document the V1.4 PDF ambiguities around brake IDs, status cadence and 0x0D parser widths.
- [x] Map the V1.7 CAN target UI state, ID discovery and request call sites.
- [x] Trace the standard UartComm path: it does not prepend the public V1.6 CMD 0x10 wrapper at the examined insertion points.
- [ ] Determine how the V1.7 selected CAN ID reaches the external FTESC Gateway (side channel or alternate path).
- [ ] Recover slave response correlation and error/time-out mapping.
- [x] Recover the V1.7 BLE UART service, TX and RX UUIDs from the native `BleUart` constructor.
- [x] Map BLE controller/service signal registration, service discovery, characteristic-change callback and missing-characteristic paths.
- [x] Confirm constructor connection from BleUart::bleDataRx(QByteArray) to app-level dataRx(QByteArray) receiver.
- [x] Locate the CCCD descriptor UUID `0x2902` lookup in the service-state handler.
- [ ] Finish the native `writeData` / `sendNextPacket` → `QLowEnergyService::writeCharacteristic` chain and identify response/no-response mode.
- [ ] Confirm the exact CCCD value, negotiated MTU, packet chunk size and receive reassembly from native code and passive captures.
- [ ] Implement FTESC BLE transport only after the wire path is established.

## Phase D — VESC/FSESC parallel protocol profile

- [x] Read all four user-supplied Flipsky VESC UART/CAN V1.0 PDFs (English and Chinese).
- [x] Cross-check UART framing/CRC/command IDs against pinned VESC Tool source.
- [x] Cross-check direct CAN command IDs and identifier composition against pinned VESC firmware.
- [x] Add `scripts/vesc_uart.py` and tests for 02/03/04 framing and VESC CRC.
- [x] Add `scripts/vesc_can.py` and tests for VESC target/command ID layout and basic scaling.
- [x] Add `scripts/vesc_stream.py` for incremental VESC UART decoding, fragmentation, concatenation and resynchronization.
- [x] Add explicit adapter-family matrix: FTESC NON-VESC vs FSESC VESC.
- [ ] Expand VESC GET_VALUES response decoder and firmware-version compatibility profiles.
- [ ] Run CI against the newly added 7 VESC stream tests (not yet verified in this checkpoint).
- [ ] Add version negotiation and explicit user-selected protocol-profile UX; never infer protocol from brand alone.
- [ ] Decide whether the open-source app will implement only the documented Flipsky V3.00 profile or multiple VESC firmware generations.

## Phase E — Firmware update and security state machine

- [x] Recover V1.7 UUID response path and TEA challenge/request usage.
- [x] Recover the 240-byte block payload builder and XOR transform.
- [x] Implement offline firmware authorization/block helpers.
- [ ] Complete all bootloader entry, erase, write, ACK, retry and timeout transitions.
- [ ] Identify exact firmware image container/metadata and checksum/signature.
- [ ] Complete static analysis of device-side firmware challenge semantics, key provisioning, full write/ACK frame fields, integrity checks and recovery; keep TEA/XOR secrets out of public artifacts.
- [ ] Validate against an authorized firmware image in a safe, isolated test plan; do not flash during protocol discovery.
- [ ] Add safe recovery/abort states to the replacement application before any firmware UI is enabled.

## Phase F — Open-source application implementation

- [x] Define a separate protocol-adapter boundary and document family selection rules.
- [ ] Build desktop app shell and project structure (Qt/PySide or another explicitly chosen stack).
- [ ] Implement serial-port discovery and connection state as a read-only first milestone.
- [ ] Implement passive receive/telemetry display with raw-frame logging and replay.
- [ ] Implement configuration views backed by FTESC ValueSetup metadata and explicit ValueSeque ordering.
- [ ] Implement CAN topology / slave list after gateway routing is resolved.
- [ ] Implement BLE only after write mode, CCCD value, MTU/chunking and notification/reassembly behavior are verified.
- [ ] Implement firmware update UI only after the full state machine and recovery path are validated.
- [ ] Match the essential Flipsky ESC Tool V1.7 functionality without copying proprietary UI assets or source.

## Phase G — Reproducibility and validation

- [x] Use content hashes and manifests for binary/resource identity.
- [x] Restore large data artifacts from gzip/Base64 payloads.
- [x] Regenerate parameter and profile catalogs deterministically.
- [x] Add GitHub Actions for artifact restore, regeneration compare, unit tests and compileall.
- [x] Maintain tests for FTESC framing, stream recovery, requests, responses, setup serializer, firmware blocks, direct CAN, generic XML scanning and VESC UART/CAN.
- [x] Fresh REA clone test run: **148 passed, 0 failed** (earlier baseline).
- [x] GitHub Actions run #156: 159 passed, 0 failed, 25/25 research payloads restored, parameter catalog/profile exports regenerated deterministically, and Python compileall passed.
- [x] GitHub Actions run #199 after native ValueSetup boundary tests: 162 passed, 0 failed; catalog/profile regeneration and Python compileall passed. Documentation follow-on run #200 also green.
- [ ] Add protocol capture replay fixtures from authorized passive traces.
- [ ] Build a benign fake-ESC simulator for read-only responses.
- [ ] Perform a staged bench test with a known ESC model, firmware and mechanically safe configuration.
- [ ] Document hardware validation for each model/version; do not extrapolate between SKUs.

## Future generic reverse-engineering workflow

- [x] Add [RE_WORKFLOW.md](RE_WORKFLOW.md) covering intake, triage, Ghidra/Rizin, Qt metadata, bounded extraction, evidence discipline, tests and GitHub hygiene.
- [x] Add a generic compressed XML scanner for future Qt/resource-heavy programs.
- [ ] Add a reusable blank project-template generator for artifact inventory, evidence ledger and checkpoint files.
- [x] Add [NEXTCLOUD_SOFTWARE_INVENTORY.md](NEXTCLOUD_SOFTWARE_INVENTORY.md) and [TOOLING_AUDIT.md](TOOLING_AUDIT.md) for source/tool tracking.

## Current blockers

1. **TopFlow:** the V1.7 executable references `:/ftesc/1.7/TopFlowSetupValueTable.xml`; the complete scan found more ValueSetup profiles but not the TopFlow table itself.
2. **CAN target path:** the UI stores the flag and target ID, but the standard send path inspected does not add the V1.6 `0x10` envelope. Need an authorized Gateway document, alternate path or passive trace.
3. **Firmware update:** the authorization and block codec are partially recovered; image container/recovery state is incomplete.
4. **Desktop application:** no serial/BLE UI or device integration has been implemented yet.
5. **BLE:** service/TX/RX UUIDs and controller/service callbacks are statically mapped; write mode, CCCD value, negotiated ATT MTU, retries and live behavior remain unknown; the static application-level chunk stride is 20 bytes.
6. **Hardware:** no live controller validation has occurred.
7. **V1.6 binary comparison / Android BLE cross-check:** all four artifacts are staged and hash-verified; Android QML/FTESC/firmware resource collections are extracted; both Android ABIs prove 20-byte chunking, WriteWithoutResponse and shared parser routing. Windows marker-level comparison is complete, but function-level PE diffs and the protected Windows write edge remain open.

## Safety boundary

All current protocol encoders and decoders are offline. No UART, CAN or BLE interface has been opened. No ESC control command or firmware update was transmitted.


## 2026-11-22 — BLE shared parser / transmit chunker static closure

- [x] Confirmed the native `bleDataRx` callback calls the common AA/BB receive stream handler `FUN_0049CA30`.
- [x] Confirmed the shared lower-level sender routes the same framed byte array into the BLE branch when BLE is connected.
- [x] Recovered the BLE branch's fixed 20-byte application chunk stride and asynchronous queue pump.
- [ ] Resolve the final `writeCharacteristic` call, exact write mode, CCCD value, negotiated ATT MTU and passive trace.
- Static BLE workstream: 60% → 80%; whole-product score remains 72.6%.


## 2026-11-22 — CI closure and VESC stream resynchronization

- [x] Fix the ambiguous-prefix case where a corrupted frame terminator `0x03` can be parsed as a medium-frame start and mask the following valid frame.
- [x] Validate later candidate frames only after full declared length, CRC and end-marker checks; retain incomplete input when no later valid candidate exists.
- [x] Pass GitHub Actions run #156: 159 unit tests, deterministic source restores/catalog/profile generation and compileall.
- [x] Raise reproducibility/tests/CI work package from 95% to 100%.
- New weighted progress: **79.9 / 110 = 72.64% ≈ 72.6% (73% rounded)**.


### BLE final-write narrowing — 2026-11-22

- [x] Identify an indirect call candidate at `0x00404FEC` with arguments shaped like `QLowEnergyService::writeCharacteristic(characteristic, QByteArray, WriteMode)`.
- [ ] Prove the computed target `0x00B5A1D0` in the Enigma-protected region maps to the Qt symbol, and decode the observed third argument `1` to its actual WriteMode.
- Static BLE workstream: 75% → 80%; this does not increase the whole-product score because no live transport or desktop feature was implemented.


## 2026-11-22 — V1.6 Android native BLE and Windows cross-version pass

- [x] Stage V1.6 Android BLE APK and three V1.6 Windows EXEs through Gateway SSH into CT 107; verify identical pre-/post-transfer SHA-256; leave Nextcloud originals untouched.
- [x] Inventory APK (149 occurrences / 148 nodes, no integrity contradictions) and extract Android ARM64/ARMv7 Flipsky native and Qt5Bluetooth libraries.
- [x] Inspect Qt Android Bluetooth Java bridge: characteristic write-type mapping, async I/O queue, 3-second timeout, MTU 512 request with 23-byte fallback, and CCCD notification bit handling.
- [x] Recover Flipsky ARM64 symbol map for BleUart, FtescLowLevelFace, UartComm, frameFwUpdate, ftescValueTable and firmware/CAN functions.
- [x] Compare targeted PE32 identity/marker strings across V1.6 builds and V1.7.
- [ ] Decompile application-level Android BLE method bodies and compare ARM64/ARMv7 behavior.
- [x] Decode Android application-owned Qt QML/FTESC/firmware/icon RCC resources; recover screens, setup tables and firmware UI flow.
- [x] Recover app-selected BLE write mode, CCCD notifications and shared parser on both Android ABIs.
- [ ] Resolve the exact Qt signal/slot connection edge and all remaining QML/native UI bindings.
- [ ] Complete function-level Windows V1.6/V1.7 diffs; PE import descriptors are currently unreadable in the import workflow.
- BLE static sub-workstream: 80% → 95% (Android V1.6 ARM64/ARMv7 exact write mode and shared parser); V1.6 EXE marker comparison: 0% → 25%; whole-product score remains **72.6%**.
- Detailed reports: [ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md](ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md), [BLE_TRANSPORT_SHARED_PARSER_AND_CHUNKING.md](BLE_TRANSPORT_SHARED_PARSER_AND_CHUNKING.md).


## 2026-11-22 — Android V1.6 exact BLE mode and CCCD

- [x] Recover 20-byte chunk stride in `BleUart::writeData`.
- [x] Recover direct `QLowEnergyService::writeCharacteristic` call in `BleUart::sendNextPacket`; C++ `WriteMode=1` maps to Qt 5.15 `WriteWithoutResponse`.
- [x] Recover literal CCCD payload `0100` written to descriptor UUID `0x2902`; it selects notifications, not indications.
- [x] Resolve BLE receive event to `BleUart::dataRx` signal and the `FtescLowLevelFace::bleDataRx` slot body to `uartPackData::uartPackDataHandle`, the shared FTESC stream parser.
- [ ] Resolve the exact QObject signal/slot connect call site.
- [ ] Determine negotiated ATT MTU and runtime behavior from an authorized passive capture/device; no runtime BLE operation has been performed.
- [ ] Confirm whether Windows V1.7's protected indirect target is the same Qt write mode. Android V1.6 strongly corroborates but does not prove the protected Windows edge.
- Android/BLE static sub-workstream: 85% → 95% after ARMv7 independently confirms the 20-byte chunk stride, direct WriteWithoutResponse call and common FTESC parser route. Whole-project score remains 72.6%.


## 2026-11-22 — Android ARMv7 BLE path matches ARM64

- [x] Confirm ARMv7 `BleUart::writeData` sets 20-byte (`0x14`) slices.
- [x] Confirm ARMv7 `BleUart::sendNextPacket` directly calls Qt `writeCharacteristic` with C++ `WriteMode=1` (`WriteWithoutResponse`).
- [x] Confirm ARMv7 CCCD method uses descriptor UUID `0x2902`, `QByteArray::fromHex` and `writeDescriptor`; a single `0100` string literal is present, but a direct cross-reference was not recovered.
- [x] Confirm ARMv7 `FtescLowLevelFace::bleDataRx` invokes `uartPackData::uartPackDataHandle` after copying the input QByteArray.
- [ ] Resolve Qt constructor signal/slot connection, negotiated MTU and runtime behavior.
- Android/BLE static sub-workstream: 90% → 95%; whole-product score remains 72.6%.


## 2026-11-22 — V1.6 Android application resources and UI flow

- [x] Parse the four native Qt RCC version-3 tables registered by `qInitResources_qml`, `qInitResources_ftesc`, `qInitResources_ftescFw` and `qInitResources_ftescIcon`.
- [x] Extract 28 QML files, 24 XML resources, 31 firmware resource entries and 18 icon files (101 files total, zero extraction errors).
- [x] Map the QML app objects: UartComm, motor/signal/firmware ValueSetups, BleUart, startup scan/reconnect, ESC ID → motor setup → signal setup read order and CAN master/slave selection.
- [x] Enumerate FTESC ControlSetup ValueSeque sizes across embedded versions 1.0–1.6 (24, 24, 26, 36, 46, 67, 69).
- [x] Confirm V1.6 official motor profile 94 metadata Values / 93 ValueSeque entries, with motor_rated_current omitted from serialization.
- [x] Deduplicate firmware resources by SHA-256: 31 entries, 17 unique files, 165,880 bytes each; vector-table shape consistent with Cortex-M raw images.
- [x] Recover firmware QML result codes, master-only restriction, bootloader warning, custom BIN path and native firmware-list/data API names.
- [ ] Resolve all remaining QML/native method bindings, full firmware image/model mapping and cryptographic/integrity scheme.
- Android application UI/resource static sub-workstream: 0% → 80%. Whole-product weighted score remains **72.6%** (79.9 / 110).
- Detailed report: [ANDROID_V1_6_QML_VALUESETUPS_AND_FIRMWARE_RESOURCES.md](ANDROID_V1_6_QML_VALUESETUPS_AND_FIRMWARE_RESOURCES.md).


## 2026-11-22 — CI confirmation after Android resource documentation

- [x] GitHub Actions run #195: 159 passed, 0 failed; profile/catalog regeneration and compileall passed.
- [x] Corrected README/STATUS/ROADMAP to distinguish the V1.6 Android embedded firmware images from the still-unresolved V1.7 firmware update image/container.
- Overall weighted project score remains 72.6%.


## 2026-11-22 — Native ValueSetup ordering and firmware state-machine evidence

- [x] Prove configValueStreamXml reads ValueSeque/seque into native QList at ValueSetups+0x28; Clustering goes to a separate list.
- [x] Prove valueArralize and valueDeArralize use that same list for ordered serialization and marker-validated response parsing.
- [x] Map all nine native valueTET codecs, big-endian integer/binary32 encodings and ties-away-from-zero scaled rounding.
- [x] Add negative-halfway and IEEE negative-zero regression tests; run CI #199: 162 tests, 0 failures.
- [x] Map Android V1.6 TEA preflight, 0x22 request, ACK=0 validity rule, erase 0x16 response wait, write 0x18 XOR transform, 240-byte blocks and three total attempts.
- [ ] Recover device-side key/challenge selection, entire firmware frame/ACK schema, integrity/authentication and recovery/resume.
- [ ] Compare equivalent auth/erase/write paths in Windows V1.6/V1.7 to establish version parity or differences.
- Firmware static reverse-engineering sub-workstream: 75%; weighted firmware package stays 55%, overall weighted score remains 72.6% (79.9 / 110).
- Detailed report: [ANDROID_V1_6_NATIVE_VALUESETUP_FIRMWARE_CODEC.md](ANDROID_V1_6_NATIVE_VALUESETUP_FIRMWARE_CODEC.md).


## 2026-11-22 — Windows V1.6/V1.7 static marker comparison

- [x] Run the same Ghidra 12.2 marker search on all three staged Windows V1.6 PE builds and the V1.7 PE.
- [x] Record common BLE UART, FTESC erase/write/bootloader, CAN, uartPackData and Qt BLE writeCharacteristic markers with per-build addresses and SHA-256.
- [x] Cross-check the latest V1.6 and V1.7 uartPackData string-loading stubs with Rizin and decompile their generic indirect thunks with Ghidra.
- [ ] Continue from the Qt static-metacall tables into actual V1.6 firmware/BLE function bodies; the stubs and generic thunks are not the transport implementation.
- [ ] Resolve the protected Windows BLE write target and compare its call arguments with the proven Android V1.6 WriteWithoutResponse path.
- Detailed report: [WINDOWS_V1_6_V1_7_STATIC_COMPARISON.md](WINDOWS_V1_6_V1_7_STATIC_COMPARISON.md).
- Overall weighted progress remains **72.6%**; marker-only comparison does not complete a functional replacement milestone.


## 2026-11-22 — Windows V1.6 UART frame/parser function-level pass

- [x] Decompile V1.6 Windows outer frame builder, AA/BB candidate parser and incremental stream handler.
- [x] Identify serial/device read loop and the direct QByteArray parser wrapper in `FtescLowLevelFace`.
- [x] Match V1.6 function roles to the V1.7 frame builder/parser/stream-handler roles.
- [x] Align Python frame error precedence with the native terminator-before-CRC order and add a regression test.
- [ ] Resolve the V1.6 per-instance maximum payload initializer and exact Qt method-index/string-table mapping.
- [ ] Complete the full V1.6/V1.7 function-level diff, including firmware and protected Windows BLE write path.
- Detailed report: [WINDOWS_V1_6_UART_FRAME_PARSER.md](WINDOWS_V1_6_UART_FRAME_PARSER.md).
- The V1.6 comparison sub-workstream moves from 25% to 45%; overall weighted project progress remains **72.6%**.


## 2026-11-22 — Windows V1.6 UartComm metadata and firmware send path

- [x] Decode the full V1.6 `UartComm` QMetaObject (50 methods / 19 signals) and resolve exact method names by relative string-pool offsets.
- [x] Map firmware-related slot indexes to static handler addresses and ACK signal names.
- [x] Trace firmware erase/write/boot-mode wrappers into the common `sendDataToESC(QByteArray&)` Qt signal.
- [x] Confirm the erase argument is serialized as four big-endian bytes and boot-mode sends an empty QByteArray.
- [ ] Trace the numeric INFO command IDs and incoming response dispatcher for erase/write/UUID/encryption ACKs.
- [ ] Resolve the `writeMcuEncrypt` helper and firmware key/challenge selection without publishing key material.
- [ ] Complete transfer block, ACK, retry/timeout, and recovery/resume state transitions.
- Detailed report: [WINDOWS_V1_6_UARTCOMM_QTMETAOBJECT.md](WINDOWS_V1_6_UARTCOMM_QTMETAOBJECT.md).
- V1.6 comparison sub-workstream: 45% → 55%; overall weighted project progress remains **72.6%**.


## 2026-11-22 — V1.6 firmware/CAN request-byte parity

- [x] Trace the command byte emitted by `ftescObtainFwVerSlot`, `ftescEraseFirmware`, `ftescWriteFirmware`, `ftescJPMBootMode`, `ftescObtainUuid` and `ftescObtainIdOverCan`.
- [x] Recover the V1.6 `ftescIdentifyMotorOverCan` CMD 0x0F DATA order and primitive writers.
- [x] Correct CMD 0x0F Python parity: arg4 truncates toward zero; arg3×100 rounds nearest/ties-away-from-zero.
- [x] Verify regression tests in GitHub Actions run #252: 164 passed, 0 failed.
- [ ] Trace incoming response dispatch and ACK layouts for ID/CAN discovery and firmware erase/write/UUID/encryption.
- [ ] Resolve the protected `writeMcuEncrypt` helper and firmware challenge/key provisioning without publishing secrets.
- Detailed report: [WINDOWS_V1_6_UARTCOMM_QTMETAOBJECT.md](WINDOWS_V1_6_UARTCOMM_QTMETAOBJECT.md).
- V1.6 comparison sub-workstream: 55% → 60%; overall weighted project progress remains **72.6%**.


## 2026-11-22 — V1.6 UART response command-to-signal mapping

- [x] Decompile the V1.6 `uartPackHandle` response dispatcher and inventory its command branches.
- [x] Resolve Qt signal wrapper indexes for firmware ACKs, UUID/encryption status, ID/CAN lists, telemetry, PPM/ADC, motor identification, setup reads, terminal/sample output and IMU calibration.
- [x] Record remaining response field-schema gaps without guessing payload layouts.
- [ ] Complete byte-level response decoders for the outstanding V1.6 response commands and compare against V1.7.
- Detailed report: [WINDOWS_V1_6_UART_RESPONSE_DISPATCH.md](WINDOWS_V1_6_UART_RESPONSE_DISPATCH.md).
- V1.6 comparison sub-workstream: 60% → 65%; whole-product weighted progress remains **72.6%**.


## 2026-11-22 — V1.6 separate CMD09/CMD0A setup responses

- [x] Confirm the CMD09 `0xD2C6EF10` and CMD0A `0x4879187D` marker checks and metadata-driven ValueSeque traversal.
- [x] Reuse the existing profile block decoder for V1.6 one-block responses while preserving unconsumed tail bytes.
- [x] Add unit tests for valid CMD09/CMD0A blocks and wrong marker rejection; GitHub Actions #266 passes (167 tests).
- [ ] Complete typed field names/units for the remaining PPM/ADC/IMU/motor-identification response APIs.
- Detailed report: [WINDOWS_V1_6_UART_RESPONSE_DISPATCH.md](WINDOWS_V1_6_UART_RESPONSE_DISPATCH.md).
- V1.6 comparison sub-workstream: 65% → 70%; overall weighted project progress remains **72.6%**.


## 2026-11-22 — V1.6 CMD1E ESC ID enumeration

- [x] Correlate the Windows response vector to the official V1.6 CMD1E definition (master ID first, then slave IDs).
- [x] Add an offline decoder with raw-vector preservation and tests for master/slave split and empty responses.
- [ ] Resolve the undocumented Windows CMD01 ID-vector semantics and the secondary Qt success boolean.
- Detailed report: [WINDOWS_V1_6_UART_RESPONSE_DISPATCH.md](WINDOWS_V1_6_UART_RESPONSE_DISPATCH.md).
- V1.6 comparison sub-workstream: 70% → 75%; overall weighted progress remains **72.6%**.


## 2026-11-22 — V1.6 CMD01 raw ID vector

- [x] Preserve the CMD01 DATA byte vector in an offline decoder without guessing its undocumented meaning.
- [x] Keep CMD1E as the separate documented master/slave ID enumeration response.
- [x] Verify raw vector, empty response and opcode validation tests in GitHub Actions #284 (172 tests passed).
- [ ] Resolve CMD01's command semantics and the secondary boolean argument of `ftescGetIDResAck` only with stronger native or official evidence.
- Detailed report: [WINDOWS_V1_6_UART_RESPONSE_DISPATCH.md](WINDOWS_V1_6_UART_RESPONSE_DISPATCH.md).
- V1.6 comparison sub-workstream: 75% → 78%; overall weighted project progress remains **72.6%**.
