# Windows V1.6 UUID / MCU helper — three-build call-graph comparison

**Reference date:** 2026-11-23  
**Scope:** static disassembly of the three staged Windows V1.6 PE32 builds. No protected routine was executed and no ESC was contacted.

## 1. Artifact identity and local analysis paths

All three Windows V1.6 executables are staged read-only on the REA host. Their SHA-256 values were re-measured there on 2026-11-23.

| Build | Size (bytes) | SHA-256 | REA path |
|---|---:|---|---|
| 2025-10-14 | 97,949,184 | `1dc93bd84f4dab1a3ee7b3946fa0522c78fc870227523d8d5fe6d6e187ea2b07` | `/data/analysis/pe/v1.6_20251014/Flipsky_ESC_Tool_V1.6_20251014.exe` |
| 2026-08-06 | 44,867,072 | `94cfd851a5ccce38b8c42c9f154128e10fa2906ce9efc9cddfa39c4a00361a03` | `/data/analysis/pe/v1.6_20260806/Flipsky_ESC_Tool_V1.6_20260806.exe` |
| 2026-09-12 | 45,582,336 | `051d57a776782ae8daaeaa45179f9b568f7e89b4a78ab8dd8e558ecd3e53b968` | `/data/analysis/pe/v1.6_20260912/Flipsky_ESC_Tool_V1.6_20260912.exe` |

## 2. Shared indirect-call topology

Rizin cross-reference inspection (`axt`) finds exactly two static call sites to the same indirect-call slot in each executable:

| Build | Indirect-call slot | Slot bytes resolve to | First xref: MCU write helper | Second xref: response dispatcher |
|---|---|---|---|---|
| 2025-10-14 | `0x00B7C178` | `0x0077DA60` | `FUN_004933D0 @ 0x00493423` | `FUN_004943B0 @ 0x00494AF4` |
| 2026-08-06 | `0x00BD9318` | `0x007DB110` | `FUN_004938F0 @ 0x00493943` | `FUN_004948D0 @ 0x00495014` |
| 2026-09-12 | `0x00C53318` | `0x00855110` | `FUN_004938F0 @ 0x00493943` | `FUN_004948D0 @ 0x00495014` |

The absolute slot and target addresses move between builds, but the two xref roles remain the same: one caller is the MCU-encryption/write request path and the other is the incoming UUID (`CMD 0x21`) response branch. This is observed static call-graph correspondence, not proof that the targets contain byte-identical code.

## 3. Outbound CMD 0x22 caller

The caller-side setup matches across all three builds.

- The 2025-10-14 build initializes a QByteArray-like local through `FUN_00496330`, appends command byte `0x22` through `FUN_00496360`, places `0x10` and `1` in the helper call context, saves the original method argument pointer, then calls slot `0x00B7C178` at `0x493423`.
- The 2026-08-06 and 2026-09-12 builds use `FUN_00496850` to initialize the output object, append `0x22` through `FUN_00496880`, place `0x10` and `1` in the corresponding stack/context fields, save the original method argument pointer, then call their respective slots at `0x493943`.

The stable facts are the command tag (`0x22`), the literal context values (`0x10` and `1`), the retained original argument pointer, and the indirect-call location. The protected callee's exact parameter signature is not recovered, so `0x10` and `1` are not labelled as a proven block length, round count, key size or boolean mode.

## 4. Inbound CMD 0x21 UUID caller

In the 2026-09-12 build, the response dispatcher is `FUN_004948D0`; its case `0x21`:

1. Initializes a QByteArray-like output local using `FUN_00496850`.
2. Resets the UUID cooldown/throttle field at `this+0x28`.
3. Places `0x0C` and a zero-valued context argument into the helper call frame.
4. Calls the same indirect slot `0x00C53318` used by `writeMcuEncrypt`.
5. Passes the resulting QByteArray-like object to `FUN_004B5670`, whose Qt wrapper is method index 1, `ftescGetUuidAck(QByteArray)`.

