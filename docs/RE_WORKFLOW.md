# Reusable reverse-engineering workflow for REA / Gateway

**Updated:** 2026-11-22  
**Purpose:** make the next binary, firmware utility or protocol investigation reproducible without rediscovering the workflow from scratch.

## 1. Current REA host toolchain

The current Linux REA analysis host has these verified tools:

| Tool | Version / path | Use |
|---|---|---|
| Ghidra | `/opt/ghidra_12.2_PUBLIC` | GUI analysis, data types, function boundaries, xrefs, decompiler and program database |
| Rizin | `/opt/rea-tools/releases/rizin-0.9.1/bin/rizin` | CLI disassembly, function analysis, references, strings, pseudocode and scripting |
| rz-bin | `/opt/rea-tools/releases/rizin-0.9.1/bin/rz-bin` | file type, sections, imports, resources and PE/ELF/Mach-O metadata |
| Python | 3.13.5 | bounded extraction scripts, protocol codecs and regression tests |
| Java | OpenJDK 25 | Ghidra runtime |

For the present native PE32 Qt/C++ target this is sufficient. **Do not install IDA Pro or Hopper just to continue this project.** They would add licensing and workflow complexity without resolving the current blockers. Add another tool only when a concrete file format or runtime requires it.

## 2. Intake: never start analysis before artifact identity

Create an immutable original-artifact record before extracting or modifying anything.

Required fields:
- original filename and source location;
- byte length;
- SHA-256;
- file magic / format and architecture;
- compiler/runtime clues;
- acquisition time and transfer method;
- whether the input is executable code, firmware, a resource archive, a memory dump or a document.

Recommended layout for each new project:

```text
project-name/
  artifacts/original/       # immutable input; do not commit binaries
  artifacts/derived/        # extracted resources / transformed data
  ghidra/                   # local project export notes, not DB by default
  rizin/                    # scripts, analysis commands and logs
  docs/
    ARTIFACT_INVENTORY.md
    ANALYSIS_CHECKPOINT.md
    EVIDENCE_LEDGER.md
    PROGRESS_LOG.md
    ROADMAP.md
  analysis-data/
  scripts/
  tests/
```

Keep original binaries, firmware, dumps, proprietary libraries, credentials and live device secrets out of public Git repositories by default. Store only hashes, file metadata, documented findings and derived data whose redistribution is authorized.

## 3. Triage: quick format and section review

Run metadata tools first; never execute an unknown program as a triage shortcut.

Rizin examples:

```bash
/opt/rea-tools/releases/rizin-0.9.1/bin/rz-bin -I sample.exe
/opt/rea-tools/releases/rizin-0.9.1/bin/rz-bin -S sample.exe
/opt/rea-tools/releases/rizin-0.9.1/bin/rz-bin -i sample.exe
/opt/rea-tools/releases/rizin-0.9.1/bin/rz-bin -R sample.exe
```

For a Rizin database:

```bash
rizin -A sample.exe
```

Useful commands within Rizin:

```text
iI              # binary information
iS              # sections
ii              # imports
iz              # strings
afl             # analyzed functions
axt @ addr      # references to an address
pdf @ addr      # disassembly
pdc @ addr      # decompiler output (quality depends on target/analysis)
```

Always record virtual addresses and file offsets separately. Convert between them through the section mapping; never assume RVA equals file offset. If a section is packed/protected, mark the unpacking state as unknown until backed by execution tracing or a proven unpacker routine. Unusual section names or high entropy alone do not prove a specific protector.

## 4. Resource extraction: bounded and reproducible

Start with strings and format-native resource metadata:
- PE resources and Qt `qRegisterResourceData`;
- ELF sections, notes and embedded archives;
- Mach-O sections and resource bundles;
- firmware package headers and documented compression formats.

For compressed streams:
- validate the compression header and checksum;
- impose a per-stream decompression output limit;
- reject incomplete streams and suspicious expansion sizes;
- parse XML/JSON before saving as structured data;
- calculate a SHA-256 for every extracted resource;
- deduplicate by content hash;
- record the original offset and extraction method.

This project added `scripts/scan_compressed_xml.py`, which scans bounded Zlib streams for well-formed XML, reports possible Qt `qCompress` length prefixes and deduplicates resources. It recovered 6 more unique ValueSetup XML resources after the original fixed-offset extractor had already been working. Keep the generic scanner separate from target-specific known-offset extraction.

