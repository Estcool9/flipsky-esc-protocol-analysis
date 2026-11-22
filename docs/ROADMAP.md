# Technical roadmap

**Overall estimated progress: 80% (2026-11-22).**

## Phase A — Static application mapping

- [x] Identify executable format, architecture and runtime.
- [x] Verify the V1.7 executable SHA-256.
- [x] Identify Qt/C++/QML and loaded transport modules.
- [x] Extract and validate embedded XML resources.
- [x] Generate a reproducible parameter catalog.
- [x] Map initial Qt UART/BLE signal-slot wiring.
- [x] Identify FtescLowLevelFace and uartPackData meta-object roles.
- [x] Map all 64 FtescLowLevelFace Qt meta-object dispatch indexes to native implementations; high-level API strings are catalogued.
- [ ] Confirm all callers and exact role of the tea_encrypt method.
- [x] Locate the uartPackData frame parser and frame builder.

## Phase B — Protocol reconstruction

- [x] Trace serial receive callback into the parser.
- [x] Identify outer frame boundaries and AA/BB markers.
- [x] Identify INFO length semantics and big-endian extended length.
- [x] Reconstruct CRC-16/MODBUS parameters and coverage.
- [x] Establish big-endian 16/32-bit readers.
- [x] Extract public V1.6 command IDs and main payload layouts.
- [x] Compare public V1.4 and V1.6 protocol revisions.
- [x] Build offline frame and selected command/telemetry codecs.
- [x] Run synthetic test vectors (51 passed, 0 failed on a fresh public clone).
- [x] Map most V1.7 outbound command IDs to UartComm request builders; full payload schemas remain open.
- [ ] Map all V1.7 numeric response IDs to Qt acknowledgements and parsers (0x00, 0x01, 0x0F, 0x11, 0x16, 0x18, 0x1A, 0x1E, 0x29 and setup-family IDs are now correlated).
- [ ] Trace the separate CMD 0x02 one-shot request path and confirm V1.7 offsets against V1.6; current mapped response switch has no 0x02 branch and the signal index 13 is not a request builder. See [V1_7_ONE_SHOT_CMD_02_STATUS.md](V1_7_ONE_SHOT_CMD_02_STATUS.md).
- [ ] Trace CAN forwarding and slave response dispatch.
- [ ] Establish exact cross-callback fragmentation/reset behaviour.
- [ ] Determine BLE's exact frame/envelope format.
- [ ] Analyse authentication/key-check flow without disclosing secrets.
- [ ] Determine whether ordinary UART payloads are encrypted.
- [ ] Reconstruct firmware-update block transfer and TEA usage.

**Exit criterion:** a complete protocol description with static references, source-spec reconciliation and reproducible offline test vectors for each supported command.

## Phase C — V1.4/V1.6 binary comparison and VESC assessment

- [x] Review Flipsky's distinction between FT ESC and FSESC product families.
- [x] Inventory V1.4, V1.5, three V1.6 and V1.7 Windows builds in Nextcloud.
- [x] Read public V1.4 and V1.6 UART protocol documents.
- [ ] Stage the latest V1.6 Windows executable on REA.
- [ ] Compare V1.6 and V1.7 Qt metadata, function bodies, constants and resources.
- [ ] Confirm exact ESC model and hardware revision targeted by V1.7.
- [ ] Compare proven frame/opcode/checksum details with VESC Tool and firmware.
- [ ] Mark features identical, similar or incompatible based on code evidence.

## Phase D — Offline tooling

- [x] Implement parser and encoder for confirmed outer frame layout.
- [x] Implement selected V1.6 command and telemetry decoders.
- [x] Decode V1.7 CMD 0x00 extended angular fields and PAS RPM offline.
- [x] Cross-check short-frame bytes against a separately maintained FTESC UART implementation.
- [x] Create synthetic test vectors and unit tests.
- [x] Add offline stream-chunking, partial-frame retention and resynchronization tests (synthetic data only).
- [ ] Add offline capture replay using authorized passive captures.
- [ ] Add a simulator for benign, read-only responses.
- [ ] Add command-schema validation after remaining setup and CAN request schemas are mapped.

## Phase E — Hardware validation (later)

- [ ] Obtain exact ESC model and hardware revision.
- [ ] Obtain matching firmware through an authorized source.
- [ ] Capture a passive session during connection and information readout.
- [ ] Validate only benign read operations in a mechanically safe setup.
- [ ] Do not issue unknown writes, motor commands or firmware operations.

## Current blockers / availability

- The three V1.6 Windows executables are in Nextcloud and inventoried, but not on the REA host yet.
- The current REA sample directory contains only the V1.7 Windows executable.
- Rizin 0.9.1 and Ghidra 12.2 are already installed; no additional reverse-engineering package is required for current static work.
- The user's Nextcloud V1.6 protocol PDF, user manual and ECU-side C example were readable and have been documented in this repository.

No serial/BLE command was sent to an ESC and no firmware was flashed.
