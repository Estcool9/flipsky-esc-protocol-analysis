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
