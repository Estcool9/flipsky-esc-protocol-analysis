# Static reverse-engineering report - Flipsky ESC Tool V1.7

## Scope
Static analysis only. The EXE was not launched, no ESC was connected, and no firmware/configuration was written to hardware. The original Nextcloud file was not modified.

## Artifact identity
- File: Flipsky_ESC_Tool_V1.7_20261029.exe
- Size: 50,611,200 bytes
- SHA-256: dba48a24cf8a65c16e752037ffa93407c0ebf9fa39883d03180db35bce557b38
- Format: PE32, x86, Windows GUI
- Image base: 0x00400000
- Entry point RVA: 0x1480 (VA 0x00401480)
- CLR header: absent in PE data directory
- Symbols: stripped

## Protection and layout
Sections named .enigma1 and .enigma2 have unusual raw/virtual-size relationships. This is consistent with a protected or packed application, and Enigma-related protection is a strong hypothesis, but section names alone do not prove protector/version. Static imports include VirtualAlloc, VirtualProtect, ReadProcessMemory, WriteProcessMemory and SetThreadContext; these support a loader/protection layer, not a malware verdict.

Rizin 0.9.1 is installed at /opt/rea-tools/releases/rizin-0.9.1/bin/rizin (not on REA service PATH). GNU objdump and Binwalk were also used. A broad Rizin full-file string pass exceeded the command window and was cancelled; it produced no evidence. Binwalk had false-positive hits; only Zlib streams independently decompressed to valid XML were retained.

## Application and transports
Static strings/imports indicate a Qt 5 / QML application. Qt modules include QtQuick, QtQuick.Controls, QtQuick.Layouts, QtCharts, Qt5SerialPort and Qt5Bluetooth. Internal modules include:
- Flipsky.ftesc.FtescLowLevelFace
- Flipsky.ftesc.ToolLib
- Flipsky.ftesc.uartcomm
- Flipsky.ftesc.valuesetups
- Flipsky.ftesc.bleuart

Observed interface paths include USB serial, BLE UART service discovery and CAN bus enumeration.

## Protocol-related method names
The binary contains these Qt meta-object/method-name strings:
- lowLevelSendDataToFtesc(QByteArray&)
- uartPackDataFromESC(QByteArray&)
- uartCommSendToFtesc(QByteArray&)
- ftescMotorSignalReadAck(QString,bool)
- ftescTopFlowSetupReadAck(QString,bool)
- ftescMotorSignalSecretKeyCheckAck(int)
- ftescGetIDResAck(QVector<int>,bool)
- ftescAutoGetRealtimeDataAck()
- ftescGetRealtimeDataOnce(FTESC_REALTIME_DATA)

These establish packet assembly, receive unpacking, ACK handlers, setup-read responses and realtime data paths. They do not reveal the frame layout, opcodes, byte order, checksum or CRC. Those remain unknown. Other identifiers include UG_FT_NUMBER, UG_MOTOR_SIGNAL_SETUP, UG_TOPFLOW_SETUP, FTESC_FIRMWARE_NUMBER and FTESC_REALTIME_DATA. Their wire-format meaning is not established.

## Embedded XML recovery
Selected Zlib streams in the resource-rich .rdata region were independently decompressed with Python zlib, bounded to 4 MiB per stream, and parsed with ElementTree. Thirteen unique XML resources with root ValueSetups were saved in embedded-xml/. Their offsets, sizes and hashes are in extraction-manifest.json.

The parameter catalogue contains 736 rows across the recovered profiles and 222 unique IDs. Duplicate IDs across profiles are expected; 736 is not the number of distinct UART commands.

Parameter families include ESC identity, multi-ESC sync, CAN, signal/control modes, UART, PPM, ADC, PAS, motor/battery currents, eRPM, phase resistance/inductance/flux, FOC gains, encoders, PWM, thermal sensing and battery cutoffs.

Selected metadata observations:
- ftesc_id: integer range 1-254. Embedded description reserves ID 0 for special instructions and ID 255 for broadcast.
- can_baud_rate: one profile shows 1000K(default), stored as value_int=3. This is an enum label, not a live bus measurement.
- canStatusFreq: default 100 Hz, integer range 0-10,000 in one profile.
- input_signal_type description lists OFF, UART, PPM, ADC and PAS. UART is documented for selected Flipsky VX remote/TFT configurations; PPM uses nominal 1-2 ms pulses; ADC input must stay below 3.3 V; PAS covers pedal sensors.
- motor_current and battery_current: one profile has an 80 A default and 800 A maximum. These are embedded metadata, not safe settings for a particular hardware setup.
- battery_cells_series: default 3, range 3-100 in one profile.
- motor_rated_current: default 50 A, range 5-500 A in one profile; its description warns to use the motor manufacturer's correct rating during identification.

Multi-ESC Sync metadata says ON allows master/slave synchronized input control and CAN commands to slaves; OFF blocks CAN control commands on a slave. For independent local UART/PPM/ADC control with CAN physically connected, the metadata advises turning this option OFF on each ESC. For a custom CAN master, it advises ON and Input Signal Type OFF.

## Firmware updater warnings
Strings describe Enter Bootloader and Start Flashing steps. The application warns that entering bootloader clears settings, that firmware must match the ESC, and that the image must not exceed 150 KiB. It states firmware update cannot be done while targeting a CAN slave; USB must connect directly to the target ESC. These are application-embedded instructions, not validation of every hardware/firmware combination.

## Next steps
1. Map XML variants to hardware/firmware profiles using firmware-version and hardware-name metadata plus supplied firmware files.
2. Inspect .text and .enigma2 with narrow Rizin/Ghidra operations; avoid repeated full-file string scans.
3. Recover references/call context around UART packet packing, unpacking and ACK handlers.
4. Compare against matching firmware or read-only UART/BLE traffic from a test ESC before assigning opcodes or checksum semantics.
5. Keep UART and CAN protocol notes separate until evidence connects them.

No UART opcode table or frame example is claimed here.
