"""Offline VESC UART framing codec based on Flipsky VESC UART V1.0.

This module is deliberately separate from the FTESC codec. It performs no
serial I/O and must not be selected for an FTESC device.
"""
from __future__ import annotations

from dataclasses import dataclass


START_SHORT = 0x02
START_MEDIUM = 0x03
START_LONG = 0x04
END_MARKER = 0x03
MAX_INFO_LENGTH = 0xFFFFFF


class VescFrameError(ValueError):
    """A malformed VESC UART frame."""


class NeedMoreData(VescFrameError):
    """The supplied bytes do not yet contain a complete VESC UART frame."""


@dataclass(frozen=True, slots=True)
class VescFrame:
    info: bytes
    start_marker: int
    encoded_length: int


def crc16_vesc(data: bytes | bytearray | memoryview) -> int:
    """VESC/Flipsky VESC CRC-16: poly 0x1021, init 0, no reflection/xorout."""
    crc = 0
    for value in data:
        crc ^= int(value) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def encode_frame(info: bytes | bytearray | memoryview) -> bytes:
    """Encode INFO (command byte + DATA) using VESC 02/03/04 framing."""
    payload = bytes(info)
    length = len(payload)
    if length == 0:
        raise VescFrameError("VESC INFO must contain at least a command byte")
    if length > MAX_INFO_LENGTH:
        raise VescFrameError(f"VESC INFO length exceeds {MAX_INFO_LENGTH}")

    if length <= 0xFF:
        header = bytes((START_SHORT, length))
    elif length <= 0xFFFF:
        header = bytes((START_MEDIUM,)) + length.to_bytes(2, "big")
    else:
        header = bytes((START_LONG,)) + length.to_bytes(3, "big")

    crc = crc16_vesc(payload)
    return header + payload + crc.to_bytes(2, "big") + bytes((END_MARKER,))


def decode_frame(frame: bytes | bytearray | memoryview) -> VescFrame:
    """Decode exactly one VESC UART frame, validating length, CRC and ETX."""
    raw = bytes(frame)
    if not raw:
        raise NeedMoreData("empty input")

    marker = raw[0]
    if marker == START_SHORT:
        width = 1
    elif marker == START_MEDIUM:
        width = 2
    elif marker == START_LONG:
        width = 3
    else:
        raise VescFrameError(f"invalid VESC start marker 0x{marker:02X}")

    header_length = 1 + width
    if len(raw) < header_length:
        raise NeedMoreData("truncated VESC length field")

    length = int.from_bytes(raw[1:header_length], "big")
    if length == 0:
        raise VescFrameError("VESC INFO length cannot be zero")

    total_length = header_length + length + 2 + 1
    if len(raw) < total_length:
        raise NeedMoreData(
            f"truncated VESC frame: need {total_length} bytes, got {len(raw)}"
        )
    if len(raw) != total_length:
        raise VescFrameError(
            f"expected exactly one frame ({total_length} bytes), got {len(raw)}"
        )

    if raw[-1] != END_MARKER:
        raise VescFrameError(
            f"invalid VESC end marker 0x{raw[-1]:02X}; expected 0x03"
        )

    payload_start = header_length
    payload_end = payload_start + length
    info = raw[payload_start:payload_end]
    received_crc = int.from_bytes(raw[payload_end:payload_end + 2], "big")
    calculated_crc = crc16_vesc(info)
    if received_crc != calculated_crc:
        raise VescFrameError(
            f"VESC CRC mismatch: received 0x{received_crc:04X}, "
            f"calculated 0x{calculated_crc:04X}"
        )

    return VescFrame(
        info=info,
        start_marker=marker,
        encoded_length=length,
    )


def extract_complete_frame_length(buffer: bytes | bytearray | memoryview) -> int:
    """Return the first complete frame length, without validating CRC."""
    raw = bytes(buffer)
    if not raw:
        raise NeedMoreData("empty input")
    marker = raw[0]
    widths = {START_SHORT: 1, START_MEDIUM: 2, START_LONG: 3}
    if marker not in widths:
        raise VescFrameError(f"invalid VESC start marker 0x{marker:02X}")
    width = widths[marker]
    header_length = 1 + width
    if len(raw) < header_length:
        raise NeedMoreData("truncated VESC length field")
    length = int.from_bytes(raw[1:header_length], "big")
    if length == 0:
        raise VescFrameError("VESC INFO length cannot be zero")
    return header_length + length + 3
