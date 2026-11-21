# Technical roadmap

## Phase A — Static application mapping

- [x] Identify executable format, architecture and runtime.
- [x] Verify the executable SHA-256.
- [x] Identify Qt/C++/QML and loaded transport modules.
- [x] Extract and validate embedded XML resources.
- [x] Generate a reproducible parameter catalog.
- [x] Map initial Qt UART/BLE signal-slot wiring.
- [x] Identify the FtescLowLevelFace class and static Qt meta-object.
- [ ] Map every meta-object dispatch index to its implementation.
- [ ] Confirm callers and exact role of the `tea_encrypt` method.
- [ ] Locate the low-level UART component implementation.

## Phase B — Protocol reconstruction

- [ ] Trace serial receive callback to byte-buffer accumulation.
- [ ] Identify frame boundaries and start/end markers.
- [ ] Identify length and command/opcode fields.
- [ ] Reconstruct payload layouts for each read-only query.
- [ ] Identify CRC/checksum algorithm and parameters.
- [ ] Establish endianness and numeric scaling.
- [ ] Describe fragmentation, escaping, retry, timeout and error behaviour.
- [ ] Analyse authentication/key-check flow without disclosing secrets.
- [ ] Determine whether BLE wraps UART packets or uses a distinct frame format.

**Exit criterion:** a protocol description backed by disassembly references and reproducible offline test vectors.

## Phase C — VESC compatibility assessment

- [x] Review Flipsky's distinction between FT ESC and FSESC product families.
- [ ] Confirm the exact ESC model and hardware revision this application targets.
- [ ] Compare proven frame/opcode/checksum details with VESC Tool and firmware.
- [ ] Mark each feature as identical, similar or incompatible based on code evidence.

## Phase D — Offline tooling

- [ ] Implement a parser for confirmed frame layouts.
- [ ] Create synthetic test vectors and unit tests.
- [ ] Implement an encoder only after command and payload semantics are validated.
- [ ] Add an offline replay harness.
- [ ] Add a simulator for benign, read-only responses.

## Phase E — Hardware validation (later)

- [ ] Obtain exact ESC model and hardware revision.
- [ ] Obtain matching firmware through an authorized source.
- [ ] Capture a passive session during connection and information readout.
- [ ] Validate only benign read operations in a mechanically safe setup.
- [ ] Do not issue unknown writes, motor commands or firmware operations.

## Tooling needs

No additional REA tool is required for the next static-analysis phase: Rizin 0.9.1 and Ghidra 12.2 are already available. A Windows debugger in an isolated VM is optional for later runtime observation. A passive UART/USB capture is a higher-value input than another static-analysis package.
