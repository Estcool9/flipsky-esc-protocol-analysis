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
| Apktool 3.0.3 | Verified at `/usr/local/bin/apktool` | Decode APK manifest/resources and Smali (no APK staged yet) |
| ADB 34.0.5 | Verified at `/usr/bin/adb` | Read-only device inventory/logs when an authorized handset is attached; no device contacted |

## Missing or unavailable optional tools

These are not all required to finish the current PE analysis. They apply only to the corresponding workstream.

| Tool/capability | Current REA status | Needed for |
|---|---|---|
| Hopper | Executable missing at /opt/hopper/bin/Hopper | Independent GUI decompiler cross-check; optional |
| IDA MCP adapter | REA_IDA_MCP_CONFIG not configured | Independent IDA cross-check; optional |
| Kuna | REA_KUNA_COMMAND not configured; PE not admitted by this provider | Alternative analysis on supported ELF/Mach-O, not this PE |
| JADX headless MCP bridge | Verified operational: engine 0.7.1, backed by installed JADX 1.5.7 / Temurin JDK 25 | Static Java/Dex decompilation of the staged V1.6 BLE APK; Qt Android BLE methods decompiled successfully |
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

Priority 1 is application-level function analysis. The three V1.6 Windows EXEs and the Android BLE APK are staged in read-only version-specific directories on CT 107. APK/JADX analysis is operational; the native application library is extracted for both ARM64 and ARMv7. Targeted Ghidra analysis of the large ARM64 application library timed out, while Rizin 0.9.1 symbol inventory responded. Continue with small function batches and preserve the timeout as an analysis limitation.

Priority 2 is Windows PE function-level comparison. Ghidra/Rizin identify PE32 x86, but the import inspectors fail to map the Enigma-protected import descriptor ranges. Rizin strings confirm common BLE/FTESC marker sets across V1.6/V1.7. Use bounded string/symbol and disassembly probes; do not describe the empty partial import rows as no imports.

Priority 3 is Qt QML resource decoding. The APK `.rcc` bundle is extracted and hash-verified, but its embedded QML call sites have not been decoded. Apktool 3.0.3 is configured; ADB 34.0.5 is available but no Android device was contacted.

Priority 3 is protocol verification hardware. A known controller and firmware revision, safe bench power arrangement, BLE-capable phone, passive BLE capture, UART capture and a USB-CAN adapter/capture are needed for actual behavior validation. The desktop app must remain read-only until transport assumptions have been independently captured and verified.

## No installation performed

No tools were installed, no REA environment variables were modified, no Android device was connected, and no physical ESC was controlled. Hopper, IDA, APK tooling, sigrok, Binwalk/Unblob and other optional tools are not prerequisites for continuing the current Ghidra PE analysis.


## Session verification — 2026-11-22

- Confirmed `/usr/local/bin/apktool` reports Apktool 3.0.3.
- Confirmed `/usr/bin/adb` reports Android Debug Bridge 34.0.5-debian. The version check did not contact a device; no `adb devices` query or device operation was performed.
- The caller reports JADX 1.5.7 and Temurin JDK 25 installed in the REA environment. The specific JADX MCP bridge JAR/configuration path has not yet been verified.
- The V1.6 APK and Windows binaries are not staged on REA. The Nextcloud temporary checkouts were authorized, but the available Gateway endpoint is another LXC host and cannot reach CT 107 / `192.168.10.107:8765`.


## V1.6 artifact staging and JADX verification — 2026-11-22

- Four source artifacts were checked out from Nextcloud read-only, transferred via Gateway SSH to CT 107, and verified by matching source/destination size and SHA-256.
- Staged paths: `/data/analysis/pe/v1.6_20260912/`, `/data/analysis/pe/v1.6_20260806/`, `/data/analysis/pe/v1.6_20251014/`, and `/data/analysis/android/v1.6_ble/`.
- JADX headless MCP 0.7.1 is operational and successfully decompiled `QtBluetoothLE` methods. Apktool 3.0.3 is available. No ADB device query or handset operation was performed.
- Extracted Android native libraries and Qt RCC resource to `/data/analysis/extracted/v1.6_ble_native/`; extracted files were hash-verified by REA.
- See [ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md](ANDROID_V1_6_NATIVE_BLE_REVERSE_ENGINEERED.md).
