# REA tooling audit — Flipsky project

Audit date: 2026-11-22  
Active target: Flipsky ESC Tool V1.7 PE32 x86  
Active static provider: Ghidra 12.2  
Host: Linux; macOS-native tools are unsupported on this host.

## Ready now

| Tool/capability | State | Use |
|---|---|---|
| Ghidra 12.2 through REA | Available | Primary native PE32 reverse engineering: decompilation, xrefs, imports, functions and evidence |
| Rizin/rz-bin 0.9.1 | Verified installed in prior REA host check | Independent PE triage and instruction-level cross-check |
| REA evidence registry/checkpoints | Available | Evidence tracking and target-bound Ghidra checkpoint |
| Python unittest / compileall in project CI | Available | Offline protocol implementation tests |
| Nextcloud file inventory/read | Available | Source tree, manuals, C references and PDF text |

## Missing or unavailable optional tools

These are not all required to finish the current PE analysis. They apply only to the corresponding workstream.

| Tool/capability | Current REA status | Needed for |
|---|---|---|
| Hopper | Executable missing at /opt/hopper/bin/Hopper | Independent GUI decompiler cross-check; optional |
| IDA MCP adapter | REA_IDA_MCP_CONFIG not configured | Independent IDA cross-check; optional |
| Kuna | REA_KUNA_COMMAND not configured; PE not admitted by this provider | Alternative analysis on supported ELF/Mach-O, not this PE |
| ADB / Android platform-tools | REA_ADB_PATH not set | Android device interaction and logcat/device facts |
| Apktool | REA_APKTOOL_COMMAND not set | Decoding Android resources/manifest for V1.6 BLE APK |
| JADX MCP server/JAR + JDK | Required by REA Android package/class/method analysis; not verified here | Static Java/DEX decompilation of V1.6 BLE APK |
| JEB MCP server | Not running at default MCP endpoint | Alternative Android/Dex decompilation; optional if JADX is supplied |
| sigrok-cli | REA_SIGROK_COMMAND not set | Decoding logic-analyzer recordings |
| Binwalk | REA_BINWALK_COMMAND not set | Identifying firmware containers/embedded regions |
| Unblob | REA_UNBLOB_COMMAND not set | Extracting supported firmware/container payloads |
| pwntools 4.15 | REA_PWNTOOLS_PYTHON not set | ELF layout/crash workflows; not required for this PE |
| WABT | REA_WABT_BIN_DIRECTORY not set | WASM analysis; not relevant to current native Qt PE |
| Wakaru | REA_WAKARU_COMMAND not set | JavaScript bundle recovery; optional for QML work |
| Browser import resolver | REA_BROWSER_EXECUTABLE not supplied | Native JavaScript module resolution |
| Native macOS/Xcode utilities | Unsupported host | DMG/Mach-O inspection and macOS runtime capture |
| BLE hardware capture stack | No BLE capture source supplied | Verifying GATT traffic, notifications, MTU and write behavior |
| USB-CAN / UART capture setup | No capture fixture or hardware provided | Validating FTESC command and CAN gateway behavior |

## What is actually needed next

Priority 1 is source staging, not a different decompiler. Ghidra is sufficient for the immediate PE work. The biggest blocker is materializing the three V1.6 Windows executables and the V1.6 BLE Android APK from Nextcloud onto the REA analysis host. Without those local bytes, neither a version diff nor APK decompilation can run.

Priority 2 is Android static analysis. For the APK, provide/configure JADX MCP JAR + JDK (and optionally Apktool for resources). ADB is only needed if an Android device is used for controlled runtime observation.

Priority 3 is protocol verification hardware. A known controller and firmware revision, safe bench power arrangement, BLE-capable phone, passive BLE capture, UART capture and a USB-CAN adapter/capture are needed for actual behavior validation. The desktop app must remain read-only until transport assumptions have been independently captured and verified.

## No installation performed

No tools were installed, no REA environment variables were modified, no Android device was connected, and no physical ESC was controlled. Hopper, IDA, APK tooling, sigrok, Binwalk/Unblob and other optional tools are not prerequisites for continuing the current Ghidra PE analysis.