The 2026-08-06 build has the same dispatcher/call-site addresses and slot (`0x00BD9318`). The 2025-10-14 build uses dispatcher `FUN_004943B0`, calls slot `0x00B7C178` at `0x494AF4`, then calls `FUN_004B51E0`. The latter wrapper loads Qt method index 1 and passes the output object through the common Qt activation call. In the 2026-09-12 build, index 1 is independently named `ftescGetUuidAck`; the 2025 wrapper's exact signal string was not separately re-established in this pass.

The offline `parse_uuid_response()` therefore continues to preserve the raw CMD21 DATA length and bytes. The native call path does not provide a proven fixed 16-byte validation rule in the decompiled dispatcher.

## 5. What is and is not established

**Established by static evidence:**
- All three staged builds contain the same two-role indirect-call topology.
- The outgoing caller constructs a CMD22-tagged output object and invokes the shared helper with the same observed context values.
- The CMD21 dispatcher invokes that helper and forwards its resulting byte-array object to a one-argument Qt signal wrapper.
- The pointer slot and target address are version-specific and must not be hard-coded across binaries.

**Still unknown:**
- The native body/algorithm behind targets `0x0077DA60`, `0x007DB110` and `0x00855110`.
- The exact ABI names/types corresponding to context values `0x10`, `1` and `0x0C`.
- Whether the helper performs encryption, decryption, serialization, a protected copy, or a combination.
- UUID transformation/normalization, byte order, canonical length and device-side semantics.
- Whether the Windows helper is equivalent to the separate Android V1.6 TEA routine. No equivalence is assumed.

The existing Android V1.6 TEA evidence remains scoped to that APK; it is not transferred to these Windows PE builds. Do not infer a 16-byte UUID rule from the separate firmware preflight buffer size.


## 6. Ghidra target-body validation

The three resolved target addresses were then queried independently through REA/Ghidra 12.2:

| Build | Queried target | Ghidra function body | Observed decompiler outcome |
|---|---|---|---|
| 2025-10-14 | `0x0077DA60` | `0x0077DA60–0x0077DA60` (1 byte) | Invalid control-flow/data warnings, implausible I/O/access expressions and termination at `halt_baddata()` |
| 2026-08-06 | `0x007DB110` | `0x007DB110–0x007DB110` (1 byte) | One isolated register/memory expression, then `halt_baddata()` |
| 2026-09-12 | `0x00855110` | `0x00855110–0x00855110` (1 byte) | Implausible I/O and calculated memory accesses, then `halt_baddata()` |

The recovered body extents are only one byte in all three sessions. The extra pseudocode emitted beyond those extents is **not** accepted as a decoded implementation. This is consistent with an unrecognized, virtualized, packed or otherwise non-standard code/data region, but the available evidence does not identify a specific protector or establish which mechanism caused the bad boundary.

The practical conclusion remains unchanged: the cross-build call graph is established, the protected helper implementation is not. Do not translate these decompiler expressions into Python, and do not infer an encryption algorithm from the CMD22 method name alone.

## 7. PE section and VirtualProtect cross-build map

### Static section placement

For all three PE builds, the pointer slot and the address stored in it are in different sections:

- The indirect-call slot is in `.idata` (static section flags `-rw-`).
- The stored target VA is in `.rdata` (static flags `-r--`, no execute bit).
- Ghidra recovers only a one-byte body at each stored target and fails decompilation there.

This is a static-image property, not a claim about runtime page protection.

### All statically recovered VirtualProtect call-site groups

Rizin `axt` on the import stub produces the same six call sites in each PE:

