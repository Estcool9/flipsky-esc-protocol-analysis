"""Offline serializer for the typed setup values observed in Flipsky V1.7.

This module only constructs bytes in memory. It does not open a transport.
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from collections.abc import Iterable, Mapping
from typing import Any


class SetupValueError(ValueError):
    """Unsupported setup type or value outside the encoded range."""


def _round_away_from_zero(value: float) -> int:
    if not math.isfinite(value):
        raise SetupValueError("scaled value must be finite")
    return math.floor(value + 0.5) if value >= 0 else math.ceil(value - 0.5)


def _require_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SetupValueError(f"{field} must be an integer")
    return value


def _pack_byte(value: Any) -> bytes:
    n = _require_int(value, "value")
    if not 0 <= n <= 0xFF:
        raise SetupValueError("byte value outside 0..255")
    return bytes((n,))


def _pack_signed_byte(value: Any) -> bytes:
    n = _require_int(value, "value")
    if not -0x80 <= n <= 0x7F:
        raise SetupValueError("value outside signed 8-bit range")
    return struct.pack(">b", n)


def encode_setup_value(
    *,
    val_type: int,
    value_tet: int | None,
    value_int: int | None = None,
    value_dou: float | None = None,
    eval_scl: float | None = None,
) -> bytes:
    """Encode one XML ValueSetup using the V1.7 serializer's type branches.

    val_type corresponds to the outer ValueSetup type discriminator.
    value_tet corresponds to the transmit-type discriminator.
    """
    if val_type == 1:
        if value_dou is None:
            raise SetupValueError("floating ValueSetup requires value_dou")
        if value_tet in (7, 8):
            if eval_scl is None:
                raise SetupValueError("scaled float requires eval_scl")
            scaled = _round_away_from_zero(float(value_dou) * float(eval_scl))
            if value_tet == 7:
                if not -0x8000 <= scaled <= 0x7FFF:
                    raise SetupValueError("scaled value outside signed 16-bit range")
                return struct.pack(">h", scaled)
            if not -0x80000000 <= scaled <= 0x7FFFFFFF:
                raise SetupValueError("scaled value outside signed 32-bit range")
            return struct.pack(">i", scaled)
        if value_tet == 9:
            try:
                return struct.pack(">f", float(value_dou))
            except (OverflowError, struct.error) as exc:
                raise SetupValueError("value outside IEEE-754 float32 range") from exc
        raise SetupValueError(f"unsupported floating valueTET {value_tet!r}")

    if val_type == 2:
        n = _require_int(value_int, "value_int")
        if value_tet == 1:
            return _pack_byte(n)
        if value_tet == 2:
            return _pack_signed_byte(n)
        if value_tet == 3:
            if not 0 <= n <= 0xFFFF:
                raise SetupValueError("value outside unsigned 16-bit range")
            return struct.pack(">H", n)
        if value_tet == 4:
            if not -0x8000 <= n <= 0x7FFF:
                raise SetupValueError("value outside signed 16-bit range")
            return struct.pack(">h", n)
        if value_tet == 5:
            if not 0 <= n <= 0xFFFFFFFF:
                raise SetupValueError("value outside unsigned 32-bit range")
            return struct.pack(">I", n)
        if value_tet == 6:
            if not -0x80000000 <= n <= 0x7FFFFFFF:
                raise SetupValueError("value outside signed 32-bit range")
            return struct.pack(">i", n)
        raise SetupValueError(f"unsupported integer valueTET {value_tet!r}")

    if val_type in (4, 6, 7):
        return _pack_signed_byte(value_int)

    raise SetupValueError(f"unsupported valType {val_type!r}")


def encode_setup_block(marker: int, values: Iterable[Mapping[str, Any]]) -> bytes:
    """Encode one observed marker-prefixed setup block in vector order."""
    if isinstance(marker, bool) or not isinstance(marker, int) or not 0 <= marker <= 0xFFFFFFFF:
        raise SetupValueError("marker must be an unsigned 32-bit integer")
    output = bytearray(struct.pack(">I", marker))
    for item in values:
        output.extend(
            encode_setup_value(
                val_type=int(item["valType"]),
                value_tet=(int(item["valueTET"]) if item.get("valueTET") not in (None, "") else None),
                value_int=(int(item["value_int"]) if item.get("value_int") not in (None, "") else None),
                value_dou=(float(item["value_dou"]) if item.get("value_dou") not in (None, "") else None),
                eval_scl=(float(item["evalScl"]) if item.get("evalScl") not in (None, "") else None),
            )
        )
    return bytes(output)


def encode_profile_block(
    marker: int,
    profile_order: Iterable[str],
    values_by_id: Mapping[str, Mapping[str, Any]],
) -> bytes:
    """Encode a profile using its ValueSeque order, not Values/dict order."""
    order = list(profile_order)
    missing = [xml_id for xml_id in order if xml_id not in values_by_id]
    if missing:
        raise SetupValueError(f"profile values missing IDs: {missing}")
    return encode_setup_block(marker, (values_by_id[xml_id] for xml_id in order))



@dataclass(frozen=True, slots=True)
class DecodedSetupBlock:
    """Decoded marker block; next_offset allows parsing a following block."""
    marker: int
    values: dict[str, dict[str, int | float]]
    next_offset: int


def _read_integer(data: bytes, offset: int, size: int, *, signed: bool) -> tuple[int, int]:
    end = offset + size
    if offset < 0 or end > len(data):
        raise SetupValueError("setup block is truncated")
    return int.from_bytes(data[offset:end], "big", signed=signed), end


def decode_profile_block(
    data: bytes | bytearray | memoryview,
    marker: int,
    profile_order: Iterable[str],
    metadata_by_id: Mapping[str, Mapping[str, Any]],
    *,
    offset: int = 0,
) -> DecodedSetupBlock:
    """Decode one marker-prefixed block using its ValueSeque and ValueSetup metadata.

    The returned next_offset points immediately after this block, so a caller
    can decode an optional second marker block from the same response buffer.
    """
    raw = bytes(data)
    if isinstance(marker, bool) or not isinstance(marker, int) or not 0 <= marker <= 0xFFFFFFFF:
        raise SetupValueError("marker must be an unsigned 32-bit integer")
    if offset < 0 or offset + 4 > len(raw):
        raise SetupValueError("setup block is missing its 4-byte marker")
    actual_marker = struct.unpack_from(">I", raw, offset)[0]
    if actual_marker != marker:
        raise SetupValueError(
            f"setup marker mismatch: expected 0x{marker:08X}, got 0x{actual_marker:08X}"
        )
    cursor = offset + 4
    decoded: dict[str, dict[str, int | float]] = {}

    for xml_id in profile_order:
        if xml_id not in metadata_by_id:
            raise SetupValueError(f"profile metadata missing ID {xml_id!r}")
        item = metadata_by_id[xml_id]
        try:
            val_type = int(item["valType"])
            raw_tet = item.get("valueTET")
            value_tet = None if raw_tet in (None, "") else int(raw_tet)
        except (KeyError, TypeError, ValueError) as exc:
            raise SetupValueError(f"invalid type metadata for {xml_id!r}") from exc

        if val_type == 1:
            if value_tet in (7, 8):
                scale_raw = item.get("evalScl")
                if scale_raw in (None, ""):
                    raise SetupValueError(f"scaled float {xml_id!r} is missing evalScl")
                scale = float(scale_raw)
                if not math.isfinite(scale) or scale == 0:
                    raise SetupValueError(f"scaled float {xml_id!r} has invalid evalScl")
                size = 2 if value_tet == 7 else 4
                integer, cursor = _read_integer(raw, cursor, size, signed=True)
                decoded[xml_id] = {"value_dou": integer / scale}
            elif value_tet == 9:
                if cursor + 4 > len(raw):
                    raise SetupValueError("setup block is truncated")
                value = struct.unpack_from(">f", raw, cursor)[0]
                cursor += 4
                decoded[xml_id] = {"value_dou": value}
            else:
                raise SetupValueError(
                    f"unsupported floating valueTET {value_tet!r} for {xml_id!r}"
                )
        elif val_type == 2:
            layouts = {
                1: (1, False),
                2: (1, True),
                3: (2, False),
                4: (2, True),
                5: (4, False),
                6: (4, True),
            }
            if value_tet not in layouts:
                raise SetupValueError(
                    f"unsupported integer valueTET {value_tet!r} for {xml_id!r}"
                )
            size, signed = layouts[value_tet]
            value, cursor = _read_integer(raw, cursor, size, signed=signed)
            decoded[xml_id] = {"value_int": value}
        elif val_type in (4, 6, 7):
            value, cursor = _read_integer(raw, cursor, 1, signed=True)
            decoded[xml_id] = {"value_int": value}
        else:
            raise SetupValueError(f"unsupported valType {val_type!r} for {xml_id!r}")

    return DecodedSetupBlock(marker=marker, values=decoded, next_offset=cursor)
