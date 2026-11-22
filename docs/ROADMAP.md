# Technical roadmap — open-source Flipsky client

**Reference date:** 2026-11-22  
**Overall project progress: 72%** (weighted whole-product estimate; scoring table in [STATUS.md](STATUS.md)).

## Phase A — Artifact intake and static reverse engineering

- [x] Inventory and SHA-256 verify the V1.7 PE32 executable.
- [x] Identify native x86 / Qt 5 / C++ / QML architecture and transport modules.
- [x] Inventory Ghidra 12.2 and Rizin 0.9.1 tools on REA.
- [x] Map key Qt meta-objects, signals/slots and static meta-call indexes.
- [x] Map the main UART receive and transmit paths.
- [x] Trace the normal UartComm transmit path end-to-end and document the scoped CMD 0x10 negative finding.
- [x] Add a generic bounded Zlib/XML resource scanner and regression tests.
- [ ] Finish QML resource tree and all remaining UI/property dynamic behaviour.
- [ ] Obtain and compare the staged V1.6 Windows executable with V1.7.

## Phase B — FTESC protocol reconstruction

- [x] Recover AA/BB UART framing, payload length semantics, CRC-16/MODBUS and DD terminator.
- [x] Implement frame decoding, encoder and incremental receive stream/resynchronization tests.
- [x] Map the majority of V1.7 request builders and response dispatch/ACK signals.
- [x] Implement offline request/response codecs for discovered control, identity, telemetry, setup and string operations.
- [x] Recover typed setup value serialization and response decoding for observed types.
- [x] Extract 19 unique ValueSetup resources and generate reproducible catalogs and ValueSeque order files.
- [ ] Recover TopFlow ValueSetup XML and exact model/SKU mapping.
- [ ] Validate all V1.7 command response layouts against passive captures.
- [ ] Resolve remaining V1.7 request-schema and unknown command cases.

## Phase C — CAN, BLE and gateway behaviour

- [x] Implement and test FTESC direct CAN V1.4 ID, CRC and periodic telemetry decoders.
- [x] Document the V1.4 PDF ambiguities around brake IDs, status cadence and 0x0D parser widths.
- [x] Map the V1.7 CAN target UI state, ID discovery and request call sites.
- [x] Trace the standard UartComm path: it does not prepend the public V1.6 CMD 0x10 wrapper at the examined insertion points.
- [ ] Determine how the V1.7 selected CAN ID reaches the external FTESC Gateway (side channel or alternate path).
- [ ] Recover slave response correlation and error/time-out mapping.
- [ ] Find BLE service and characteristic UUIDs, MTU/chunk size and write/notification mode.
- [ ] Implement FTESC BLE transport only after the wire path is established.

## Phase D — VESC/FSESC parallel protocol profile

- [x] Read all four user-supplied Flipsky VESC UART/CAN V1.0 PDFs (English and Chinese).
- [x] Cross-check UART framing/CRC/command IDs against pinned VESC Tool source.
- [x] Cross-check direct CAN command IDs and identifier composition against pinned VESC firmware.
- [x] Add `scripts/vesc_uart.py` and tests for 02/03/04 framing and VESC CRC.
- [x] Add `scripts/vesc_can.py` and tests for VESC target/command ID layout and basic scaling.
- [x] Add explicit adapter-family matrix: FTESC NON-VESC vs FSESC VESC.
- [ ] Expand VESC GET_VALUES response decoder and firmware-version compatibility profiles.
- [ ] Add version negotiation and explicit user-selected protocol-profile UX; never infer protocol from brand alone.
- [ ] Decide whether the open-source app will implement only the documented Flipsky V3.00 profile or multiple VESC firmware generations.

## Phase E — Firmware update and security state machine

- [x] Recover V1.7 UUID response path and TEA challenge/request usage.
- [x] Recover the 240-byte block payload builder and XOR transform.
- [x] Implement offline firmware authorization/block helpers.
- [ ] Complete all bootloader entry, erase, write, ACK, retry and timeout transitions.
- [ ] Identify exact firmware image container/metadata and checksum/signature.
- [ ] Validate against an authorized firmware image; do not flash during protocol discovery.
- [ ] Add safe recovery/abort states to the replacement application before any firmware UI is enabled.

## Phase F — Open-source application implementation

- [x] Define a separate protocol-adapter boundary and document family selection rules.
- [ ] Build desktop app shell and project structure (Qt/PySide or another explicitly chosen stack).
- [ ] Implement serial-port discovery and connection state as a read-only first milestone.
- [ ] Implement passive receive/telemetry display with raw-frame logging and replay.
- [ ] Implement configuration views backed by FTESC ValueSetup metadata and explicit ValueSeque ordering.
- [ ] Implement CAN topology / slave list after gateway routing is resolved.
- [ ] Add BLE only after characteristics and packet transport are known.
- [ ] Implement firmware update UI only after the full state machine and recovery path are validated.
- [ ] Match the essential Flipsky ESC Tool V1.7 functionality without copying proprietary UI assets or source.

## Phase G — Reproducibility and validation

- [x] Use content hashes and manifests for binary/resource identity.
- [x] Restore large data artifacts from gzip/Base64 payloads.
- [x] Regenerate parameter and profile catalogs deterministically.
- [x] Add GitHub Actions for artifact restore, regeneration compare, unit tests and compileall.
- [x] Maintain tests for FTESC framing, stream recovery, requests, responses, setup serializer, firmware blocks, direct CAN, generic XML scanning and VESC UART/CAN.
- [x] Fresh REA clone test run: **148 passed, 0 failed**.
- [ ] Add protocol capture replay fixtures from authorized passive traces.
- [ ] Build a benign fake-ESC simulator for read-only responses.
- [ ] Perform a staged bench test with a known ESC model, firmware and mechanically safe configuration.
- [ ] Document hardware validation for each model/version; do not extrapolate between SKUs.

## Future generic reverse-engineering workflow

- [x] Add [RE_WORKFLOW.md](RE_WORKFLOW.md) covering intake, triage, Ghidra/Rizin, Qt metadata, bounded extraction, evidence discipline, tests and GitHub hygiene.
- [x] Add a generic compressed XML scanner for future Qt/resource-heavy programs.
- [ ] Add a reusable blank project-template generator for artifact inventory, evidence ledger and checkpoint files.

## Current blockers

1. **TopFlow:** the V1.7 executable references `:/ftesc/1.7/TopFlowSetupValueTable.xml`; the complete scan found more ValueSetup profiles but not the TopFlow table itself.
2. **CAN target path:** the UI stores the flag and target ID, but the standard send path inspected does not add the V1.6 `0x10` envelope. Need an authorized Gateway document, alternate path or passive trace.
3. **Firmware update:** the authorization and block codec are partially recovered; image container/recovery state is incomplete.
4. **Desktop application:** no serial/BLE UI or device integration has been implemented yet.
5. **BLE:** transport UUIDs and packet chunking remain unknown.
6. **Hardware:** no live controller validation has occurred.
7. **V1.6 binary comparison:** binaries are inventoried in Nextcloud but not staged in the REA sample directory.

## Safety boundary

All current protocol encoders and decoders are offline. No UART, CAN or BLE interface has been opened. No ESC control command or firmware update was transmitted.
