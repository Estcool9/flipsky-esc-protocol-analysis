# Nextcloud Software source inventory

Source folder: /Projet Perso/Revolt-Engine/Software  
Inventory: 92 entries, tree not truncated at depth 5.  
This is a Nextcloud source inventory only. It does not mean each binary has been copied to REA or analyzed.

## Flipsky ESC Tool executables

| Version/build | Relative path | Size (bytes) | Status |
|---|---|---:|---|
| V1.1 | Flipsky ESC Tool/Flipsky ESC Tool V1.1/Flipsky ESC Tool V1.1.exe | 25,850,368 | Inventoried; not staged |
| V1.2 | Flipsky ESC Tool/Flipsky ESC Tool V1.2/Flipsky ESC Tool V1.2.exe | 28,235,776 | Inventoried; not staged |
| V1.3 | Flipsky ESC Tool/Flipsky ESC Tool V1.3/Flipsky ESC Tool V1.3.exe | 28,941,312 | Inventoried; not staged |
| V1.4 | Flipsky ESC Tool/Flipsky ESC Tool V1.4/Windows/Flipsky_ESC_Tool_V1.4_20240826.exe | 18,999,808 | Inventoried; not staged |
| V1.5 | Flipsky ESC Tool/Flipsky ESC Tool V1.5/Windows/Flipsky ESC Tool V1.5 20250511.exe | 97,531,904 | Inventoried; not staged |
| V1.6 (2025-10-14) | Flipsky ESC Tool/Flipsky ESC Tool V1.6/Windows/Flipsky_ESC_Tool_V1.6_20251014.exe | 97,949,184 | Inventoried; not staged |
| V1.6 (2026-08-06) | Flipsky ESC Tool/Flipsky ESC Tool V1.6/Windows/Flipsky_ESC_Tool_V1.6_20260806.exe | 44,867,072 | Inventoried; not staged |
| V1.6 (2026-09-12) | Flipsky ESC Tool/Flipsky ESC Tool V1.6/Windows/Flipsky_ESC_Tool_V1.6_20260912.exe | 45,582,336 | Inventoried; not staged |
| V1.7 (2026-10-29) | Flipsky ESC Tool/Flipsky ESC Tool V1.7/Windows/Flipsky_ESC_Tool_V1.7_20261029(1).exe | 50,611,200 | Analyzed in REA; SHA-256 dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38 |

A root-level V1.7 file with the same date and size is also present. Confirm SHA-256 before treating it as a distinct build.

## Cross-platform and mobile versions

| Artifact | Relative path | Size (bytes) | Status |
|---|---|---:|---|
| V1.6 macOS DMG (2025-10-14) | Flipsky ESC Tool/Flipsky ESC Tool V1.6/Mac/Flipsky_ESC_Tool_V1.6_20251014.dmg | 23,527,248 | Inventoried; not staged |
| V1.6 Android BLE APK | Flipsky ESC Tool/Flipsky ESC Tool V1.6/Android/Flipsky ESC Tool BLE V1.6/Flipsky_ESC_Tool_V1.6.apk | 44,167,894 | High-value BLE cross-check; not staged |
| V1.5 UART C reference | Flipsky ESC Tool/Flipsky ESC Tool V1.5/ftesc_v1.4_1.5_uart_handle.c | 12,690 | Read through Nextcloud |
| V1.6 UART C reference | Flipsky ESC Tool/Flipsky ESC Tool V1.6/ftesc_v1.4_1.5_1.6_uart_handle.c | 12,314 | Read through Nextcloud |

The Android V1.6 app is especially valuable because it is explicitly labelled as the BLE tool. A static comparison against the V1.7 Windows BleUart implementation may independently confirm GATT direction, characteristic properties, CCCD writes, MTU and packet chunking.

## TFT firmware and update tooling

| Artifact | Relative path | Size (bytes) | Status |
|---|---|---:|---|
| TFT application V2.0 | Flipsky TFT V2.0/V2.0/20250428_Ebike_TFT_APP_V2_0.bin | 492,096 | Inventoried; not staged |
| TFT application V2.1 | Flipsky TFT V2.0/V2.1/20251126_Ebike_TFT_APP_V2_1.bin | 494,548 | Inventoried; not staged |
| Remote update tool V1.4 | FS-VX_Remote_Update_Tool_V1.4.exe | 13,544,960 | Inventoried; not staged |

These are separate products/artifacts from the FTESC/VESC desktop protocol targets. Do not mix their firmware or commands into ESC Tool protocol profiles without identifying their exact device boundaries.

## Highest-value next intake

1. Stage all three V1.6 Windows executables to REA and hash them; compare 2025-10-14 → 2026-08-06 → 2026-09-12 → V1.7.
2. Stage the V1.6 Android BLE APK and perform a static cross-check of BLE UUIDs, characteristic properties, CCCD writes and chunking.
3. Stage the V1.6 macOS DMG only if cross-platform packaging/UI comparison becomes important.
4. Stage TFT firmware only for the separate TFT firmware investigation, not as a substitute for ESC firmware.

Current blocker: the binaries are visible in Nextcloud but have not been materialized into the REA analysis host. No files in the source folder were changed by this inventory.
