"""Incremental offline VESC UART stream decoder.

This module only parses byte streams. It never opens a serial port or sends data.
"""
from __future__ import annotations

from dataclasses import dataclass

from .vesc_uart import (
    NeedMoreData,
    VescFrame,
    VescFrameError,
    decode_frame,
    extract_complete_frame_length,
)


@dataclass(frozen=True, slots=True)
class VescStreamStats:
    frames: int
    discarded_bytes: int
    buffered_bytes: int


class VescStreamDecoder:
    """Decode fragmented/concatenated VESC frames and recover after noise.

    Invalid candidates are discarded one byte at a time, matching the
    resynchronization strategy used by the FTESC stream decoder. Incomplete
    candidates remain buffered until the next feed().
    """

    def __init__(self, *, max_info_length: int = 0x100000) -> None:
        if isinstance(max_info_length, bool) or not isinstance(max_info_length, int):
            raise ValueError("max_info_length must be an integer")
        if not 1 <= max_info_length <= 0xFFFFFF:
            raise ValueError("max_info_length must be in 1..0xFFFFFF")
        self.max_info_length = max_info_length
        self._buffer = bytearray()
        self._frames = 0
        self._discarded = 0

    @property
    def buffered_bytes(self) -> int:
        return len(self._buffer)

    @property
    def stats(self) -> VescStreamStats:
        return VescStreamStats(self._frames, self._discarded, len(self._buffer))

    def reset(self) -> None:
        self._buffer.clear()
        self._frames = 0
        self._discarded = 0

    def feed(self, data: bytes | bytearray | memoryview) -> list[VescFrame]:
        self._buffer.extend(data)
        decoded: list[VescFrame] = []

        while self._buffer:
            if self._buffer[0] not in (0x02, 0x03, 0x04):
                del self._buffer[0]
                self._discarded += 1
                continue

            try:
                frame_length = extract_complete_frame_length(self._buffer)
            except NeedMoreData:
                break
            except VescFrameError:
                del self._buffer[0]
                self._discarded += 1
                continue

            info_length = frame_length - (2 if self._buffer[0] == 0x02 else
                                          3 if self._buffer[0] == 0x03 else 4) - 3
            if info_length > self.max_info_length:
                del self._buffer[0]
                self._discarded += 1
                continue

            if len(self._buffer) < frame_length:
                break

            candidate = bytes(self._buffer[:frame_length])
            try:
                frame = decode_frame(candidate)
            except VescFrameError:
                del self._buffer[0]
                self._discarded += 1
                continue

            del self._buffer[:frame_length]
            decoded.append(frame)
            self._frames += 1

        return decoded
