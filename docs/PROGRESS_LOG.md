# Progress log

## 2026-11-25 — OpenWebUI single LFM3 background sub-agent configured

### OpenWebUI configuration

- OpenWebUI 0.13.5 on Docker host 192.168.10.52; container returned healthy after the configuration restart.
- Enabled background sub-agents and constrained the deployment to one foreground and one background worker at a time.
- Limits: 16 tool-call rounds per worker and 6,000 characters returned to the parent.
- Configured one LFM3 target (`local.lfm3:latest`) on the saved Qwen3.8/Qwen3.6 parent models. Enabled the Sub-agents builtin category.
- Added parent instructions to explicitly use `delegate_task(model_id="local.lfm3:latest", background=true)` for independent, read-only work. The worker prompt requires tool-first behavior, evidence and no recursive delegation, hardware writes or GitHub commits.
- Database backups were taken before configuration changes; paths and exact settings are documented in [OPENWEBUI_SUBAGENT_SETUP](OPENWEBUI_SUBAGENT_SETUP.md).

### LFM3 tool-call check and caveats

- A harmless direct Ollama API tool-call probe succeeded with `think:false` in 1.35 seconds.
- With a tool-first system prompt and default thinking, the same probe succeeded in 5.62 seconds (62 generated tokens). This is a direct Ollama probe, not a full OpenWebUI delegation test.
- Latest `ollama ps` showed LFM3 using 100% CPU, context 4096. Ollama runs in Proxmox CT 102; the Proxmox host has no NVIDIA device nodes or `nvidia-smi`, and CT 102's optional GPU bind mounts resolve to mode-000 device nodes (`nvidia-smi`: GPU access blocked by OS). The connected Ollama endpoint is CPU-only in practice, so the RTX 2060 is not available to this OpenWebUI connection. No GPU/LXC passthrough changes were made.
- OpenWebUI logs contain repeated `InvalidToken. Stored OAuth client data is invalid` errors for MCP OAuth clients. Affected connectors need reauthorization; no secret key or tokens were changed.

### Project score

- Overall reverse-engineering project score remains **72.6% (73% rounded)**. This infrastructure configuration adds no protocol coverage and does not change the score.
- No ESC hardware was contacted; no firmware was flashed.

### Commits

- `21d9cb3c1b943a2332fff717783f4a229e0b8bdd` — added [OPENWEBUI_SUBAGENT_SETUP](OPENWEBUI_SUBAGENT_SETUP.md).
- `7977e3c9c32fb1e98c875d964c59fc94482d5834` — linked the setup guide from README.
- `586d5b1757cddefa3cffd0167588f05e11683235` — clarified the CPU-only Ollama/GPU access diagnosis.

---

## 2026-11-25 — V1.7 TopFlow read selector and CAN-forward TX helper traced

**Binary:** V1.7 2026-10-29 (`dba48a24…`), REA 6.10.1 / Ghidra 12.2.

### Artifact and preservation

- V1.7 source at CT107 `/data/samples/Flipsky_ESC_Tool_V1.7_20261029.exe`: 50,611,200 bytes; SHA-256 `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`.
- Read-only working copy staged at `/data/analysis/pe/v1.7_20261029/Flipsky_ESC_Tool_V1.7_20261029.exe`; hash/size verified, original preserved.
- V1.6 retained Evidence exported to `/data/analysis/reports/evidence-v1.6-pre-v1.7-20261125.json` (232 records, 19,440,198 bytes), then V1.6 was closed normally before opening V1.7.

### TopFlow selection and request

- String inventory confirms `ftesc/1.7/TopFlowSetupValueTable.xml` at `0x52ed00`; `FUN_00488010` selects this path when its selector argument is 1. Other values select the combined Motor/Control setup table path.
- `FUN_00487fc0` maps selector 1 to `TopFlowMainController`.
- `FUN_0048c700` is the Read Setup event path; it reads object offset `+0x40`. Value 1 selects manual setup; other values use the automatic realtime-data ACK path.
- `FUN_004891d0` dispatches automatic setup reads using the same selector: 1 -> `FUN_004972f0`; other -> `FUN_00496bf0`.
- `FUN_004972f0` logs `Send TopFlow setup read command`, calls the command factory with `0x3B`, applies a pending-response/factory-restore guard, and sends through `FUN_00495910`.
- The exact product/SKU meaning of selector 1 and the actual TopFlow XML bytes remain unknown.

### V1.7 CAN-forward correction

- `FUN_00495910` reads the command byte from the QByteArray. When UartComm `+0x0C` (canForward) is active, it calls protected helper `PTR_FUN_00f591c0` with UartComm `+0x10` (canId), then with literal `0x10`, before forwarding through `FUN_004bbc20`.
- The TopFlow 0x3B request explicitly uses this shared helper; 0x3B is in the diagnostic setup-command range 0x3A–0x3D.
- This supersedes the earlier negative conclusion that V1.7 `FUN_00495910` simply forwarded the QByteArray unchanged. The two helper invocations are directly observed; the helper target is Enigma-protected (`0x00b5aadc`) and the lower send target (`0x00b5ac7c`) is also undecodable, so the emitted byte sequence is not yet proven by disassembly or capture.

### Bounded Qt/RCC scan

