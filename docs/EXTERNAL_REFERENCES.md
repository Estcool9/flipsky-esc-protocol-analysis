# External references and cross-checks

Research checked on 2026-11-22. External references are used for product-family context and protocol comparison; reverse-engineered V1.7 facts remain grounded in the local binary and are documented separately.

## Flipsky official sources

1. **Differences Between FT ESC and FSESC** — 9 January 2026  
   https://flipsky.net/blogs/vesc-tool/differences-between-ft-esc-and-fsesc  
   Flipsky describes FSESC as its VESC-based family and FT ESC as NON-VESC, independently developed and intended for Flipsky ESC Tool. The article says the product families and programming tools are not interchangeable.

2. **How to Update FT Series ESC to V1.6** — 24 March 2026  
   https://flipsky.net/blogs/vesc-tool/how-to-update-ft-series-esc-to-v16  
   Official FT-series update procedure: connect via USB, enter bootloader, reconnect, start flashing, and update master/slave controllers separately on dual-drive systems. The article also notes saved `motor_conf` and `control_conf` settings in V1.6.

3. **Flipsky FTESC Gateway Interface Module**  
   https://flipsky.net/products/flipsky-ftesc-gateway-interface-module-multi-esc-networked-cooperative-control-for-ftesc-series  
   Product page references the FTESC V1.6 manual and describes CAN-based multi-ESC operation. The linked PDF was not retrievable through the research browser during this session.

## VESC primary sources

4. **Benjamin Vedder — Communicating with the VESC using UART**  
   https://vedder.se/2015/10/communicating-with-the-vesc-using-uart/  
   Documents the standard VESC UART frame: start byte 2/3, length, payload, CRC and stop byte 3.

5. **VESC Tool — packet.h**  
   https://github.com/vedderb/vesc_tool/blob/master/packet.h  
   Primary source for the VESC Tool packet encoder/decoder interface and packet signals.

6. **VESC firmware — datatypes.h**  
   https://github.com/vedderb/bldc/blob/master/datatypes.h  
   Primary source for standard VESC communication command IDs, including FW version 0, bootloader 1, erase 2, write 3, GET_VALUES 4, SET_DUTY 5, SET_CURRENT 6, brake current 7, RPM 8 and position 9.

7. **VESC Tool — vescinterface.cpp**  
   https://github.com/vedderb/vesc_tool/blob/master/vescinterface.cpp  
   Shows the VESC Tool transport abstraction for serial, CAN, TCP/UDP, virtual and BLE transports.

## Conclusions supported by these references

- The user's intuition that the tools are similar is valid at the product and UI level.
- Flipsky's own product-family description distinguishes FT ESC from FSESC/VESC and says their tools are not interchangeable.
- The V1.7 binary's AA/BB framing and DD terminator differ from the standard VESC 02/03 framing and 03 terminator.
- The V1.7 request command IDs differ from the standard VESC `COMM_PACKET_ID` enumeration; some numeric values collide but mean different things.
- VESC Tool source is useful for architectural comparison, not as the FTESC protocol implementation.

## Limitations

- The official Flipsky V1.6 manual PDF linked from the product page was not accessible in the web research environment. The local extracted protocol document remains the basis for detailed V1.6 command cross-checks.
- No external source was used to infer undocumented V1.7 payload fields; those are derived from the executable's native code.


8. **Flipsky FTESC Gateway Interface Module — official product page**  
   https://flipsky.net/collections/new-arrival/products/flipsky-ftesc-gateway-interface-module-multi-esc-networked-cooperative-control-for-ftesc-series  
   Describes FTESC Gateway firmware V1.6+, USB/CAN/UART/PPM/ADC interfaces, USB passthrough to address a specific ESC by CAN ID, unique-ID and common-baud requirements. The linked V1.6 manual PDF was visible on the product page but could not be retrieved by the research browser in this session.

9. **Flipsky FT110120A WP product page**  
   https://flipsky.net/collections/non-vesc/products/flipsky-ft110120a-wp-ip68-waterproof-110v-120a-brushless-esc-speed-controller-for-e-foil-electric-surfboard-underwater-thruster-rc-boat-e-skateboard-e-bike  
   Lists firmware V1.7 and above, Flipsky ESC Tool, and USB/CAN/UART/PPM/ADC communication ports. This is a product-specific example, not evidence that all FTESC SKUs use identical parameter tables.


