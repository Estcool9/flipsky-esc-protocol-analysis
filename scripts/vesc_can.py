"""Offline VESC direct-CAN identifier and basic command codec.

The ID composition follows Flipsky VESC CAN V1.0's C example and the pinned
VESC firmware source: controller ID in bits 0..7, CAN command in bits 8..15.
No CAN socket/interface is opened and no frames are transmitted.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import math


MAX_EXTENDED_ID = 0x1FFFFFFF


class VescCanError(ValueError):
    """Invalid VESC CAN identifier or offline payload."""


class VescCanCommand(IntEnum):
    SET_DUTY = 0
    SET_CURRENT = 1
    SET_CURRENT_BRAKE = 2
    SET_RPM = 3
    SET_POS = 4
    STATUS = 9
    SET_CURRENT_REL = 10
    SET_CURRENT_BRAKE_REL = 11
    SET_CURRENT_HANDBRAKE = 12
    SET_CURRENT_HANDBRAKE_REL = 13
    STATUS_2 = 14
    STATUS_3 = 15
    STATUS_4 = 16
    STATUS_5 = 27


@dataclass(frozen=True, slots=True)
class VescCanFrame:
    can_id: int
    data: bytes
    extended: bool = True

    def __post_init__(self) -> None:
        if not 0 <= self.can_id <= MAX_EXTENDED_ID:
            raise VescCanError("CAN identifier must fit in 29 bits")
        if len(self.data) > 8:
            raise VescCanError("classic CAN payload cannot exceed 8 bytes")


@dataclass(frozen=True, slots=True)
class VescCanAddress:
    controller_id: int
    command_id: int
    reserved: int


def encode_identifier(controller_id: int, command_id: int) -> int:
    """Return the 29-bit VESC extended identifier."""
    for name, value in (("controller_id", controller_id), ("command_id", command_id)):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xFF:
            raise VescCanError(f"{name} must be an integer in 0..255")
    return controller_id | (command_id << 8)


def decode_identifier(can_id: int) -> VescCanAddress:
    if isinstance(can_id, bool) or not isinstance(can_id, int):
        raise VescCanError("CAN identifier must be an integer")
    if not 0 <= can_id <= MAX_EXTENDED_ID:
        raise VescCanError("CAN identifier must fit in 29 bits")
    return VescCanAddress(
        controller_id=can_id & 0xFF,
        command_id=(can_id >> 8) & 0xFF,
        reserved=(can_id >> 16) & 0x1FFF,
    )


def _scaled_i32(value: int | float, scale: float, label: str) -> bytes:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise VescCanError(f"{label} must be numeric")
    if not math.isfinite(value):
        raise VescCanError(f"{label} must be finite")
    scaled = int(value * scale)  # C sample casts truncate toward zero.
    if not -(1 << 31) <= scaled < (1 << 31):
        raise VescCanError(f"{label} overflows signed 32-bit scaled representation")
    return scaled.to_bytes(4, "big", signed=True)


def build_scaled_command(
    controller_id: int,
    command: VescCanCommand | int,
    value: int | float,
    scale: float,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> VescCanFrame:
    """Build a basic 4-byte scaled VESC CAN command without transmitting it."""
    try:
        command_id = int(command)
    except (TypeError, ValueError) as exc:
        raise VescCanError("command must be a known integer VESC CAN command") from exc
    if isinstance(command, bool) or not 0 <= command_id <= 0xFF:
        raise VescCanError("command must fit in one byte")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise VescCanError("value must be a finite number")
    if minimum is not None and value < minimum:
        raise VescCanError(f"value must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise VescCanError(f"value must be at most {maximum}")
    return VescCanFrame(
        can_id=encode_identifier(controller_id, command_id),
        data=_scaled_i32(value, scale, "value"),
    )


def build_duty(controller_id: int, duty: float) -> VescCanFrame:
    return build_scaled_command(
        controller_id, VescCanCommand.SET_DUTY, duty, 100_000.0,
        minimum=-1.0, maximum=1.0,
    )


def build_current(controller_id: int, current_a: float) -> VescCanFrame:
    return build_scaled_command(
        controller_id, VescCanCommand.SET_CURRENT, current_a, 1_000.0
    )


def build_brake_current(controller_id: int, current_a: float) -> VescCanFrame:
    return build_scaled_command(
        controller_id, VescCanCommand.SET_CURRENT_BRAKE, current_a, 1_000.0
    )


def build_rpm(controller_id: int, erpm: int | float) -> VescCanFrame:
    return build_scaled_command(
        controller_id, VescCanCommand.SET_RPM, erpm, 1.0
    )


def build_position(controller_id: int, degrees: float) -> VescCanFrame:
    return build_scaled_command(
        controller_id, VescCanCommand.SET_POS, degrees, 1_000_000.0,
        minimum=-180.0, maximum=180.0,
    )