- Rizin PE inspection found no standard PE resource entries (`rz-bin -U` empty). The parsed .rdata file-offset range is 0x11DA00–0xB28E00.
- A bounded scan of .rdata for common zlib headers found 41 complete streams (36 unique payloads), of which 19 parsed as XML. They are the existing ValueSetups resources; no TopFlow table payload was recovered.
- The same scan of other PE regions found 2,648 candidate header positions but no complete zlib streams. Three raw `<?xml` candidates in .enigma1 are garbled and not parseable; they remain unclassified.
- qResourceFeatureZlib and qRegisterResourceData name strings occur in .idata, but their Ghidra xref lists are empty; they are not proof of a live registration call.
- Full V1.7 Evidence export: `/data/analysis/reports/evidence-v1.7-topflow-can-20261125-final.json`, 308 records, 32,692,246 bytes, 0 unknowns, SHA-256 `3b94f6ae5e3ab59b9031c517ab33c4e642f876e612490bc7c23aa1f0fce25413`.

### Progress

- Overall project estimate remains 72.6% (73% rounded); this scan did not recover the TopFlow payload or implement new functionality.

### Evidence IDs

- TopFlow string search: `ev_8af1e4554c4ea676dc76a0ef18e14f0ef77a04d6c76e5242cb4802ee51b2d4f3`.
- Selector-to-table helper: `ev_235d3fba5a5d3ea3a0063220e75e6dcf0ce439b7948bf7a6c176853bae419996`.
- Read Setup handler: `ev_3c9d8b16b9747ab4221f94a6c1b0a053881cc6edb97777dc54e20dea8c07b554`.
- TopFlow send command: `ev_3459543a9785d2fb17b4791c0aa3d262101352745b8df0e697175642abe9b634`.
- Shared TX helper: `ev_5577ccc5290ab681440823555f6ab93ba5406f09896f8c684001c6f96e6b6b4b`.

### Progress

- Overall weighted estimate unchanged: **72.6% (73% rounded)**. This is a new reverse-engineering finding, not implementation or hardware validation.
- No test suite was run and no ESC hardware was contacted; no UART/CAN/BLE command was transmitted.

---

## 2026-11-25 — V1.6 CMD 0x10 CAN-forward wrapper confirmed in TX helper

**Binary:** V1.6 2026-09-12 (`051d57a7…`), Ghidra 12.2 via REA 6.10.1, checkpoint active.

### Facts (DIRECT CODE EVIDENCE)

- `FUN_00492ab0` decompiled fully (REA evidence `ev_9407521b152a83ed0c9eb9e261cdfff4faea8a455c2c11d9a5c1fbe5020ed0ca`).
- **UartComm `+0x0C`** = CAN-forward enable flag (byte, non-zero = active). Confirmed by pseudocode branch `if (*(char *)(in_ECX + 0x0C) != '\0')`.
- **UartComm `+0x10`** = CAN slave target ID (byte/char). Confirmed by `PTR_FUN_00c53314((int)*(char *)(in_ECX + 0x10))`.
- When canForward is active, the UUID helper pointer `PTR_FUN_00c53314` is called twice: once with the slave ID, once with the literal `0x10`. This is the **inline CMD 0x10 wrapper insertion** mechanism in V1.6.
- After the CAN wrapper calls, the standard UART frame builder (`PTR_FUN_00c535b0(param_1)`) is called with the original payload.
- String `"Sending to ESC:"` is embedded in this function (confirmed via pseudocode).
- Function has 25 callers, 11 direct callees, 14 computed call sites. Callees include `0x4b55f0` (cleanup) and 10 functions in the `0x854f08–0x856b18` range (Enigma/Qt virtual).

### Hypotheses

- The two calls to `PTR_FUN_00c53314` with `slave_id` then `0x10` likely build the prefix `[0x10][slave_id]` before the actual payload bytes, matching the public FTESC V1.6 UART protocol CMD 0x10 format (`CMD | CAN_ID | nested_payload`). This is a STRONG INFERENCE based on the argument order and the known protocol spec; the exact byte sequence is not directly readable from the Enigma-protected helper.

### Unknowns

- Exact byte-level output of `PTR_FUN_00c53314` (Enigma-protected, 1-byte Ghidra body, unresolvable statically).
- Whether V1.7 performs CMD 0x10 insertion through a path not yet traced (separate signal, BLE path, or gateway-specific slot).
- Slave response routing in both V1.6 and V1.7.

### Architectural difference V1.6 vs V1.7 (CONFIRMED)

- V1.6 `FUN_00492ab0`: inserts CMD 0x10 wrapper inline **before** calling the frame builder.
- V1.7 `FUN_00495910`: passes QByteArray unmodified to the frame builder signal. No CMD 0x10 insertion observed in the normal transmit chain.

### Progress update

- CAN/gateway workstream: **65%** (up from 60%). The V1.6 insertion mechanism is now confirmed. V1.7 alternate path and slave response routing remain.
- Overall weighted estimate: **73%** (up from 72%).

### Commits

- `7464055983d5de47cf25ea54f1e884b118c0e2fe` — `docs/CAN_FORWARDING_STATE.md` updated with V1.6 TX helper analysis.
- `6e4c3673133cca4176134c3769a3b911ce857175` — `docs/ANALYSIS_CHECKPOINT.md` updated.

---

## 2026-11-22 — Project baseline

- Identified the Windows executable as PE32 x86, native, with no CLR/.NET header.
- Verified its SHA-256: `dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38`.
- Observed unusual `.enigma1` and `.enigma2` sections; a protected/packed build is plausible, but the exact protector is not confirmed.
- Recovered and validated 13 Zlib-compressed XML resources.
- Built a reproducible catalog with 736 profile rows, 222 unique parameter IDs and 13 profile/resource variants.
- Identified Qt 5, C++, QML, QtSerialPort and QtBluetooth components.
- Mapped the first UART signal/slot connections in the FtescLowLevelFace initialization path.
- Published the project reports, analysis scripts, catalogs and all 13 extracted XML resources to GitHub. Larger text files are stored as gzip/base64 payloads; [the restoration guide](PAYLOAD_FORMAT.md) explains how to reconstruct them.
