"""Offline decoders for V1.6/V1.7 FTESC response payloads with recovered field layouts."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Mapping
from typing import Any

from scripts.ftesc_protocol import parse_info
from scripts.ftesc_setup_serializer import DecodedSetupBlock, SetupValueError, decode_profile_block
from scripts.ftesc_requests import MOTOR_SETUP_MARKER, MOTOR_SIGNAL_SETUP_MARKER, TOPFLOW_SETUP_MARKER


@dataclass(frozen=True, slots=True)
class SignalAdcResponse:
    """Six native ADC values; semantic channel labels are not yet established."""
    values: tuple[float, float, float, float, float, float]


@dataclass(frozen=True, slots=True)
class ImuCalibrationResponse:
    """Nine native calibration scalars; semantic axis labels are not yet established."""
    values: tuple[float, float, float, float, float, float, float, float, float]


@dataclass(frozen=True, slots=True)
class CanForwardResponse:
    slave_command: int
    slave_data: bytes


@dataclass(frozen=True, slots=True)
class EscIdEnumerationResponse:
    """CMD 0x1E: first DATA byte is master ID, remaining bytes are slave IDs."""
    master_id: int | None
    slave_ids: tuple[int, ...]
    raw_ids: bytes


@dataclass(frozen=True, slots=True)
class MotorSignalSetupResponse:
    first_block: DecodedSetupBlock
    second_block: DecodedSetupBlock
    secret_key_status: int
    success: bool


@dataclass(frozen=True, slots=True)
class SingleSetupProfileResponse:
    """One marker-prefixed V1.6 setup profile response.

    Any bytes not consumed by the known ValueSeque are preserved verbatim.
    """
    command: int
    block: DecodedSetupBlock
    trailing_data: bytes


@dataclass(frozen=True, slots=True)
class TopFlowSetupResponse:
    block: DecodedSetupBlock
    secret_key_status: int
    success: bool


@dataclass(frozen=True, slots=True)
class SetupWriteAck:
    command: int
    acknowledged: bool = True


@dataclass(frozen=True, slots=True)
class TextResponse:
    command: int
    raw: bytes
    text: str


@dataclass(frozen=True, slots=True)
class MotorIdentifyResponse:
    label_raw: bytes
    label: str
    success: bool


@dataclass(frozen=True, slots=True)
class FirmwareVersionResponse:
    major: int
    minor: int
    boot_mode_flag: int
    hardware_name_raw: bytes
    hardware_name: str
    hardware_serial_number: int

    @property
    def firmware_type(self) -> int:
        return self.boot_mode_flag

    @property
    def label_raw(self) -> bytes:
        return self.hardware_name_raw

    @property
    def label(self) -> str:
        return self.hardware_name

    @property
    def suffix_byte(self) -> int:
        return self.hardware_serial_number


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


def parse_text_response(
    info: bytes | bytearray | memoryview, expected_command: int
) -> TextResponse:
    """Decode UTF-8 text responses CMD 0x14 (terminal) and CMD 0x24 (samples)."""
    if expected_command not in (0x14, 0x24):
        raise ValueError("text responses are supported for CMD 0x14 and 0x24")
    message = parse_info(info)
    if message.command != expected_command:
        raise ValueError(
            f"expected CMD 0x{expected_command:02X}, got 0x{message.command:02X}"
        )
    raw = bytes(message.data)
    # The native V1.6 CMD 0x14 path scans a C-style string only up to
    # the first NUL byte. CMD 0x24 is passed as a QByteArray and keeps
    # its full length, including any embedded NUL bytes.
    if expected_command == 0x14:
        raw = raw.split(bytes((0,)), 1)[0]
    return TextResponse(command=message.command, raw=raw, text=raw.decode("utf-8", errors="replace"))


def parse_motor_identify_response(
    info: bytes | bytearray | memoryview,
) -> MotorIdentifyResponse:
    """Decode CMD 0x0F QString plus trailing boolean response."""
    message = parse_info(info)
    if message.command != 0x0F:
        raise ValueError(f"expected CMD 0x0F, got 0x{message.command:02X}")
    if not message.data:
        raise ValueError("CMD 0x0F response requires a trailing status byte")
    raw = bytes(message.data[:-1])
    return MotorIdentifyResponse(
        label_raw=raw,
        label=raw.decode("utf-8", errors="replace"),
        success=message.data[-1] != 0,
    )


def parse_firmware_version_response(
    info: bytes | bytearray | memoryview,
) -> FirmwareVersionResponse:
    """Decode CMD 0x11 version, boot/app marker, ASCII hardware name and serial.

    The V1.6 protocol defines D0 major, D1 minor, D2 mode marker (0xAC
    bootloader, 0xEF application), D3..D(n+2) ASCII hardware name, and the
    final byte as hardware serial number. The native V1.7 parser reads these
    fields in the same order. Raw name bytes are preserved.
    """
    message = parse_info(info)
    if message.command != 0x11:
        raise ValueError(f"expected CMD 0x11, got 0x{message.command:02X}")
    if len(message.data) < 4:
        raise ValueError("CMD 0x11 response requires three header bytes and one suffix byte")
    major, minor, boot_mode_flag = message.data[:3]
    hardware_name_raw = bytes(message.data[3:-1])
    serial_number = message.data[-1]
    return FirmwareVersionResponse(
        major=major,
        minor=minor,
        boot_mode_flag=boot_mode_flag,
        hardware_name_raw=hardware_name_raw,
        hardware_name=hardware_name_raw.decode("ascii", errors="replace"),
        hardware_serial_number=serial_number,
    )


def parse_setup_write_ack(
    info: bytes | bytearray | memoryview, expected_command: int
) -> SetupWriteAck:
    """Validate no-DATA status acknowledgements for setup/reset commands."""
    if expected_command not in (0x1B, 0x1D, 0x3A, 0x3D):
        raise ValueError("unsupported setup status acknowledgement command")
    message = parse_info(info)
    if message.command != expected_command:
        raise ValueError(
            f"expected CMD 0x{expected_command:02X}, got 0x{message.command:02X}"
        )
    if message.data:
        raise ValueError(f"CMD 0x{expected_command:02X} status ACK must have no DATA")
    return SetupWriteAck(command=message.command)


def parse_motor_signal_setup_response(
    info: bytes | bytearray | memoryview,
    first_profile_order: Iterable[str],
    first_metadata: Mapping[str, Mapping[str, Any]],
    second_profile_order: Iterable[str],
    second_metadata: Mapping[str, Mapping[str, Any]],
) -> MotorSignalSetupResponse:
    """Decode CMD 0x1C's two required marker-prefixed setup blocks."""
    message = parse_info(info)
    if message.command != 0x1C:
        raise ValueError(f"expected CMD 0x1C, got 0x{message.command:02X}")
    first = decode_profile_block(
        message.data, MOTOR_SETUP_MARKER, first_profile_order, first_metadata
    )
    second = decode_profile_block(
        message.data,
        MOTOR_SIGNAL_SETUP_MARKER,
        second_profile_order,
        second_metadata,
        offset=first.next_offset,
    )
    if second.next_offset != len(message.data):
        raise SetupValueError("CMD 0x1C response has unexpected trailing DATA")
    return MotorSignalSetupResponse(
        first_block=first, second_block=second, secret_key_status=0, success=True
    )


