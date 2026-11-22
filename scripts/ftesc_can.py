"""Offline, read-only decoder for the public FTESC CAN V1.4 protocol.

This module never opens a CAN interface and never transmits frames.
"""
from __future__ import annotations

from dataclasses import dataclass

from scripts.ftesc_frame import crc16_modbus

CAN_EID_MASK = 0x1FFFFFFF
CAN_FIXED_MASK = 0x1FFF0000
CAN_FIXED_VALUE = 0x10000000

CAN_ESC_REALTIME_DATA_0 = 0x0B
CAN_ESC_REALTIME_DATA_1 = 0x0C
CAN_ESC_REALTIME_DATA_2 = 0x0D


@dataclass(frozen=True, slots=True)
class CanIdentifier:
    raw: int
    esc_id: int
    command: int


@dataclass(frozen=True, slots=True)
class CanFrame:
    identifier: CanIdentifier
    data: bytes
    crc_valid: bool | None


@dataclass(frozen=True, slots=True)
class CanRealtimeData0:
    esc_id: int
    motor_current_a: float
    battery_current_a: float


@dataclass(frozen=True, slots=True)
class CanRealtimeData1:
    esc_id: int
    motor_erpm: int
    duty: float


@dataclass(frozen=True, slots=True)
class CanRealtimeData2:
    esc_id: int
    mosfet_temperature_c: float
    motor_temperature_c: float
    battery_voltage_v: float


def decode_can_identifier(identifier: int) -> CanIdentifier:
    """Decode the 29-bit extended ID documented by FTESC CAN V1.4."""
    if not isinstance(identifier, int) or not 0 <= identifier <= CAN_EID_MASK:
        raise ValueError("CAN identifier must be an unsigned 29-bit integer")
    if identifier & CAN_FIXED_MASK != CAN_FIXED_VALUE:
        raise ValueError("CAN identifier does not match the FTESC extended-ID prefix")
    return CanIdentifier(
        raw=identifier,
        esc_id=(identifier >> 8) & 0xFF,
        command=identifier & 0xFF,
    )


def encode_can_identifier(esc_id: int, command: int) -> int:
    """Build an FTESC extended ID; this does not transmit anything."""
    if not 0 <= esc_id <= 0xFF:
        raise ValueError("ESC ID must fit in one byte")
    if not 0 <= command <= 0xFF:
        raise ValueError("CAN command must fit in one byte")
    return CAN_FIXED_VALUE | (esc_id << 8) | command


def parse_can_frame(identifier: int, data: bytes | bytearray | memoryview) -> CanFrame:
    """Decode the ID and validate the payload CRC where V1.4 defines one."""
    ident = decode_can_identifier(identifier)
    payload = bytes(data)
    # V1.4 defines CRC-bearing commands 00-05, 0B-0D and 12-14.
    has_crc = (
        0x00 <= ident.command <= 0x05
        or 0x0B <= ident.command <= 0x0D
        or 0x12 <= ident.command <= 0x14
    )
    if not has_crc:
        return CanFrame(ident, payload, None)
    if len(payload) < 2:
        raise ValueError("CRC-bearing FTESC CAN command is shorter than its CRC")
    expected = int.from_bytes(payload[-2:], "big")
    actual = crc16_modbus(payload[:-2])
    return CanFrame(ident, payload, expected == actual)


def _signed_i24(data: bytes, offset: int) -> int:
    value = int.from_bytes(data[offset:offset + 3], "big", signed=False)
    return value - 0x1000000 if value & 0x800000 else value


def decode_realtime_data(
    identifier: int, data: bytes | bytearray | memoryview
) -> CanRealtimeData0 | CanRealtimeData1 | CanRealtimeData2:
    """Decode one of the three periodic 8-byte CAN telemetry frames."""
    frame = parse_can_frame(identifier, data)
    if frame.crc_valid is not True:
        raise ValueError("FTESC CAN telemetry CRC mismatch")
    d = frame.data
    if len(d) != 8:
        raise ValueError(f"FTESC CAN telemetry frame requires 8 data bytes, got {len(d)}")
    cmd = frame.identifier.command
    esc_id = frame.identifier.esc_id
    if cmd == CAN_ESC_REALTIME_DATA_0:
        return CanRealtimeData0(
            esc_id=esc_id,
            motor_current_a=_signed_i24(d, 0) / 1000.0,
            battery_current_a=_signed_i24(d, 3) / 1000.0,
        )
    if cmd == CAN_ESC_REALTIME_DATA_1:
        return CanRealtimeData1(
            esc_id=esc_id,
            motor_erpm=_signed_i24(d, 0),
            duty=_signed_i24(d, 3) / 1000.0,
        )
    if cmd == CAN_ESC_REALTIME_DATA_2:
        return CanRealtimeData2(
            esc_id=esc_id,
            mosfet_temperature_c=int.from_bytes(d[0:2], "big", signed=True) / 100.0,
            motor_temperature_c=int.from_bytes(d[2:4], "big", signed=True) / 100.0,
            battery_voltage_v=int.from_bytes(d[4:6], "big", signed=True) / 100.0,
        )
    raise ValueError(f"unsupported FTESC CAN telemetry command 0x{cmd:02X}")
