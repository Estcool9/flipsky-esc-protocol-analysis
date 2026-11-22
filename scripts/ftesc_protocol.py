"""Offline helpers for the documented Flipsky FT ESC UART command layer.

This module only builds/parses byte buffers. It opens no serial/BLE connection
and does not transmit commands to a physical ESC.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import math


class CommandId(IntEnum):
    OBTAIN_DATA_ONCE = 0x00
    OBTAIN_ID_OVER_CAN = 0x01
    CONTROL_AND_OBTAIN_DATA_ONCE = 0x02
    PAS_GEAR_CONTROL_AND_OBTAIN_DATA_ONCE = 0x02  # same ID; firmware mode selects meaning
    SET_DUTY = 0x03
    SET_CURRENT = 0x04
    SET_CURRENT_GEAR = 0x05
    SET_BRAKE_CURRENT = 0x06
    CAN_FORWARD = 0x10
    OBTAIN_FIRMWARE_VERSION = 0x11
    KEEP_LIVE = 0x19
    SET_AUTO_OBTAIN_REALTIME_DATA = 0x1A
    RESET_AND_REBOOT = 0x1D
    OBTAIN_ALL_ESC_IDS = 0x1E
    SET_CURRENT_GEAR_AND_OBTAIN_DATA = 0x20
    REBOOT = 0x23
    SET_ID_CURRENT = 0x25
    SET_POSITION = 0x26
    SET_SPEED = 0x27


@dataclass(frozen=True, slots=True)
class CommandMessage:
    command: int
    data: bytes


@dataclass(frozen=True, slots=True)
class RealtimeDataV16:
    controller_id: int
    error_code: int
    battery_voltage_v: float
    battery_current_a: float
    motor_current_a: float
    motor_erpm: int
    duty_cycle: float
    mosfet_temperature_c: float
    motor_temperature_c: float
    cpu_utilization: float
    encoder_angle_degrees: float
    reserved_extension: bytes = b""
    pas_rpm: int | None = None


@dataclass(frozen=True, slots=True)
class RealtimeDataV17Extension:
    """V1.7 values occupying the 16-byte extension to CMD 0x00 DATA."""
    angular_value_1_degrees: float
    angular_value_2_degrees: float
    angular_value_3_degrees: float
    pas_rpm: int


@dataclass(frozen=True, slots=True)
class MotorTelemetryV16:
    error_code: int
    battery_voltage_v: float
    battery_current_a: float
    motor_current_a: float
    motor_erpm: int
    duty_cycle: float
    mosfet_temperature_c: float
    motor_temperature_c: float
    cpu_utilization: float
    encoder_angle_degrees: float
    pas_rpm: int | None = None


def _signed(data: bytes, offset: int, size: int) -> int:
    if offset < 0 or offset + size > len(data):
        raise ValueError("field exceeds available command data")
    return int.from_bytes(data[offset:offset + size], "big", signed=True)


def _unsigned(data: bytes, offset: int, size: int) -> int:
    if offset < 0 or offset + size > len(data):
        raise ValueError("field exceeds available command data")
    return int.from_bytes(data[offset:offset + size], "big", signed=False)


def build_info(command: int | CommandId, data: bytes = b"") -> bytes:
    """Build the INFO field (CMD + DATA), without the outer UART frame."""
    command_value = int(command)
    if not 0 <= command_value <= 0xFF:
        raise ValueError("command ID must fit in one byte")
    return bytes((command_value,)) + bytes(data)


def encode_command(command: int | CommandId, data: bytes = b"") -> bytes:
    """Build an offline UART frame for CMD + DATA using the outer frame codec."""
    from scripts.ftesc_frame import encode_frame

    return encode_frame(build_info(command, data))


def parse_info(info: bytes | bytearray | memoryview) -> CommandMessage:
    """Split a validated INFO field into its command byte and DATA."""
    raw = bytes(info)
    if not raw:
        raise ValueError("INFO must contain at least the one-byte CMD")
    return CommandMessage(raw[0], raw[1:])


def decode_command_frame(wire: bytes | bytearray | memoryview, *, offset: int = 0):
    """Decode one outer frame then split its INFO field into CMD and DATA."""
    from scripts.ftesc_frame import decode_frame

    frame = decode_frame(wire, offset=offset)
    return frame, parse_info(frame.payload)


def parse_realtime_data_00(info: bytes | bytearray | memoryview) -> RealtimeDataV16:
    """Parse UART_OBTAIN_DATA_ONCE (00H) response from the V1.6 specification.

    INFO length includes CMD. 29 bytes is the base response; 45 bytes is the
    automatic-report extension, containing 12 reserved bytes and a 32-bit
    PAS RPM value. The optional fields are not assumed present in every reply.
    """
    message = parse_info(info)
    if message.command != CommandId.OBTAIN_DATA_ONCE:
        raise ValueError(f"expected CMD 0x00, got 0x{message.command:02X}")
    d = message.data
    if len(d) not in (28, 44):
        raise ValueError(
            f"V1.6 CMD 0x00 DATA must be 28 or 44 bytes, got {len(d)}"
        )

    return RealtimeDataV16(
        controller_id=d[0],
        error_code=d[1],
        battery_voltage_v=_signed(d, 2, 2) / 100.0,
        battery_current_a=_signed(d, 4, 4) / 1_000_000.0,
        motor_current_a=_signed(d, 8, 4) / 1_000_000.0,
        motor_erpm=_signed(d, 12, 4),
        duty_cycle=_signed(d, 16, 2) / 10_000.0,
        mosfet_temperature_c=_signed(d, 18, 2) / 100.0,
        motor_temperature_c=_signed(d, 20, 2) / 100.0,
        cpu_utilization=_signed(d, 22, 2) / 10_000.0,
        encoder_angle_degrees=_signed(d, 24, 4) / 1_000_000.0,
        reserved_extension=d[28:40] if len(d) == 44 else b"",
        pas_rpm=_signed(d, 40, 4) if len(d) == 44 else None,
    )


def parse_realtime_data_00_v17_angular_extension(
    info: bytes | bytearray | memoryview,
) -> tuple[float, float, float]:
    """Decode the three V1.7 angular values occupying V1.6's 12 reserved bytes.

    The V1.7 binary reads each as a signed 32-bit big-endian integer, divides
    by 1,000,000 to obtain radians, then converts radians to degrees.
    """
    message = parse_info(info)
    if message.command != CommandId.OBTAIN_DATA_ONCE:
        raise ValueError(f"expected CMD 0x00, got 0x{message.command:02X}")
    d = message.data
    if len(d) != 44:
        raise ValueError(f"V1.7 CMD 0x00 angular extension requires 44 DATA bytes, got {len(d)}")
    return tuple(
        math.degrees(_signed(d, offset, 4) / 1_000_000.0)
        for offset in (28, 32, 36)
    )


def parse_realtime_data_00_v17_extension(
    info: bytes | bytearray | memoryview,
) -> RealtimeDataV17Extension:
    """Decode the 16-byte V1.7 extension of CMD 0x00 DATA.

    Native V1.7 response code reads three signed 32-bit big-endian values
    scaled from microradians to degrees, followed by one signed 32-bit
    big-endian PAS-RPM value. The three angular values' semantic labels
    are not identified by the executable's UI/API metadata yet.
    """
    message = parse_info(info)
    if message.command != CommandId.OBTAIN_DATA_ONCE:
        raise ValueError(f"expected CMD 0x00, got 0x{message.command:02X}")
    d = message.data
    if len(d) != 44:
        raise ValueError(f"V1.7 CMD 0x00 extension requires 44 DATA bytes, got {len(d)}")
    angles = tuple(
        math.degrees(_signed(d, offset, 4) / 1_000_000.0)
        for offset in (28, 32, 36)
    )
    return RealtimeDataV17Extension(
        angular_value_1_degrees=angles[0],
        angular_value_2_degrees=angles[1],
        angular_value_3_degrees=angles[2],
        pas_rpm=_signed(d, 40, 4),
    )


def parse_motor_telemetry_02_or_20(
    info: bytes | bytearray | memoryview,
) -> MotorTelemetryV16:
    """Parse the common telemetry response for CMD 02H or 20H.

    The V1.6 PAS-mode section also lists D27-D30 as PAS RPM, although it leaves
    DLEN at 1CH (the length for only D0-D26 plus CMD). This function accepts
    the base 28-byte INFO or the 32-byte INFO needed to carry that extra field.
    """
    message = parse_info(info)
    if message.command not in (CommandId.CONTROL_AND_OBTAIN_DATA_ONCE,
                                CommandId.SET_CURRENT_GEAR_AND_OBTAIN_DATA):
        raise ValueError(f"expected CMD 0x02 or 0x20, got 0x{message.command:02X}")
    d = message.data
    if len(d) not in (27, 31):
        raise ValueError(
            f"CMD 0x02/0x20 DATA must be 27 bytes, or 31 with PAS RPM; got {len(d)}"
        )
    return MotorTelemetryV16(
        error_code=d[0],
        battery_voltage_v=_signed(d, 1, 2) / 100.0,
        battery_current_a=_signed(d, 3, 4) / 1_000_000.0,
        motor_current_a=_signed(d, 7, 4) / 1_000_000.0,
        motor_erpm=_signed(d, 11, 4),
        duty_cycle=_signed(d, 15, 2) / 10_000.0,
        mosfet_temperature_c=_signed(d, 17, 2) / 100.0,
        motor_temperature_c=_signed(d, 19, 2) / 100.0,
        cpu_utilization=_signed(d, 21, 2) / 10_000.0,
        encoder_angle_degrees=_signed(d, 23, 4) / 1_000_000.0,
        pas_rpm=_signed(d, 27, 4) if len(d) == 31 else None,
    )


def parse_all_esc_ids(info: bytes | bytearray | memoryview) -> tuple[int, tuple[int, ...]]:
    """Parse CMD 1EH response: master ESC ID followed by zero or more slave IDs."""
    message = parse_info(info)
    if message.command not in (CommandId.OBTAIN_ID_OVER_CAN, CommandId.OBTAIN_ALL_ESC_IDS):
        raise ValueError(f"expected CMD 0x01 or 0x1E, got 0x{message.command:02X}")
    if not message.data:
        raise ValueError("CMD 0x1E response must include the master ESC ID")
    return message.data[0], tuple(message.data[1:])


def parse_auto_realtime_config(info: bytes | bytearray | memoryview) -> tuple[int, int, int]:
    """Parse CMD 1AH response as (enable_marker, frequency_hz, function_address)."""
    message = parse_info(info)
    if message.command != CommandId.SET_AUTO_OBTAIN_REALTIME_DATA:
        raise ValueError(f"expected CMD 0x1A, got 0x{message.command:02X}")
    if len(message.data) != 7:
        raise ValueError(f"CMD 0x1A response DATA must be 7 bytes, got {len(message.data)}")
    return message.data[0], _unsigned(message.data, 1, 2), _unsigned(message.data, 3, 4)
