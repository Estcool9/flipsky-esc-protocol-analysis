import unittest

from scripts.ftesc_requests import (
    MOTOR_SETUP_MARKER,
    MOTOR_SIGNAL_SETUP_MARKER,
    TOPFLOW_SETUP_MARKER,
    build_auto_realtime_info,
    build_can_forward_info,
    build_v14_control_and_obtain_data_once_info,
    build_v16_control_and_obtain_data_once_info,
    build_v16_pas_gear_control_info,
    build_current_gear_and_obtain_data_info,
    build_control_brake_current_info,
    build_control_current_info,
    build_control_duty_info,
    build_control_id_current_info,
    build_control_position_info,
    build_control_speed_info,
    build_get_realtime_once_info,
    build_imu_calibration_info,
    build_identify_motor_over_can_info,
    build_motor_setup_info,
    build_motor_signal_setup_info,
    build_reset_motor_signal_setup_info,
    build_reset_topflow_info,
    build_topflow_setup_info,
    build_v14_reset_reboot_info,
)
from scripts.ftesc_setup_serializer import SetupValueError


class V17RequestBuilderTests(unittest.TestCase):
    def test_realtime_once_is_cmd_00(self):
        self.assertEqual(build_get_realtime_once_info(), b"\x00")

    def test_control_scaling_and_signed_big_endian(self):
        self.assertEqual(build_control_duty_info(0.5), bytes.fromhex("03 00 00 C3 50"))
        self.assertEqual(build_control_current_info(1.5), bytes.fromhex("04 00 00 05 DC"))
        self.assertEqual(build_control_brake_current_info(-1.5), bytes.fromhex("06 FF FF FA 24"))
        self.assertEqual(build_control_id_current_info(1), bytes.fromhex("25 00 00 03 E8"))
        self.assertEqual(build_control_position_info(-1), bytes.fromhex("26 FF FF FC 18"))
        self.assertEqual(build_control_speed_info(-123), bytes.fromhex("27 FF FF FF 85"))

    def test_identify_motor_over_can_native_field_order(self):
        self.assertEqual(
            build_identify_motor_over_can_info(0x12, 0x34, 1.25, -2.5, 0x56),
            bytes.fromhex("0F 34 12 FF FD 00 7D 56"),
        )

    def test_identify_motor_over_can_uses_native_rounding_and_truncation(self):
        # arg4 is cast to int16 with truncation toward zero; arg3 is *100
        # and rounded to nearest with ties away from zero.
        self.assertEqual(
            build_identify_motor_over_can_info(0x12, 0x34, 1.25, 2.9, 0x56),
            bytes.fromhex("0F 34 12 00 02 00 7D 56"),
        )
        self.assertEqual(
            build_identify_motor_over_can_info(0x12, 0x34, -1.25, -2.9, 0x56),
            bytes.fromhex("0F 34 12 FF FE FF 83 56"),
        )

    def test_control_scaling_rounds_half_away_from_zero(self):
        self.assertEqual(build_control_current_info(0.0005), bytes.fromhex("04 00 00 00 01"))
        self.assertEqual(build_control_current_info(-0.0005), bytes.fromhex("04 FF FF FF FF"))

    def test_imu_calibration_scaling(self):
        self.assertEqual(build_imu_calibration_info(1.234), bytes.fromhex("29 00 00 04 D2"))

    def test_auto_realtime_enable_and_interval(self):
        self.assertEqual(build_auto_realtime_info(True, 100), bytes.fromhex("1A 01 00 64"))
        self.assertEqual(build_auto_realtime_info(False, 0), bytes.fromhex("1A 00 00 00"))

    def test_motor_setup_marker_and_sequence(self):
        values = {"b": {"valType": 2, "valueTET": 1, "value_int": 2}}
        self.assertEqual(
            build_motor_setup_info(["b"], values),
            bytes.fromhex("07 D2 C6 EF 10 02"),
        )
        self.assertEqual(MOTOR_SETUP_MARKER, 0xD2C6EF10)

    def test_motor_signal_setup_optional_second_marker(self):
        motor = {"m": {"valType": 2, "valueTET": 1, "value_int": 1}}
        signal = {"s": {"valType": 2, "valueTET": 1, "value_int": 2}}
        one = build_motor_signal_setup_info(["m"], motor)
        two = build_motor_signal_setup_info(["m"], motor, ["s"], signal)
        self.assertEqual(one, bytes.fromhex("1B D2 C6 EF 10 01"))
        self.assertEqual(two, bytes.fromhex("1B D2 C6 EF 10 01 48 79 18 7D 02"))
        self.assertEqual(MOTOR_SIGNAL_SETUP_MARKER, 0x4879187D)

    def test_topflow_marker(self):
        values = {"x": {"valType": 2, "valueTET": 1, "value_int": 3}}
        self.assertEqual(build_topflow_setup_info(["x"], values), bytes.fromhex("3A 54 46 43 46 03"))
        self.assertEqual(TOPFLOW_SETUP_MARKER, 0x54464346)

    def test_reset_topflow_and_overloaded_reset_variant(self):
        self.assertEqual(build_reset_topflow_info(), b"\x1D")
        self.assertEqual(build_reset_motor_signal_setup_info(1), bytes.fromhex("1D 01"))

    def test_range_and_pair_validation(self):
        with self.assertRaises(SetupValueError):
            build_auto_realtime_info(True, 65536)
        with self.assertRaises(SetupValueError):
            build_reset_motor_signal_setup_info(256)
        with self.assertRaises(SetupValueError):
            build_motor_signal_setup_info(["m"], {"m": {"valType": 2, "valueTET": 1, "value_int": 1}}, ["s"], None)
        with self.assertRaises(SetupValueError):
            build_control_speed_info(float("inf"))


