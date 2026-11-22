"""Offline decoders for V1.7 response payloads with recovered field layouts."""
from __future__ import annotations

from dataclasses import dataclass

from scripts.ftesc_protocol import parse_info


@dataclass(frozen=True, slots=True)
class SignalAdcResponse:
    """Six native ADC values; semantic channel labels are not yet established."""
    values: tuple[float, float, float, float, float, float]


@dataclass(frozen=True, slots=True)
class ImuCalibrationResponse:
    """Nine native calibration scalars; semantic axis labels are not yet established."""
    values: tuple[float, float, float, float, float, float, float, float, float]


@dataclass(frozen=True, slots=True)
class BooleanAck:
    command: int
    success: bool


def _signed_i32(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise ValueError("response field exceeds available DATA")
    return int.from_bytes(data[offset:offset + 4], "big", signed=True)


def parse_signal_ppm_response(info: bytes | bytearray | memoryview) -> float:
    """Decode CMD 0x0D: one signed int32 scaled by 1,000,000."""
    message = parse_info(info)
    if message.command != 0x0D:
        raise ValueError(f"expected CMD 0x0D, got 0x{message.command:02X}")
    if len(message.data) != 4:
        raise ValueError(f"CMD 0x0D DATA must be 4 bytes, got {len(message.data)}")
    return _signed_i32(message.data, 0) / 1_000_000.0


def parse_signal_adc_response(
    info: bytes | bytearray | memoryview,
) -> SignalAdcResponse:
    """Decode CMD 0x0E: six signed int32 values with scales 1e6,1e6,1,1,1,1e6."""
    message = parse_info(info)
    if message.command != 0x0E:
        raise ValueError(f"expected CMD 0x0E, got 0x{message.command:02X}")
    if len(message.data) != 24:
        raise ValueError(f"CMD 0x0E DATA must be 24 bytes, got {len(message.data)}")
    scales = (1_000_000.0, 1_000_000.0, 1.0, 1.0, 1.0, 1_000_000.0)
    values = tuple(
        _signed_i32(message.data, offset) / scales[index]
        for index, offset in enumerate(range(0, 24, 4))
    )
    return SignalAdcResponse(values=values)  # type: ignore[arg-type]


def parse_boolean_ack(
    info: bytes | bytearray | memoryview, expected_command: int
) -> BooleanAck:
    """Decode one-byte boolean acknowledgement for CMD 0x16, 0x18 or 0x22."""
    if expected_command not in (0x16, 0x18, 0x22):
        raise ValueError("supported boolean ACK commands are 0x16, 0x18 and 0x22")
    message = parse_info(info)
    if message.command != expected_command:
        raise ValueError(
            f"expected CMD 0x{expected_command:02X}, got 0x{message.command:02X}"
        )
    if len(message.data) != 1:
        raise ValueError(f"CMD 0x{expected_command:02X} ACK DATA must be 1 byte")
    return BooleanAck(command=message.command, success=message.data[0] != 0)


def parse_auto_realtime_ack(info: bytes | bytearray | memoryview) -> None:
    """Validate the no-DATA CMD 0x1A acknowledgement."""
    message = parse_info(info)
    if message.command != 0x1A:
        raise ValueError(f"expected CMD 0x1A, got 0x{message.command:02X}")
    if message.data:
        raise ValueError(f"CMD 0x1A acknowledgement must have no DATA, got {len(message.data)}")
    return None


def parse_imu_calibration_response(
    info: bytes | bytearray | memoryview,
) -> ImuCalibrationResponse:
    """Decode CMD 0x29: nine signed int32 values divided by 1,000,000."""
    message = parse_info(info)
    if message.command != 0x29:
        raise ValueError(f"expected CMD 0x29, got 0x{message.command:02X}")
    if len(message.data) != 36:
        raise ValueError(f"CMD 0x29 DATA must be 36 bytes, got {len(message.data)}")
    values = tuple(
        _signed_i32(message.data, offset) / 1_000_000.0
        for offset in range(0, 36, 4)
    )
    return ImuCalibrationResponse(values=values)  # type: ignore[arg-type]


def parse_uuid_response(info: bytes | bytearray | memoryview) -> bytes:
    """Return raw CMD 0x21 UUID DATA as emitted by the native QByteArray signal.

    The firmware-update TEA preflight uses a 16-byte key, but the native
    response dispatcher copies the QByteArray without a visible 16-byte
    length check. This decoder therefore preserves the raw length.
    """
    message = parse_info(info)
    if message.command != 0x21:
        raise ValueError(f"expected CMD 0x21, got 0x{message.command:02X}")
    return bytes(message.data)
