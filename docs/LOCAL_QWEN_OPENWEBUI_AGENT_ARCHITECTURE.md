# Local Qwen agent architecture for the Flipsky reverse-engineering project

**Reviewed:** 2026-11-22  
**Purpose:** proposed Open WebUI configuration; no model was downloaded and no Open WebUI setting was changed in this session.

## Model selection

### Main planner: Qwen3.8-27B

Recommended first model to trial as the top-level agent:

- Official Ollama tag: `qwen3.8:27b` (the unqualified `qwen3.8` alias also resolves to the 27B model).
- Current Ollama Q4_K_M artifact is listed at approximately 18 GB, with a 256K context window and text/image input.
- Model card describes a 27B dense model, native 262,144-token context, vision-language input, flexible thinking controls and improvements for long-horizon agent tasks.
- Ollama's library marks it as supporting tools/thinking and lists common agent harness integrations.

Why it is the first choice: it is newer than Qwen3.6, has a smaller listed Ollama Q4 model blob than Qwen3.6-35B-A3B, and is explicitly designed for multi-step agent execution. This is a recommendation to benchmark on the actual hardware, not a claim that it will complete the whole reverse-engineering project without supervision.

References:
- Ollama model/tag: https://ollama.com/library/qwen3.8
- Qwen official model card: https://huggingface.co/Qwen/Qwen3.8-27B
- Qwen3.8 source repository: https://github.com/QwenLM/Qwen3.8

### Alternative main model: Qwen3.6-35B-A3B

- Official Ollama tag: `qwen3.6:35b-a3b`.
- The model has 35B total parameters with about 3B active per token; the current Ollama Q4_K_M build is listed at approximately 23 GB and 256K context.
- Active parameter count reduces per-token computation but does **not** make the model's stored weights a 3B model. It remains a materially larger model to load than a 9B helper.
- Qwen's Hugging Face card documents OpenAI-compatible serving and tool-use parser configuration for vLLM/SGLang.

Use it as the comparison model if its tool-use behavior or analysis quality proves better on the local hardware. It is not the smaller helper.

References:
- Ollama model/tag: https://ollama.com/library/qwen3.6
- Exact A3B variant: https://ollama.com/library/qwen3.6:35b-a3b
- Qwen model card: https://huggingface.co/Qwen/Qwen3.6-35B-A3B

### Small auxiliary model: Qwen3.5-9B

Suggested only for narrow, lower-risk jobs: summarizing REA evidence pages, extracting file/version metadata, drafting first-pass notes, classifying test logs and checking documentation consistency.

- Ollama Q4_K_M build is listed at approximately 6.6 GB, with 256K context and text/image input.
- Do not give this small helper unrestricted write, terminal, Gateway or ESC capabilities. Do not rely on it as the sole controller for long multi-step analysis or repository mutations.

Reference:
- Ollama tags: https://ollama.com/library/qwen3.5/tags

## Proposed division of work

| Agent | Model | Tools | Responsibility |
|---|---|---|---|
| Project coordinator | Qwen3.8-27B | Read-only REA, GitHub read, task tracker | Plan phases, choose next probes, check coverage, challenge unsupported conclusions |
| Native/Android analyst | Qwen3.8-27B or Qwen3.6-35B-A3B | REA Ghidra, Rizin/JADX evidence tools | Decompile targeted functions, correlate call paths, map JNI and BLE |
| Evidence clerk / report writer | Qwen3.5-9B | Read-only REA evidence pages, repository read | Extract exact hashes/addresses, normalize findings, draft Markdown |
| Test and CI reviewer | Qwen3.5-9B or main model | GitHub read + CI status; limited branch writes | Inspect failures, propose regression tests, verify CI results |

Keep the same project manifest, evidence IDs, progress formula and safety rules in every agent prompt. Sub-agents should receive bounded independent tasks; they should not concurrently edit the same files. The parent agent should review all findings, retain evidence IDs, recompute the weighted score and perform the sequential GitHub commit.

## Open WebUI integration layout

### 1. Model provider

Use Ollama (or a compatible local inference server) as the OpenAI-compatible model provider. Start by registering `qwen3.8:27b` and verify that its native tool calls survive an end-to-end Open WebUI test.

Set Function Calling to **Native / Agentic Mode**. Keep thinking enabled for the project coordinator; tune reasoning depth and output/context limits only after measuring memory and response quality. Start with a 32K–64K context rather than immediately forcing 256K: REA evidence is paged and should be queried by ID instead of pasting multi-megabyte reports into every prompt.

### 2. REA tools

Open WebUI supports remote MCP over Streamable HTTP starting with v0.6.31. In Settings → Admin → Integrations → External Tool Servers, add:

