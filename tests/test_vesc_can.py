import unittest

from scripts.vesc_can import (
    VescCanCommand,
    VescCanError,
    build_brake_current,
    build_current,
    build_duty,
    build_position,
    build_rpm,
    decode_identifier,
    encode_identifier,
)


class VescCanIdentifierTests(unittest.TestCase):
    def test_v1_c_layout_target_low_command_high(self):
        can_id = encode_identifier(0x2A, VescCanCommand.SET_CURRENT)
        self.assertEqual(can_id, 0x12A)
        decoded = decode_identifier(can_id)
        self.assertEqual(decoded.controller_id, 0x2A)
        self.assertEqual(decoded.command_id, 0x01)

    def test_reserved_high_identifier_bits_are_preserved(self):
        decoded = decode_identifier(0x1234512A)
        self.assertEqual(decoded.controller_id, 0x2A)
        self.assertEqual(decoded.command_id, 0x51)
        self.assertEqual(decoded.reserved, 0x123)

    def test_invalid_identifiers_are_rejected(self):
        for bad in (-1, 0x20000000, True):
            with self.subTest(bad=bad):
                with self.assertRaises(VescCanError):
                    decode_identifier(bad)

    def test_identifier_components_are_one_byte(self):
        with self.assertRaises(VescCanError):
            encode_identifier(256, 0)
        with self.assertRaises(VescCanError):
            encode_identifier(0, -1)


class VescCanCommandTests(unittest.TestCase):
    def test_basic_control_scalings(self):
        self.assertEqual(build_duty(1, 0.25).data.hex(), "000061a8")
        self.assertEqual(build_current(1, 12.5).data.hex(), "000030d4")
        self.assertEqual(build_brake_current(1, 5.0).data.hex(), "00001388")
        self.assertEqual(build_rpm(1, 1000).data.hex(), "000003e8")
        self.assertEqual(build_position(1, 10.0).data.hex(), "00989680")

    def test_control_identifier_uses_correct_command_namespace(self):
        self.assertEqual(build_duty(1, 0.5).can_id, 0x0001)
        self.assertEqual(build_current(1, 10.0).can_id, 0x0101)
        self.assertEqual(build_brake_current(1, 5.0).can_id, 0x0201)
        self.assertEqual(build_rpm(1, 1000).can_id, 0x0301)
        self.assertEqual(build_position(1, 10.0).can_id, 0x0401)

    def test_duty_and_position_range_validation(self):
        with self.assertRaises(VescCanError):
            build_duty(1, 1.1)
        with self.assertRaises(VescCanError):
            build_position(1, 181.0)

    def test_non_finite_and_overflow_are_rejected(self):
        with self.assertRaises(VescCanError):
            build_current(1, float("nan"))
        with self.assertRaises(VescCanError):
            build_current(1, 1e20)


if __name__ == "__main__":
    unittest.main()
