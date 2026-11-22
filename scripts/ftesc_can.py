"""Offline codec for the public FTESC CAN V1.4 protocol.

This module builds/decodes byte structures only. It never opens a CAN
interface and never transmits frames.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

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


# V1.4 direct-CAN control command identifiers.
CAN_SET_CURRENT_GEAR_CRC16 = 0x00
CAN_SET_BRAKE_CURRENT_CRC16 = 0x01
CAN_SET_DUTY_GEAR_CRC16 = 0x02
CAN_SET_CURRENT_PERCENT_CRC16 = 0x03
CAN_SET_CURRENT_PERCENT_GEAR_CRC16 = 0x04
CAN_SET_BRAKE_CURRENT_PERCENT_CRC16 = 0x05
CAN_SET_ERPM_GEAR_CRC16 = 0x12
CAN_SET_POSITION_GEAR_CRC16 = 0x13
CAN_SET_ID_CURRENT_CRC16 = 0x14

CAN_SET_CURRENT_GEAR = 0x15
CAN_SET_CURRENT_PERCENT_GEAR = 0x16
CAN_SET_DUTY_GEAR = 0x17
CAN_SET_ERPM_GEAR = 0x18
CAN_SET_POSITION_GEAR = 0x19
CAN_SET_BRAKE_CURRENT = 0x1A
CAN_SET_BRAKE_CURRENT_PERCENT = 0x1B


def _can_i32(value: int) -> bytes:
    if isinstance(value, bool) or not isinstance(value, int) or not -(1 << 31) <= value < (1 << 31):
        raise ValueError("CAN scalar must fit signed int32")
    return value.to_bytes(4, "big", signed=True)


def _can_scaled_i32(value: int | float, scale: int, label: str) -> bytes:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{label} must be finite")
    # The V1.4 sample's float-to-integer helper uses a C integer cast
    # (truncate toward zero), unlike the V1.7 UART scalar helpers.
    return _can_i32(int(numeric * scale))


def _can_gear(gear: int) -> bytes:
    if isinstance(gear, bool) or not isinstance(gear, int) or not 0 <= gear <= 4:
        raise ValueError("gear must be an integer in 0..4")
    return bytes((gear,))


def _build_crc_can_frame(esc_id: int, command: int, payload: bytes) -> CanFrame:
    if len(payload) + 2 > 8:
        raise ValueError("CAN payload plus CRC exceeds the 8-byte classic CAN limit")
    crc = crc16_modbus(payload).to_bytes(2, "big")
    raw_id = encode_can_identifier(esc_id, command)
    ident = CanIdentifier(raw=raw_id, esc_id=esc_id, command=command)
    return CanFrame(identifier=ident, data=payload + crc, crc_valid=True)


def _build_plain_can_frame(esc_id: int, command: int, payload: bytes) -> CanFrame:
    if len(payload) > 8:
        raise ValueError("CAN payload exceeds the 8-byte classic CAN limit")
    raw_id = encode_can_identifier(esc_id, command)
    ident = CanIdentifier(raw=raw_id, esc_id=esc_id, command=command)
    return CanFrame(identifier=ident, data=payload, crc_valid=None)


def build_can_current_gear_crc16(esc_id: int, current: int | float, gear: int) -> CanFrame:
    return _build_crc_can_frame(
        esc_id, CAN_SET_CURRENT_GEAR_CRC16,
        _can_scaled_i32(current, 100_000, "current") + _can_gear(gear),
    )


def build_can_brake_current_crc16(esc_id: int, current: int | float) -> CanFrame:
    return _build_crc_can_frame(
        esc_id, CAN_SET_BRAKE_CURRENT_CRC16,
        _can_scaled_i32(current, 100_000, "brake current"),
    )


def build_can_duty_gear_crc16(esc_id: int, duty: int | float, gear: int) -> CanFrame:
    return _build_crc_can_frame(
        esc_id, CAN_SET_DUTY_GEAR_CRC16,
        _can_scaled_i32(duty, 1_000_000, "duty") + _can_gear(gear),
    )


def build_can_current_percent_crc16(esc_id: int, percent: int | float) -> CanFrame:
    return _build_crc_can_frame(
        esc_id, CAN_SET_CURRENT_PERCENT_CRC16,
        _can_scaled_i32(percent, 100_000, "current percent"),
    )


def build_can_current_percent_gear_crc16(
    esc_id: int, percent: int | float, gear: int
) -> CanFrame:
    return _build_crc_can_frame(
        esc_id, CAN_SET_CURRENT_PERCENT_GEAR_CRC16,
        _can_scaled_i32(percent, 100_000, "current percent") + _can_gear(gear),
    )


def build_can_brake_current_percent_crc16(
    esc_id: int, percent: int | float
) -> CanFrame:
    return _build_crc_can_frame(
        esc_id, CAN_SET_BRAKE_CURRENT_PERCENT_CRC16,
        _can_scaled_i32(percent, 100_000, "brake current percent"),
    )


def build_can_erpm_gear_crc16(esc_id: int, erpm: int, gear: int) -> CanFrame:
    return _build_crc_can_frame(
        esc_id, CAN_SET_ERPM_GEAR_CRC16, _can_i32(erpm) + _can_gear(gear)
    )


def build_can_position_gear_crc16(
    esc_id: int, position: int | float, gear: int
) -> CanFrame:
    return _build_crc_can_frame(
        esc_id, CAN_SET_POSITION_GEAR_CRC16,
        _can_scaled_i32(position, 100_000, "position") + _can_gear(gear),
    )


def build_can_id_current_crc16(esc_id: int, current: int | float) -> CanFrame:
    return _build_crc_can_frame(
        esc_id, CAN_SET_ID_CURRENT_CRC16,
        _can_scaled_i32(current, 100_000, "D-axis current") + bytes((0,)),
    )


def build_can_current_gear(esc_id: int, current: int | float, gear: int) -> CanFrame:
    return _build_plain_can_frame(
        esc_id, CAN_SET_CURRENT_GEAR,
        _can_scaled_i32(current, 100_000, "current") + _can_gear(gear),
    )


def build_can_current_percent_gear(
    esc_id: int, percent: int | float, gear: int
) -> CanFrame:
    return _build_plain_can_frame(
        esc_id, CAN_SET_CURRENT_PERCENT_GEAR,
        _can_scaled_i32(percent, 100_000, "current percent") + _can_gear(gear),
    )


def build_can_duty_gear(esc_id: int, duty: int | float, gear: int) -> CanFrame:
    return _build_plain_can_frame(
        esc_id, CAN_SET_DUTY_GEAR,
        _can_scaled_i32(duty, 1_000_000, "duty") + _can_gear(gear),
    )


def build_can_erpm_gear(esc_id: int, erpm: int, gear: int) -> CanFrame:
    return _build_plain_can_frame(
        esc_id, CAN_SET_ERPM_GEAR, _can_i32(erpm) + _can_gear(gear)
    )


def build_can_position_gear(
    esc_id: int, position: int | float, gear: int
) -> CanFrame:
    return _build_plain_can_frame(
        esc_id, CAN_SET_POSITION_GEAR,
        _can_scaled_i32(position, 100_000, "position") + _can_gear(gear),
    )


def build_can_brake_current(esc_id: int, current: int | float) -> CanFrame:
    return _build_plain_can_frame(
        esc_id, CAN_SET_BRAKE_CURRENT,
        _can_scaled_i32(current, 100_000, "brake current"),
    )


def build_can_brake_current_percent(
    esc_id: int, percent: int | float
) -> CanFrame:
    return _build_plain_can_frame(
        esc_id, CAN_SET_BRAKE_CURRENT_PERCENT,
        _can_scaled_i32(percent, 100_000, "brake current percent"),
    )