## 5. Native application mapping

For each transport/UI class:
1. Identify strings, exported names, RTTI/typeinfo, vtables and Qt meta-object records.
2. Map signal/slot method signatures and method indexes.
3. Resolve `qt_static_metacall` / static meta-call switch cases to native functions.
4. Record callers and callees for each public request.
5. Trace data ownership across the full route: QML action → request builder → signal/slot → frame builder → serial/BLE transport.
6. Trace the reverse route: transport ready-read → incremental receive buffer → frame parser → response dispatcher → acknowledgement/data model → UI signal.
7. Follow important state variables into their read/write call sites; a UI field or log string alone does not prove it affects the transmitted bytes.

For each reported function record:
- VA and section;
- function start and end;
- decompiler and disassembly references;
- callers/callees;
- input/output buffer ownership;
- relevant structure offsets;
- exact evidence ID in REA, when available;
- confidence: confirmed, strongly inferred, tentative, unknown or contradictory.

A negative finding must be scoped to the path that was actually examined. For example, “no CMD 0x10 prepend in the normal UartComm send chain” is defensible; “there is no CAN forwarding anywhere in the app” is not.

## 6. Protocol reconstruction

Create one protocol adapter per genuinely distinct product/firmware family. Do not infer compatibility from brand, UI similarities or shared Qt code.

For each layer, capture:
- UART framing markers, length width/endian, checksum parameters/coverage and terminator;
- command namespace and per-command payload schema;
- response/ACK routing;
- direct CAN extended identifier bit layout and DLC;
- UART-over-CAN forwarding wrapper;
- BLE service/characteristic UUIDs, MTU/chunk size, write/notify behaviour;
- firmware authorization, bootloader transitions, image/chunk format and retries;
- configuration data model and exact serialization order.

Build tests for:
- published reference vectors;
- minimum/maximum lengths;
- signed and unsigned numeric values;
- all supported endian/scaling modes;
- malformed length, CRC and marker;
- fragmented reads at every split point;
- concatenated frames and resynchronization;
- unknown commands and future-version extensions;
- byte-for-byte regeneration of extracted metadata.

Keep command encoders offline-only until the full protocol and hardware safety envelope are independently validated.

## 7. Evidence, notes and confidence discipline

Use the following labels consistently:
- **CONFIRMED:** visible in direct source bytes/code or validated by an exact reference vector.
- **CROSS-CHECKED:** independently matches another implementation or official protocol document.
- **STRONG INFERENCE:** several call paths agree but no direct runtime observation.
- **TENTATIVE:** plausible from naming/strings/single function only.
- **UNKNOWN:** not recovered.
- **CONTRADICTORY:** source documents or code disagree; retain both alternatives and do not guess.

Maintain a chronological progress log. After each milestone, update:
- the evidence index / source inventory;
- the technical document for the affected subsystem;
- tests and fixtures;
- the README summary;
- the authoritative checkpoint and remaining blockers;
- the weighted completion estimate.

Progress percentages must be tied to named work packages and weights. Do not use “protocol is 95% done” to imply the desktop app or hardware validation is ready.

## 8. GitHub and CI discipline

- Keep binaries, firmware, dumps and device secrets excluded by default.
- Store large extracted text only when redistribution is authorized. This repository uses gzip/Base64 payloads plus SHA-256 manifests because the content must survive API transfers reproducibly.
- Restore payloads using `scripts/restore_payloads.py --root .`.
- Rebuild catalogs from original extracted inputs and compare generated files byte-for-byte.
- Run `python -m unittest discover -s tests -v` and `python -m compileall -q scripts tests`.
- Keep exact source commit IDs for external projects; never compare against a moving `master` without recording the resolved commit.

## 9. Current project example

For the Flipsky project:
- original artifact: PE32 x86 executable with a recorded SHA-256;
- tools: Ghidra 12.2 and Rizin 0.9.1 on REA;
- resources: 19 unique Zlib XML `ValueSetups` profiles;
- tests: 148 passing;
- protocols: separate FTESC and VESC UART/CAN offline adapters;
- open blockers: TopFlow metadata/SKU map, exact FTESC V1.7 gateway routing, complete firmware update state machine, BLE details, desktop UI/real transport integration and hardware validation.

No device has been connected and no command was sent during this workflow.