def _parse_single_setup_profile_response(
    info: bytes | bytearray | memoryview,
    expected_command: int,
    marker: int,
    profile_order: Iterable[str],
    metadata: Mapping[str, Mapping[str, Any]],
) -> SingleSetupProfileResponse:
    """Decode one V1.6 marker-prefixed setup block and preserve trailing bytes."""
    message = parse_info(info)
    if message.command != expected_command:
        raise ValueError(
            f"expected CMD 0x{expected_command:02X}, got 0x{message.command:02X}"
        )
    block = decode_profile_block(message.data, marker, profile_order, metadata)
    return SingleSetupProfileResponse(
        command=message.command,
        block=block,
        trailing_data=bytes(message.data[block.next_offset:]),
    )


def parse_v16_motor_setup_response(
    info: bytes | bytearray | memoryview,
    profile_order: Iterable[str],
    metadata: Mapping[str, Mapping[str, Any]],
) -> SingleSetupProfileResponse:
    """Decode V1.6 CMD 0x09 using marker 0xD2C6EF10."""
    return _parse_single_setup_profile_response(
        info, 0x09, MOTOR_SETUP_MARKER, profile_order, metadata
    )


def parse_v16_motor_signal_setup_response(
    info: bytes | bytearray | memoryview,
    profile_order: Iterable[str],
    metadata: Mapping[str, Mapping[str, Any]],
) -> SingleSetupProfileResponse:
    """Decode V1.6 CMD 0x0A using marker 0x4879187D."""
    return _parse_single_setup_profile_response(
        info, 0x0A, MOTOR_SIGNAL_SETUP_MARKER, profile_order, metadata
    )


