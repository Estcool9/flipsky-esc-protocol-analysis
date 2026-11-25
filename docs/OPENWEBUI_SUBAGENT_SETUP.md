# OpenWebUI — single background sub-agent setup

**Updated:** 2026-11-25  
**Purpose:** let the main local Qwen agent delegate one focused task to one replaceable local worker, while the parent continues.

## Verified deployment

- OpenWebUI: Docker host `192.168.10.52`, container `open-webui`, version **0.13.5**; healthy after configuration restart.
- Ollama: `192.168.10.86:11434`, version **0.40.16**.
- Worker currently selected: OpenWebUI model ID **`local.lfm3:latest`** (Ollama model `lfm3:latest`, 1.2 GB).
- No model preset named `local.lfm3-worker` was created. The parent points to the direct LFM3 model; the optional per-model `think:false` preset is described below.

## Admin sub-agent limits (applied)

| Setting | Value |
|---|---:|
| Enabled | `true` |
| Background sub-agents | `true` |
| Max foreground concurrent | `1` |
| Max background async | `1` |
| Max tool-call iterations | `16` |
| Max result to parent | `6000` characters |

The max-foreground semaphore is read at startup; OpenWebUI was restarted after setting it to 1. Background limit and per-task iteration/output settings are read by the delegation code. The 16-iteration cap is a tool-round cap, not a wall-clock timer.

## Parent models configured

Each saved Qwen parent has exactly one sub-agent target, `local.lfm3:latest`, and the Sub-agents builtin category is enabled:

- `qwen3.8:27b`
- `local.qwen3.6:35b`
- `pc-est.qwen3.6:35b-a3b`
- `pc-est.qwen3.6:35b`

The parent model prompts were updated to use the explicit target and background mode for useful independent tasks. This matters because OpenWebUI uses the current parent model when `delegate_task` omits `model_id`, even when another target is configured.

Parent delegation instruction:

> For an independent, bounded subtask that benefits from a separate context, use the builtin `delegate_task` with `model_id="local.lfm3:latest"` and `background=true` so the LFM3 worker can run while you continue. Delegate only focused read-only research, extraction, summarization, or evidence gathering—not the whole project and not overlapping edits to shared files. Give the worker the exact goal, relevant function addresses/file paths, and required evidence format. Use at most one worker at a time. Review its result and verify important claims yourself; do not trust unsupported conclusions. Skip delegation for trivial work.

## Worker system prompt

The global sub-agent prompt now requires:

- One focused task; no recursive delegation.
- Promptly use tools instead of lengthy narration.
- Prefer bounded, read-only inspection.
- For reverse engineering, separate facts, hypotheses and unknowns; include exact addresses/offsets and evidence.
- Never send ESC commands, flash firmware or perform hardware writes.
- Do not commit/push or change the project score/checkpoint; return findings to the parent.
- Concise final result (under 4,000 characters preferred).

## LFM3 tool-call probe

Direct Ollama API probe with a harmless test tool:

- With `think:false`: tool call succeeded in **1.35 s**.
- With a tool-first system prompt and default thinking: tool call succeeded in **5.62 s** (62 generated tokens).
- An earlier 96-token probe with default thinking stopped before producing the tool call.

This is a direct Ollama tool-call test, **not** an end-to-end OpenWebUI `delegate_task` test.

## Optional one-time LFM3 fast preset

The current direct model has no saved Workspace preset, so its Ollama `think` setting is still Default. To pin fast tool mode:

1. Open **Workspace → Models → Create**.
2. Name it `LFM3 Worker (fast tools)`.
3. Set Base Model (From) to `local.lfm3:latest`.
4. In Advanced Params set:
   - Think (Ollama): **Off**
   - `num_ctx`: **8192**
   - `max_tokens`: **1536**
   - `temperature`: **0.1**
   - `keep_alive`: **10m**
5. Save and note the new model ID.
6. In each parent model's **Sub-agents** list, replace the single `local.lfm3:latest` target with that saved worker ID.

Ollama's `think:false` is an API request parameter. It is not a supported Modelfile `PARAMETER` in the installed Ollama generation; use OpenWebUI's per-model Advanced Params instead. Official docs: [OpenWebUI model editor](https://docs.openwebui.com/features/workspace/models/) and [Ollama thinking API](https://ollama.com/blog/thinking).

## How the parent should delegate

Use a short, self-contained task, for example:

```text
delegate_task(
  task="Trace callers of function 0x00495910 and report direct evidence.",
  context="V1.7 is open in REA/Ghidra. Return caller addresses, evidence IDs, and unknowns. Read-only; do not modify files.",
  model_id="local.lfm3:latest",
  background=true
)
```

Use the worker for independent extraction, function summaries, caller/xref lists, string classification, or evidence formatting. Keep architectural conclusions, cross-build synthesis, shared-file edits, commits and score updates with the parent.

OpenWebUI sub-agents inherit the parent's tools, skills and filters, but start with a focused context. Attachments do not automatically transfer; pass their IDs using `file_ids`. Sub-agents cannot delegate recursively. Background sub-agents require a saved chat.

Official reference: [OpenWebUI Sub-agents](https://docs.openwebui.com/features/chat-conversations/chat-features/subagents/).

## Hardware and connector caveats

- The OpenWebUI-connected Ollama endpoint is CT 102 (`ollama`) on Proxmox host `192.168.10.18`, exposed as `192.168.10.86:11434`. Latest `ollama ps` showed `lfm3:latest` at **100% CPU**, context 4096. Read-only Proxmox inspection found no `/dev/nvidia*` device nodes or `nvidia-smi` on the host; CT 102 has optional NVIDIA bind-mount entries, but its device nodes are mode `000` and `nvidia-smi` reports `GPU access blocked by the operating system`. Therefore this connected Ollama is CPU-only in practice; the RTX 2060 is not available to it. No Proxmox/GPU configuration was changed. To use the 2060, OpenWebUI must connect to an Ollama endpoint running on the machine where that GPU is accessible, or the GPU must be correctly installed/assigned to the Proxmox host and passed through to CT 102 (a separate infrastructure change requiring approval).
- OpenWebUI logs show repeated `InvalidToken. Stored OAuth client data is invalid` errors for connected MCP OAuth clients. A sub-agent inherits those same tools, so affected connectors need reauthorization in OpenWebUI **Settings → Connections**. No secret key was rotated and no OAuth tokens were modified.
- The end-to-end OpenWebUI background delegation has not yet been verified from an authenticated chat. The configuration and model-level tool call are verified separately.

## Backups

Database snapshots were saved inside the OpenWebUI data directory before configuration/model metadata changes, including:

- `webui.db.pre-subagents-20261125`
- `webui.db.pre-qwen-builtin-subagents-20261125`
- `webui.db.pre-qwen-delegation-prompt-20261125`
- `webui.db.pre-subagents-iteration16-20261125`

No project progress score was changed by this infrastructure setup.
