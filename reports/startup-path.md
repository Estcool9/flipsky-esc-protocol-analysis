# Narrow startup disassembly notes

Tool: Rizin 0.9.1, targeted `pd` at explicit addresses only. No executable was launched.

## Observations

- PE entry point: VA `0x00401480`.
- `0x00401480` writes `1` to global `0x00f573f8`, calls `0x004c08d0`, then jumps to `0x00401150`.
- A second nearby entry variant at `0x004014a0` writes `0` to the same global, calls the same routine, then jumps to `0x00401150`.
- At `0x004c08d0`, the routine compares the stored word at `0x0051f3bc` with the common sentinel `0xbb40e64e`; it derives a non-default value through helper calls and stores the value and complement at `0x0051f3bc` / `0x0051f3c0`. This is strongly consistent with compiler security-cookie initialisation, not evidence of an Enigma unpacker.
- `0x00401150` performs process/runtime startup work, including a TLS-related read from `fs:[0x18]`, a `lock cmpxchg` on a global state field, and calls into static initialization helpers.
- `0x004c0be0` is the short sequence `fninit; ret`, an FPU-state initialization helper.
- `0x004c0d60` walks table-like structures and invokes helper routines; this is consistent with runtime/static initializer traversal, but the exact table semantics were not proven in this pass.

## Interpretation and limits

The visible entry path is a conventional native startup/CRT path and does not expose the UART protocol. It does not rule out runtime unpacking or code restoration elsewhere, especially given the large `.enigma1` raw section and unusual PE mappings. The `.enigma1` / `.enigma2` names remain a protection/packing indicator, not proof of a particular product or version.

Next useful step: follow the references to the UART/FTESC method-name strings from the resource/meta-object tables, then map any resulting code addresses to the file-backed source ranges. The current broad full-file string indexing attempt was cancelled because it exceeded the time window; do not treat that cancelled scan as evidence.