def parse_topflow_setup_response(
    info: bytes | bytearray | memoryview,
    expected_command: int,
    profile_order: Iterable[str],
    metadata: Mapping[str, Mapping[str, Any]],
) -> TopFlowSetupResponse:
    """Decode CMD 0x3B/0x3C TopFlow block when its XML metadata is available."""
    if expected_command not in (0x3B, 0x3C):
        raise ValueError("TopFlow setup read responses use CMD 0x3B or 0x3C")
    message = parse_info(info)
    if message.command != expected_command:
        raise ValueError(
            f"expected CMD 0x{expected_command:02X}, got 0x{message.command:02X}"
        )
    block = decode_profile_block(
        message.data, TOPFLOW_SETUP_MARKER, profile_order, metadata
    )
    if block.next_offset != len(message.data):
        raise SetupValueError("TopFlow response has unexpected trailing DATA")
    return TopFlowSetupResponse(block=block, secret_key_status=0, success=True)


def parse_unclassified_id_vector_response(
    info: bytes | bytearray | memoryview,
) -> tuple[int, ...]:
    """Return the raw CMD 0x01 ID byte vector without semantic interpretation.

    Windows V1.6 converts all DATA bytes to a QVector<int>, but CMD 0x01 is
    absent from the public V1.6 command table. Do not label its elements as
    master/slave IDs until the command's semantics are independently proven.
    """
    message = parse_info(info)
    if message.command != 0x01:
        raise ValueError(f"expected CMD 0x01, got 0x{message.command:02X}")
    return tuple(message.data)


def parse_esc_id_enumeration_response(
    info: bytes | bytearray | memoryview,
) -> EscIdEnumerationResponse:
    """Decode official V1.6 CMD 0x1E: D0 master ID, D1.. slaves.

    The native Qt signal has an additional boolean argument whose exact
    meaning is not established here, so this decoder preserves only the
    documented ID vector and does not infer a success flag.
    """
    message = parse_info(info)
    if message.command != 0x1E:
        raise ValueError(f"expected CMD 0x1E, got 0x{message.command:02X}")
    raw = bytes(message.data)
    if not raw:
        return EscIdEnumerationResponse(master_id=None, slave_ids=(), raw_ids=raw)
    return EscIdEnumerationResponse(
        master_id=raw[0],
        slave_ids=tuple(raw[1:]),
        raw_ids=raw,
    )


def parse_can_forward_response(
    info: bytes | bytearray | memoryview, expected_slave_command: int | None = None
) -> CanForwardResponse:
    """Parse the UART bridge response: SlaveCMD becomes the INFO command byte."""
    message = parse_info(info)
    if expected_slave_command is not None and message.command != expected_slave_command:
        raise ValueError(
            f"expected slave response CMD 0x{expected_slave_command:02X}, "
            f"got 0x{message.command:02X}"
        )
    return CanForwardResponse(slave_command=message.command, slave_data=bytes(message.data))