## Pinned VESC source comparison snapshots

10. **VESC Tool source repository, pinned commit**  
    https://github.com/vedderb/vesc_tool/commit/04614bf50909b78f23716af694bf19ab9745e7df  
    Inspected `packet.cpp`, `commands.cpp`, `datatypes.h`, `bleuart.cpp` and `LICENSE` at the pinned revision. This revision is dated 2026-11-21 and declares GPL-3.0.

11. **VESC firmware repository, pinned commit**  
    https://github.com/vedderb/bldc/commit/6fda11c299a475d5e6a6d1c5f5efd2539643d70b  
    Inspected firmware `datatypes.h`, `comm/comm_can.c`, `comm/commands.c`, and `documentation/comm_can.md` for CAN IDs, command payloads, extended identifier composition and COMM_FORWARD_CAN behavior. This revision is dated 2026-11-21.

Machine-readable source/file digests are recorded in [vesc-reference-manifest.json](../analysis-data/vesc-reference-manifest.json). The full comparison is in [VESC_COMPARISON.md](VESC_COMPARISON.md).


## Flipsky VESC V1.0 protocol PDFs supplied through Nextcloud

12. **Flipsky VESC UART Communication Protocol V1.0 (English)**  
    User-provided file: `VESC UART Protocol V1.0.pdf`  
    Document number `VESC-CM-UART-20250331-01`; issue date 2025-04-15; VESC firmware V3.00 and above; cover marks Public.

13. **Flipsky VESC UART Communication Protocol V1.0 (Chinese)**  
    User-provided file: `VESC UART 协议 V1.0.pdf`  
    Same document number/date/version as the English UART copy. Its command-body table of contents is consistent with the VESC command namespace.

14. **Flipsky VESC CAN Communication Protocol V1.0 (English)**  
    User-provided file: `VESC CAN Protocol V1.0.pdf`  
    Document number `VESC-CM-CAN-20250331-01`; issue date 2025-04-15; VESC firmware V3.00 and above; English cover states 12 pages.

15. **Flipsky VESC CAN Communication Protocol V1.0 (Chinese)**  
    User-provided file: `VESC CAN 协议 V1.0.pdf`  
    Same CAN document number/date/version; Chinese cover says 17 pages. The English/Chinese cover page count discrepancy is recorded as an editorial issue only.

The four PDFs were read through the user's connected Nextcloud files and cover pages visually inspected. The protocol digest and discrepancies are recorded in [FLIPSKY_VESC_PROTOCOL_V1.0.md](FLIPSKY_VESC_PROTOCOL_V1.0.md). The original PDFs are not committed to this repository.

## Flipsky current family/gateway references checked 2026-11-22

16. **Differences Between FT ESC and FSESC** — 9 January 2026  
    https://flipsky.net/blogs/vesc-tool/differences-between-ft-esc-and-fsesc  
    Flipsky explicitly identifies FT ESC as NON-VESC and FSESC as VESC-based and says their programming tools are not interchangeable.

17. **What Is a CAN Gateway?** — 20 November 2026  
    https://flipsky.net/blogs/vesc-tool/what-is-a-can-gateway  
    Describes distinct FTESC and FSESC gateway products: FTESC Gateway is for non-VESC FTESC controllers and uses Flipsky ESC Tool; FSESC Gateway is for VESC-based controllers and uses VESC Tool. The article notes that the FTESC control mode must be OFF when the FTESC Gateway drives control through its CAN interface, to avoid competing control sources. This is product guidance, not a substitute for the missing native V1.7 command path.

## Reusable analysis workflow

18. **REA / Rizin / Ghidra toolchain**  
    The analysis host already has Ghidra 12.2 and Rizin 0.9.1 available through REA/Gateway. No new paid disassembler was installed. The repeatable static workflow is documented in [RE_WORKFLOW.md](RE_WORKFLOW.md); the generic bounded zlib XML scanner is in [`scripts/scan_compressed_xml.py`](../scripts/scan_compressed_xml.py).