- ID: `rea`
- Type: MCP (Streamable HTTP)
- URL: `http://192.168.10.107:8765/mcp`

This address must be reachable **from the Open WebUI server/container**, not just from a user's browser. Test that route from the actual Open WebUI host before enabling it. In this investigation, the Gateway host could SSH to CT 107 on port 22, but could not reach the REA MCP port 8765; this is a network ACL/routing issue to solve explicitly, not an assumption that the MCP URL is already reachable everywhere.

Do not expose all 263 REA tools to every chat. Use Tool Search and Function Name Filter Lists, or place an allowlisted wrapper in front of REA. For ordinary analysis, allow evidence/session inspection, artifact inventory, strings/procedure searches, decompilation, call/reference inspection, APK/JADX analysis, static comparison and evidence export. Keep arbitrary shell execution, firmware write, GATT write, pairing and all motor/ESC control out of the general agent's tool list.

### 3. GitHub persistence

Connect a GitHub MCP/connector with repository-scoped permissions, or expose a narrow project MCP wrapper for:

- reading current status/roadmap/progress files;
- creating a report only after evidence review;
- sequentially updating README, STATUS, ROADMAP and PROGRESS_LOG;
- checking GitHub Actions for the exact commit SHA.

Use a dedicated project branch for automated changes, run CI, and merge only after review. Never let multiple agents update the same GitHub path simultaneously. Every report should include the REA evidence IDs and the exact artifact SHA-256 values that support its statements.

### 4. Gateway and file staging

Gateway is not automatically exposed to Open WebUI merely because both are installed. If Gateway operations must be model-callable, expose only a dedicated, allowlisted transfer/inspection service (or a restricted SSH account with forced commands) rather than root shell. Keep Nextcloud checkout tokens and temporary download URLs out of model-visible chat transcripts and logs.

### 5. Sub-agents and automation

Open WebUI sub-agents can delegate bounded tasks, but they inherit the parent chat's tools and filters; they are not an additional security boundary. Enable them only after REA/GitHub tool filters are narrow. Use separate model assignments for coordinator and clerical tasks. Background sub-agents are process-bound and can be interrupted by a server restart; durable jobs need a real scheduler/workflow engine and persisted job state, not just a prompt that says "continue later".

Open WebUI docs:
- MCP server configuration and tool requirements: https://docs.openwebui.com/features/extensibility/mcp/
- Native/legacy tool calling and model caveats: https://docs.openwebui.com/features/extensibility/plugin/tools/
- Sub-agents: https://docs.openwebui.com/features/chat-conversations/chat-features/subagents/
- Server-side tool calling: https://docs.openwebui.com/reference/server-side-tool-calling/

Important note from the Open WebUI tool documentation: an MCP connection makes tools available, but does not make a weak model reliable at choosing tools, building arguments or managing a multi-step chain. Test tool-call success, invalid-argument rates, loop length and recovery behavior before enabling autonomous writes.

## Acceptance tests before granting write access

1. Ask the model to inspect a known REA evidence ID and report the exact file hash and evidence ID. Confirm it does not invent missing facts.
2. Ask it to find a known V1.7 function and return one caller/callee relationship with address and evidence citation.
3. Ask it to compare one known APK class method, preserving the distinction between Qt backend code and Flipsky application code.
4. Ask it to draft a new GitHub report on a test branch; inspect the diff manually and require CI.
5. Send malformed arguments and stale evidence IDs; ensure it stops and reports the tool error rather than guessing.
6. Confirm the agent cannot call GATT write, pair, motor control, firmware flash, broad Gateway shell or upload/replace Nextcloud sources.

## What "no intervention" realistically means

A well-configured local agent can continuously perform low-risk static analysis, query evidence, draft reports, add regression tests and check CI. It still needs one-time configuration, resource sizing, network access, tool credentials, explicit access controls, persistent storage, and approval gates. It cannot create missing hardware validation, infer undocumented electrical behavior with certainty, or safely operate an ESC just by being given a prompt.

**Hardware constraint:** Qwen3.8 Q4 weights alone are listed at about 18 GB; Qwen3.6-35B-A3B Q4 at about 23 GB; Qwen3.5-9B Q4 at about 6.6 GB. Runtime memory must additionally cover KV cache, context length, vision projector, concurrent chats, and the serving runtime. These artifact sizes are not equivalent to a guaranteed VRAM requirement. Select the final model only after checking the GPU/VRAM, RAM, storage, backend and concurrent-use target.

No Open WebUI server, Ollama model, Gateway credential, tool filter or MCP connection was modified by this recommendation.
