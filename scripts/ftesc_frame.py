#!/usr/bin/env python3
"""Offline codec for the outer Flipsky FT ESC UART frame (static RE only)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Final

SHORT_MARKER: Final[int] = 0xAA
EXTENDED_MARKER: Final[int] = 0xBB
END_MARKER: Final[int] = 0xDD
DEFAULT_MAX_PAYLOAD: Final[int] = 0x2710  # constructor initializes 10,000

class FrameError(ValueError):
    """Invalid or unsupported frame."""

class NeedMoreData(FrameError):
    """A valid-looking frame is incomplete."""

@dataclass(frozen=True, slots=True)
class Frame:
    marker: int
    payload: bytes
    crc: int
    consumed: int
    @property
    def length(self) -> int:
        return len(self.payload)

def crc16_modbus(data: bytes | bytearray | memoryview) -> int:
    """CRC-16/MODBUS: reflected poly 0xA001, init 0xFFFF, xorout 0."""
    crc = 0xFFFF
    for value in data:
        crc ^= int(value)
        for _ in range(8):
            crc = (crc >> 1) ^ (0xA001 if crc & 1 else 0)
    return crc & 0xFFFF

def encode_frame(payload: bytes | bytearray | memoryview, *,
                 max_payload: int = DEFAULT_MAX_PAYLOAD) -> bytes:
    """Encode payload using AA+LEN8 (<=255) or BB+LEN16_BE (>255)."""
    body = bytes(payload)
    n = len(body)
    if n == 0:
        raise FrameError("zero-length payloads are rejected by the analysed parser")
    if not 1 <= max_payload <= 0xFFFF:
        raise ValueError("max_payload must be between 1 and 65535")
    if n > max_payload:
        raise FrameError(f"payload length {n} exceeds configured maximum {max_payload}")
    header = bytes((SHORT_MARKER, n)) if n <= 0xFF else bytes((EXTENDED_MARKER,)) + n.to_bytes(2, "big")
    checksum = crc16_modbus(body).to_bytes(2, "big")
    return header + body + checksum + bytes((END_MARKER,))

def decode_frame(data: bytes | bytearray | memoryview, *, offset: int = 0,
                 max_payload: int = DEFAULT_MAX_PAYLOAD) -> Frame:
    """Decode one complete frame at offset; raise NeedMoreData on truncation."""
    view = memoryview(data).cast("B")
    if offset < 0 or offset > len(view):
        raise ValueError("offset is outside the input buffer")
    available = len(view) - offset
    if available < 1:
        raise NeedMoreData("waiting for frame marker")
    marker = int(view[offset])
    if marker == SHORT_MARKER:
        header_size = 2
        if available < header_size:
            raise NeedMoreData("waiting for one-byte length")
        n = int(view[offset + 1])
        if n == 0:
            raise FrameError("AA frame has zero payload length")
    elif marker == EXTENDED_MARKER:
        header_size = 3
        if available < header_size:
            raise NeedMoreData("waiting for two-byte length")
        n = int.from_bytes(view[offset + 1:offset + 3], "big")
        if n <= 0xFE:
            raise FrameError("BB frame length must be greater than 254")
    else:
        raise FrameError(f"unsupported start marker 0x{marker:02X}")
    if not 1 <= max_payload <= 0xFFFF:
        raise ValueError("max_payload must be between 1 and 65535")
    if n > max_payload:
        raise FrameError(f"payload length {n} exceeds configured maximum {max_payload}")
    total = header_size + n + 3
    if available < total:
        raise NeedMoreData(f"frame needs {total} bytes; only {available} available")
    pstart = offset + header_size
    pend = pstart + n
    payload = bytes(view[pstart:pend])
    # Native V1.6/V1.7 parsers reject a bad terminator before checking CRC.
    terminator = int(view[pend + 2])
    if terminator != END_MARKER:
        raise FrameError(f"invalid terminator 0x{terminator:02X}; expected 0x{END_MARKER:02X}")
    received = int.from_bytes(view[pend:pend + 2], "big")
    calculated = crc16_modbus(payload)
    if received != calculated:
        raise FrameError(f"CRC mismatch: received 0x{received:04X}, calculated 0x{calculated:04X}")
    return Frame(marker, payload, received, total)

def decode_frames(data: bytes | bytearray | memoryview, *,
                  max_payload: int = DEFAULT_MAX_PAYLOAD) -> list[Frame]:
    """Decode concatenated complete frames. No speculative byte resynchronization."""
    result: list[Frame] = []
    offset = 0
    while offset < len(data):
        frame = decode_frame(data, offset=offset, max_payload=max_payload)
        result.append(frame)
        offset += frame.consumed
    return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hex_bytes", help="hex-encoded bytes containing complete frames")
    args = parser.parse_args()
    for i, f in enumerate(decode_frames(bytes.fromhex(args.hex_bytes)), 1):
        print(f"frame {i}: marker=0x{f.marker:02X} length={f.length} crc=0x{f.crc:04X} payload={f.payload.hex()}")
