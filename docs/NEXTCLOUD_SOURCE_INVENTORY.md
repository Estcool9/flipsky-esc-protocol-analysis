# Nextcloud source inventory — Flipsky ESC Tool project

**Source directory:** /Projet Perso/Revolt-Engine/Software/Flipsky ESC Tool  
**Inventory date:** 2026-11-22  
**Observed tree:** 76 entries; Nextcloud reported the listing was not truncated. Entries listed here were in the user's personal Nextcloud storage and readable.

## Windows application builds

| Version | Filename | Size (bytes) |
|---|---|---:|
| 1.1 | Flipsky ESC Tool V1.1.exe | 25,850,368 |
| 1.2 | Flipsky ESC Tool V1.2.exe | 28,235,776 |
| 1.3 | Flipsky ESC Tool V1.3.exe | 28,941,312 |
| 1.4 | Flipsky_ESC_Tool_V1.4_20240826.exe | 18,999,808 |
| 1.5 | Flipsky ESC Tool V1.5 20250511.exe | 97,531,904 |
| 1.6 | Flipsky_ESC_Tool_V1.6_20251014.exe | 97,949,184 |
| 1.6 | Flipsky_ESC_Tool_V1.6_20260806.exe | 44,867,072 |
| 1.6 | Flipsky_ESC_Tool_V1.6_20260912.exe | 45,582,336 |
| 1.7 | Flipsky_ESC_Tool_V1.7_20261029(1).exe | 50,611,200 |

The V1.7 executable staged on REA is the same 50,611,200-byte build and has SHA-256 dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38.

**Important:** the three V1.6 Windows builds are inventoried in Nextcloud but are not yet staged on REA. Binary-to-binary comparison with V1.7 has therefore not yet been performed.

## Protocol and application references

| Version | File | Size (bytes) | Notes |
|---|---|---:|---|
| 1.4 | FLIPSKY FTESC UART Protocol V1.4 English.pdf | 510,037 | 21 pages; issue date 2025-04-22 |
| 1.4 | FLIPSKY FTESC CAN Protocol V1.4 English.pdf | 618,754 | CAN protocol reference |
| 1.6 | FLIPSKY FTESC UART Protocol V1.6 English.pdf | 534,546 | 23 pages; issue date 2025-12-09 |
| 1.6 | FLIPSKY FTESC UART 通信协议 V1.6 中文.pdf | 520,303 | Chinese counterpart |
| 1.6 | Flipsky ESC Tool V1.6 User Manual.pdf | 7,387,878 | 90 pages |
| 1.6 | Flipsky ESC Tool V1.6 用户手册.pdf | 7,181,943 | Chinese manual |
| 1.6 | ftesc_v1.4_1.5_1.6_uart_handle.c | 12,314 | ECU-side illustrative protocol C example |

The C example is preserved in reference/ftesc_v1.4_1.5_1.6_uart_handle.c. It is not the ESC Tool source code or ESC firmware source.

## Other platform builds and packages

| Version | Platform | File | Size (bytes) |
|---|---|---|---:|
| 1.4 | Android | Flipsky ESC Tool.apk | 85,801,054 |
| 1.4 | macOS | Flipsky_ESC_Tool_V1.4_20241113_beta.dmg | 21,607,671 |
| 1.5 | Android | Flipsky ESC Tool.apk | 43,087,806 |
| 1.5 | macOS | Flipsky_ESC_Tool_V1.5_20250511.dmg | 23,026,010 |
| 1.6 | Android | Flipsky_ESC_Tool_V1.6.apk | 44,167,894 |
| 1.6 | macOS | Flipsky_ESC_Tool_V1.6_20251014.dmg | 23,527,248 |

## Other assets

- Windows CDC serial driver folders are present in earlier Windows application packages (V1.1-V1.5).
- V1.5 product-manual directory includes PDF manuals for FT60BD, FT85BD, FT85BS, FT85BS V2.0, FT85GS, FT85KS and FT85RS variants.
- V1.7 Mac and Android directories are present in the tree, but no deeper files from those folders were listed in the depth-5 inventory.

## Current staged analysis assets

- REA host executable: /data/samples/Flipsky_ESC_Tool_V1.7_20261029.exe
- REA project: /data/projects/Flipsky-ESC-Tool-analysis
- Only the V1.7 Windows executable is presently staged on REA.
- Public V1.4/V1.6 protocol documents and C sample have been text-extracted through Nextcloud and documented in this repository.
- No V1.6 executable has yet been extracted into the REA project.


## VESC/FSESC protocol source folder

**Source directory:** `/Projet Perso/Revolt-Engine/Software/VESC Protocol`  
**Inventory date:** 2026-11-22  
**Observed files:** 4 readable PDF files; all were in the user's personal Nextcloud storage.

| File | Size (bytes) | Modified in Nextcloud | Document number / version |
|---|---:|---|---|
| `VESC UART Protocol V1.0.pdf` | 466,634 | 2025-04-15 | `VESC-CM-UART-20250331-01`, V1.0 |
| `VESC UART 协议 V1.0.pdf` | 306,249 | 2025-04-15 | `VESC-CM-UART-20250331-01`, V1.0 |
| `VESC CAN Protocol V1.0.pdf` | 515,319 | 2025-04-26 | `VESC-CM-CAN-20250331-01`, V1.0 |
| `VESC CAN 协议 V1.0.pdf` | 501,963 | 2025-04-26 | `VESC-CM-CAN-20250331-01`, V1.0 |

The four cover pages say VESC firmware V3.00 and above and classify the protocol documents as Public. The English CAN cover says 12 pages while the Chinese CAN cover says 17; this is recorded as a document-control discrepancy. The English UART table of contents also contains stale FTESC-style command names although the body and enum use the VESC command namespace.

The documents are summarized in [FLIPSKY_VESC_PROTOCOL_V1.0.md](FLIPSKY_VESC_PROTOCOL_V1.0.md). The protocol digest records baud rate, framing, CRC, UART and CAN command IDs, payload scales, forwarding and identifier composition. The original PDFs are not duplicated in this repository.