| Role | 2025-10-14 | 2026-08-06 | 2026-09-12 | Recovered arguments/behavior |
|---|---|---|---|---|
| Six-byte patch protection + restore | `0xB9F601`, `0xB9F62D` | `0xBFC601`, `0xBFC62D` | `0xC76601`, `0xC7662D` | First call uses `dwSize=6`, `flNewProtect=0x40` (PAGE_EXECUTE_READWRITE); second restores the saved old protection. The orchestrator in each build supplies eight addresses inside that build's `.enigma2` region. |
| Unclassified wrapper call | `0xBA5607` | `0xC02607` | `0xC7C607` | Rizin reports no containing function at the call instruction; caller/argument semantics are not sufficiently recovered. |
| Dynamic import resolver protection + restore | `0xBBCC7D`, `0xBBCC96` | `0xC19C7D`, `0xC19C96` | `0xC93C7D`, `0xC93C96` | Four-byte target slot is temporarily made RWX (`0x40`), then old protection is restored. The same resolver path calls `LoadLibraryA` and `GetProcAddress`, then writes the resolved function pointer into `[ESI]`. |
| Separate data-region protection | `0xBBD708` | `0xC1A708` | `0xC94708` | `flNewProtect=0x04` (PAGE_READWRITE, **not executable**); size is read from a descriptor/object field at offset `+0x54`; the destination is resolved through the loader's descriptor table. |

### Six-byte patcher details (2026-09-12 build)

The orchestrator `FUN_00C7667C` passes these eight addresses to the patch helper `FUN_00C765E0`:

`0x00C988A8`, `0x00C988C0`, `0x00C988CC`, `0x00C988D8`, `0x00C988B4`, `0x00C988E4`, `0x00C988F0`, `0x00C988FC`.

All eight fall inside the `.enigma2` virtual range of the September build (`0x00C61000–0x00CA1000`). This is consistent with local runtime patching of the protection/loader's own region. It is **not** evidence that the helper's three target VAs (`0x0077DA60`, `0x007DB110`, `0x00855110`) are the addresses being reprotected.

### Dynamic import resolver (2026-09-12 build)

The unique caller of `FUN_00C93A58` is `FUN_00C93F88` at `0x00C946E8`. The resolver uses a descriptor pointer, reads its `+0x10` field as the pointer-slot destination, temporarily applies `0x40` to four bytes there, performs `LoadLibraryA`/`GetProcAddress`, writes the resolved pointer to `[ESI]`, then restores the previous protection. The caller-side descriptor calculation is table-relative; no static value equality between this destination and the UUID helper target has been found.

`FUN_00C93F88` also has the separate `0x00C94708` PAGE_READWRITE call. This is not PAGE_EXECUTE_READWRITE and must not be used as evidence that the UUID target is made executable.

### Conclusion

The three builds clearly contain the same families of self-modifying/runtime loader operations, and these explain why a normal static PE section map may not represent all runtime behavior. However, the known six-byte patch locations are in `.enigma2`, the four-byte resolver destination is descriptor-driven, and the other well-identified call only requests PAGE_READWRITE. **No current static evidence connects these operations to the UUID helper targets in `.rdata`.** Whether a different dynamic/unpacked path makes those targets executable remains open.
## 8. Next static probes

1. Resolve each slot's relocation/protection region and the owning image section in its own PE, rather than reusing VAs across builds.
2. Compare surrounding instruction windows and static data references at each target; keep unresolved indirect control flow explicit.
3. Trace all callers of the output QByteArray constructors and the wrappers' argument ownership/copy boundaries.
4. Only change `parse_uuid_response()` if a stable byte-level transform or length constraint becomes visible in a shipped artifact or official protocol evidence.

## 9. Safety and provenance

- Static PE/Rizin analysis only; none of the three Windows applications was executed.
- No UART, CAN or BLE command was transmitted.
- No controller was connected and no firmware was flashed.
- No keys, protected tables or secret device material are published.


Latest repository verification: GitHub Actions run #300, **177 tests passed, 0 failed**; artifact restoration, catalog/profile rebuild and Python compileall passed. https://github.com/Estcool9/flipsky-esc-protocol-analysis/actions/runs/45065537376


Latest repository verification: GitHub Actions run #301, **177 tests passed, 0 failed**; artifact restore, catalog/profile regeneration and Python compileall passed. https://github.com/Estcool9/flipsky-esc-protocol-analysis/actions/runs/45066338144
