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

## 6. Next static probes

1. Resolve each slot's relocation/protection region and the owning image section in its own PE, rather than reusing VAs across builds.
2. Compare surrounding instruction windows and static data references at each target; keep unresolved indirect control flow explicit.
3. Trace all callers of the output QByteArray constructors and the wrappers' argument ownership/copy boundaries.
4. Only change `parse_uuid_response()` if a stable byte-level transform or length constraint becomes visible in a shipped artifact or official protocol evidence.

## 7. Safety and provenance

- Static PE/Rizin analysis only; none of the three Windows applications was executed.
- No UART, CAN or BLE command was transmitted.
- No controller was connected and no firmware was flashed.
- No keys, protected tables or secret device material are published.
