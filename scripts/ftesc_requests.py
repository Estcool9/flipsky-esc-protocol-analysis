"""Offline builders for the recovered Flipsky ESC Tool V1.7 INFO requests.

The functions return bytes only. They never open a transport or transmit data.
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any

from scripts.ftesc_protocol import build_info
from scripts.ftesc_setup_serializer import (
    SetupValueError,
    _round_away_from_zero,
    encode_profile_block,
)

CMD_GET_REALTIME_ONCE = 0x00
CMD_OBTAIN_ID_OVER_CAN = 0x01
CMD_SET_DUTY = 0x03
CMD_SET_CURRENT = 0x04
CMD_SET_BRAKE_CURRENT = 0x06
CMD_SET_MOTOR_SETUP = 0x07
CMD_OBTAIN_MOTOR_SETUP = 0x09
CMD_OBTAIN_CONTROL_SETUP = 0x0A
CMD_OBTAIN_PPM = 0x0D
CMD_OBTAIN_ADC = 0x0E
CMD_IDENTIFY_MOTOR_OVER_CAN = 0x0F
CMD_GET_FIRMWARE_VERSION = 0x11
CMD_ENTER_BOOT_MODE = 0x13
CMD_KEEPALIVE = 0x19
CMD_SET_AUTO_REALTIME = 0x1A
CMD_SET_MOTOR_SIGNAL_SETUP = 0x1B
CMD_OBTAIN_MOTOR_SIGNAL_SETUP = 0x1C
CMD_RESET_TOPFLOW = 0x1D
CMD_OBTAIN_ALL_ESC_IDS = 0x1E
CMD_OBTAIN_UUID = 0x21
CMD_REBOOT = 0x23
CMD_SET_ID_CURRENT = 0x25
CMD_SET_POSITION = 0x26
CMD_SET_SPEED = 0x27
CMD_IMU_CALIBRATION = 0x29
CMD_SET_TOPFLOW_SETUP = 0x3A
CMD_OBTAIN_TOPFLOW_SETUP = 0x3B
CMD_OBTAIN_TOPFLOW_DEFAULT_SETUP = 0x3C

MOTOR_SETUP_MARKER = 0xD2C6EF10
MOTOR_SIGNAL_SETUP_MARKER = 0x4879187D
TOPFLOW_SETUP_MARKER = 0x54464346


def _scaled_i32(value: int | float, scale: int) -> bytes:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise SetupValueError("control value must be finite")
    scaled = _round_away_from_zero(numeric * scale)
    if not -(1 << 31) <= scaled < (1 << 31):
        raise SetupValueError("scaled control value does not fit signed int32")
    return scaled.to_bytes(4, "big", signed=True)


def _scaled_i16(value: int | float, scale: int, label: str) -> bytes:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise SetupValueError(f"{label} must be finite")
    scaled = _round_away_from_zero(numeric * scale)
    if not -(1 << 15) <= scaled < (1 << 15):
        raise SetupValueError(f"{label} does not fit signed int16")
    return scaled.to_bytes(2, "big", signed=True)


def _u16(value: int, label: str) -> bytes:
    if not isinstance(value, int) or not 0 <= value <= 0xFFFF:
        raise SetupValueError(f"{label} must fit unsigned 16-bit")
    return value.to_bytes(2, "big")


def _u8(value: int, label: str) -> bytes:
    if not isinstance(value, int) or not 0 <= value <= 0xFF:
        raise SetupValueError(f"{label} must fit unsigned 8-bit")
    return bytes((value,))


def build_get_realtime_once_info() -> bytes:
    return build_info(CMD_GET_REALTIME_ONCE)


def build_obtain_id_over_can_info() -> bytes:
    return build_info(CMD_OBTAIN_ID_OVER_CAN)


def build_get_firmware_version_info() -> bytes:
    return build_info(CMD_GET_FIRMWARE_VERSION)


def build_keepalive_info() -> bytes:
    return build_info(CMD_KEEPALIVE)


def build_obtain_motor_setup_info() -> bytes:
    return build_info(CMD_OBTAIN_MOTOR_SETUP)


def build_obtain_control_setup_info() -> bytes:
    return build_info(CMD_OBTAIN_CONTROL_SETUP)


def build_obtain_ppm_info() -> bytes:
    return build_info(CMD_OBTAIN_PPM)


def build_obtain_adc_info() -> bytes:
    return build_info(CMD_OBTAIN_ADC)


def build_enter_boot_mode_info() -> bytes:
    return build_info(CMD_ENTER_BOOT_MODE)


def build_obtain_motor_signal_setup_info() -> bytes:
    return build_info(CMD_OBTAIN_MOTOR_SIGNAL_SETUP)


def build_obtain_all_esc_ids_info() -> bytes:
    return build_info(CMD_OBTAIN_ALL_ESC_IDS)


def build_obtain_uuid_info() -> bytes:
    return build_info(CMD_OBTAIN_UUID)


def build_reboot_info() -> bytes:
    return build_info(CMD_REBOOT)


def build_obtain_topflow_setup_info() -> bytes:
    return build_info(CMD_OBTAIN_TOPFLOW_SETUP)


def build_obtain_topflow_default_setup_info() -> bytes:
    return build_info(CMD_OBTAIN_TOPFLOW_DEFAULT_SETUP)


def build_control_duty_info(value: int | float) -> bytes:
    return build_info(CMD_SET_DUTY, _scaled_i32(value, 100_000))


def build_control_current_info(value: int | float) -> bytes:
    return build_info(CMD_SET_CURRENT, _scaled_i32(value, 1_000))


def build_control_brake_current_info(value: int | float) -> bytes:
    return build_info(CMD_SET_BRAKE_CURRENT, _scaled_i32(value, 1_000))


def build_control_id_current_info(value: int | float) -> bytes:
    return build_info(CMD_SET_ID_CURRENT, _scaled_i32(value, 1_000))


def build_control_position_info(value: int | float) -> bytes:
    return build_info(CMD_SET_POSITION, _scaled_i32(value, 1_000))


def build_control_speed_info(value: int | float) -> bytes:
    return build_info(CMD_SET_SPEED, _scaled_i32(value, 1))


def build_identify_motor_over_can_info(
    arg1_byte: int,
    arg2_byte: int,
    arg3_scaled_100: int | float,
    arg4_rounded_int16: int | float,
    arg5_byte: int,
) -> bytes:
    """Build CMD 0x0F using the native argument order and field widths.

    The native method serializes arg2, low byte of arg1, rounded arg4,
    rounded arg3*100, then arg5. Semantic field names are not established.
    """
    data = (
        _u8(arg2_byte, "arg2_byte")
        + _u8(arg1_byte, "arg1_byte")
        + _scaled_i16(arg4_rounded_int16, 1, "arg4_rounded_int16")
        + _scaled_i16(arg3_scaled_100, 100, "arg3_scaled_100")
        + _u8(arg5_byte, "arg5_byte")
    )
    return build_info(CMD_IDENTIFY_MOTOR_OVER_CAN, data)


def build_imu_calibration_info(value: int | float) -> bytes:
    return build_info(CMD_IMU_CALIBRATION, _scaled_i32(value, 1_000))


def build_auto_realtime_info(enabled: bool, interval: int) -> bytes:
    if not isinstance(enabled, bool):
        raise SetupValueError("enabled must be bool")
    return build_info(CMD_SET_AUTO_REALTIME, bytes((int(enabled),)) + _u16(interval, "interval"))


def build_motor_setup_info(
    profile_order: Iterable[str],
    values_by_id: Mapping[str, Mapping[str, Any]],
) -> bytes:
    block = encode_profile_block(MOTOR_SETUP_MARKER, profile_order, values_by_id)
    return build_info(CMD_SET_MOTOR_SETUP, block)


def build_motor_signal_setup_info(
    motor_profile_order: Iterable[str],
    motor_values_by_id: Mapping[str, Mapping[str, Any]],
    signal_profile_order: Iterable[str] | None = None,
    signal_values_by_id: Mapping[str, Mapping[str, Any]] | None = None,
) -> bytes:
    """Build CMD 0x1B with a required motor block and optional signal block.

    V1.7 emits the second marker only when the corresponding second vector
    exists. The product/model rule deciding whether to provide it is not
    inferred here.
    """
    if (signal_profile_order is None) != (signal_values_by_id is None):
        raise SetupValueError("second marker block requires both order and values")
    data = encode_profile_block(MOTOR_SETUP_MARKER, motor_profile_order, motor_values_by_id)
    if signal_profile_order is not None and signal_values_by_id is not None:
        data += encode_profile_block(
            MOTOR_SIGNAL_SETUP_MARKER, signal_profile_order, signal_values_by_id
        )
    return build_info(CMD_SET_MOTOR_SIGNAL_SETUP, data)


def build_topflow_setup_info(
    profile_order: Iterable[str],
    values_by_id: Mapping[str, Mapping[str, Any]],
) -> bytes:
    block = encode_profile_block(TOPFLOW_SETUP_MARKER, profile_order, values_by_id)
    return build_info(CMD_SET_TOPFLOW_SETUP, block)


def build_reset_topflow_info() -> bytes:
    return build_info(CMD_RESET_TOPFLOW)


def build_reset_motor_signal_setup_info(flag: int) -> bytes:
    """Build the overloaded CMD 0x1D variant with one trailing byte.

    The native method appends one byte; the semantic name of this flag is
    not established, so the API deliberately calls it only 'flag'.
    """
    return build_info(CMD_RESET_TOPFLOW, _u8(flag, "flag"))


# V1.4-compatible UART bridge/control commands. These are kept separate from
# the V1.7-native request builders above because command 0x1D is version-overloaded.
CMD_CAN_OVER = 0x10
CMD_CONTROL_AND_OBTAIN_DATA_ONCE = 0x02
CMD_CURRENT_GEAR_AND_OBTAIN_DATA = 0x20


def _scaled_i32_trunc(value: int | float, scale: int, label: str) -> bytes:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise SetupValueError(f"{label} must be finite")
    scaled = int(numeric * scale)  # C cast semantics: truncate toward zero.
    if not -(1 << 31) <= scaled < (1 << 31):
        raise SetupValueError(f"{label} does not fit signed int32 after scaling")
    return scaled.to_bytes(4, "big", signed=True)


def _bool_byte(value: bool, label: str) -> bytes:
    if not isinstance(value, bool):
        raise SetupValueError(f"{label} must be bool")
    return bytes((int(value),))


def build_can_forward_info(
    slave_id: int, slave_command: int, slave_data: bytes = b""
) -> bytes:
    """Build UART CMD 0x10: SlaveID, SlaveCMD, then SlaveDATA."""
    if not isinstance(slave_data, (bytes, bytearray, memoryview)):
        raise SetupValueError("slave_data must be bytes-like")
    data = _u8(slave_id, "slave_id") + _u8(slave_command, "slave_command") + bytes(slave_data)
    return build_info(CMD_CAN_OVER, data)


def build_control_and_obtain_data_once_info(
    current_code: int,
    *,
    direction_switch_enabled: bool = False,
    rotation_direction: bool = False,
    gear: int = 0,
    horn: bool = False,
    headlight: bool = False,
    brake_light: bool = False,
    cruise_enabled: bool = False,
    cruise_on: bool = False,
    multi_mode_enabled: bool = False,
    multi_mode: int = 0,
) -> bytes:
    """Build the V1.4 CMD 0x02 14-byte esk8/esurf control payload.

    current_code is the protocol's raw 0..1023 code, not amperes:
    0..511 represents braking/negative current and 512..1023 driving current.
    """
    if isinstance(current_code, bool) or not isinstance(current_code, int) or not 0 <= current_code <= 1023:
        raise SetupValueError("current_code must be an integer in 0..1023")
    if isinstance(gear, bool) or not isinstance(gear, int) or not 0 <= gear <= 4:
        raise SetupValueError("gear must be an integer in 0..4")
    if isinstance(multi_mode, bool) or not isinstance(multi_mode, int) or not 0 <= multi_mode <= 2:
        raise SetupValueError("multi_mode must be an integer in 0..2")
    data = (
        _u16(current_code, "current_code")
        + bytes(2)
        + _bool_byte(direction_switch_enabled, "direction_switch_enabled")
        + _bool_byte(rotation_direction, "rotation_direction")
        + _u8(gear, "gear")
        + _bool_byte(horn, "horn")
        + _bool_byte(headlight, "headlight")
        + _bool_byte(brake_light, "brake_light")
        + _bool_byte(cruise_enabled, "cruise_enabled")
        + _bool_byte(cruise_on, "cruise_on")
        + _bool_byte(multi_mode_enabled, "multi_mode_enabled")
        + _u8(multi_mode, "multi_mode")
    )
    if len(data) != 14:
        raise AssertionError("V1.4 CMD 0x02 payload must be exactly 14 bytes")
    return build_info(CMD_CONTROL_AND_OBTAIN_DATA_ONCE, data)


def build_current_gear_and_obtain_data_info(
    current: int | float, gear: int
) -> bytes:
    """Build V1.4 CMD 0x20: signed current*1000 followed by gear byte."""
    data = _scaled_i32_trunc(current, 1_000, "current") + _u8(gear, "gear")
    return build_info(CMD_CURRENT_GEAR_AND_OBTAIN_DATA, data)


def build_v14_reset_reboot_info() -> bytes:
    """Build the V1.4 CMD 0x1D reset/reboot request with reserved byte 0x00.

    V1.7 reuses CMD 0x1D for TopFlow/motor-signal setup operations; do not
    substitute this V1.4 variant for the V1.7-native reset builders.
    """
    return build_info(0x1D, bytes((0,)))
