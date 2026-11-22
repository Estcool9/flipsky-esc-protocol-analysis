"""Incremental Flipsky FT ESC frame stream decoder; offline only."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Final
from scripts.ftesc_frame import DEFAULT_MAX_PAYLOAD, Frame, FrameError, NeedMoreData, decode_frame, encode_frame

MARKERS: Final[tuple[int, int]] = (0xAA, 0xBB)

@dataclass(frozen=True, slots=True)
class StreamStats:
    frames: int
    discarded_bytes: int
    invalid_candidates: int
    buffered_bytes: int

class FrameStreamDecoder:
    """Incremental parser retaining incomplete frames between feed calls."""
    def __init__(self, *, max_payload: int = DEFAULT_MAX_PAYLOAD) -> None:
        if not 1 <= max_payload <= 0xFFFF:
            raise ValueError("max_payload must be between 1 and 65535")
        self.max_payload = max_payload
        self._buffer = bytearray()
        self.frames_decoded = self.discarded_bytes = self.invalid_candidates = 0

    @property
    def buffered_bytes(self) -> int:
        return len(self._buffer)

    def reset(self) -> None:
        self._buffer.clear()
        self.frames_decoded = self.discarded_bytes = self.invalid_candidates = 0

    def stats(self) -> StreamStats:
        return StreamStats(self.frames_decoded, self.discarded_bytes,
                           self.invalid_candidates, len(self._buffer))

    def feed(self, data: bytes | bytearray | memoryview) -> list[Frame]:
        output: list[Frame] = []
        for value in memoryview(data).cast("B"):
            self._buffer.append(int(value))
            self._drain(output)
        return output

    def _drain(self, output: list[Frame]) -> None:
        while self._buffer:
            marker_index = next((i for i, value in enumerate(self._buffer)
                                 if value in MARKERS), None)
            if marker_index is None:
                self.discarded_bytes += len(self._buffer)
                self._buffer.clear()
                return
            if marker_index:
                self.discarded_bytes += marker_index
                del self._buffer[:marker_index]
            try:
                # Immutable copy avoids a memoryview export blocking buffer resize
                # when an invalid candidate is discarded during resynchronization.
                frame = decode_frame(bytes(self._buffer), max_payload=self.max_payload)
            except NeedMoreData:
                return
            except FrameError:
                self.invalid_candidates += 1
                self.discarded_bytes += 1
                del self._buffer[0]
                continue
            output.append(frame)
            self.frames_decoded += 1
            del self._buffer[:frame.consumed]

def encode_stream(*payloads: bytes) -> bytes:
    """Build concatenated synthetic frames for offline tests."""
    return b"".join(encode_frame(payload) for payload in payloads)