if __name__ == "__main__":
    unittest.main()



class V14CompatibilityRequestBuilderTests(unittest.TestCase):
    def test_uart_can_over_envelope(self):
        self.assertEqual(
            build_can_forward_info(0x2A, 0x04, bytes((0x01, 0x02))),
            bytes.fromhex("10 2A 04 01 02"),
        )

    def test_control_and_obtain_data_once_14_byte_payload(self):
        info = build_v14_control_and_obtain_data_once_info(
            512,
            direction_switch_enabled=True,
            rotation_direction=False,
            gear=2,
            horn=True,
            headlight=False,
            brake_light=True,
            cruise_enabled=True,
            cruise_on=False,
            multi_mode_enabled=True,
            multi_mode=2,
        )
        self.assertEqual(
            info,
            bytes.fromhex("02 02 00 00 00 01 00 02 01 00 01 01 00 01 02"),
        )
        self.assertEqual(len(info) - 1, 14)

    def test_current_gear_and_obtain_data_uses_truncation(self):
        self.assertEqual(
            build_current_gear_and_obtain_data_info(1.2349, 3),
            bytes.fromhex("20 00 00 04 D2 03"),
        )

    def test_v14_reset_reboot_reserved_zero_is_distinct(self):
        self.assertEqual(build_v14_reset_reboot_info(), bytes.fromhex("1D 00"))

    def test_v14_control_ranges(self):
        with self.assertRaises(SetupValueError):
            build_v14_control_and_obtain_data_once_info(1024)
        with self.assertRaises(SetupValueError):
            build_v14_control_and_obtain_data_once_info(100, gear=5)
        with self.assertRaises(SetupValueError):
            build_v14_control_and_obtain_data_once_info(100, multi_mode=3)



class V16CompatibilityRequestBuilderTests(unittest.TestCase):
    def test_v16_cmd02_reserved_bytes_precede_current_code(self):
        info = build_v16_control_and_obtain_data_once_info(512, gear=2)
        self.assertEqual(
            info,
            bytes.fromhex("02 00 00 02 00 00 00 02 00 00 00 00 00 00 00"),
        )
        self.assertEqual(len(info) - 1, 14)

    def test_v16_pas_alias_sets_d0_and_zeroes_ignored_tail(self):
        info = build_v16_pas_gear_control_info(3)
        self.assertEqual(info[0], 0x02)
        self.assertEqual(info[1:], bytes((3,)) + bytes(13))
