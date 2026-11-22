import unittest

from scripts.ftesc_responses import (
    BooleanAck,
    ImuCalibrationResponse,
    SignalAdcResponse,
    parse_auto_realtime_ack,
    parse_boolean_ack,
    parse_imu_calibration_response,
    parse_signal_adc_response,
    parse_signal_ppm_response,
    parse_uuid_response,
)


def i32(value):
    return int(value).to_bytes(4, "big", signed=True)


class V17ResponseDecoderTests(unittest.TestCase):
    def test_ppm_response_scaled_signed_i32(self):
        self.assertAlmostEqual(parse_signal_ppm_response(b"\x0D" + i32(-500_000)), -0.5)

    def test_adc_response_has_six_values_and_mixed_scales(self):
        values = (1_000_000, -2_000_000, 3, 4, 5, -6_000_000)
        info = b"\x0E" + b"".join(i32(v) for v in values)
        result = parse_signal_adc_response(info)
        self.assertIsInstance(result, SignalAdcResponse)
        self.assertEqual(result.values, (1.0, -2.0, 3.0, 4.0, 5.0, -6.0))

    def test_boolean_ack_commands(self):
        for cmd in (0x16, 0x18, 0x22):
            self.assertEqual(parse_boolean_ack(bytes((cmd, 1)), cmd), BooleanAck(cmd, True))
            self.assertEqual(parse_boolean_ack(bytes((cmd, 0)), cmd), BooleanAck(cmd, False))

    def test_boolean_ack_rejects_wrong_command_or_length(self):
        with self.assertRaises(ValueError):
            parse_boolean_ack(b"\x16\x01", 0x18)
        with self.assertRaises(ValueError):
            parse_boolean_ack(b"\x16\x01\x00", 0x16)

    def test_auto_realtime_ack_is_no_data(self):
        self.assertIsNone(parse_auto_realtime_ack(b"\x1A"))
        with self.assertRaises(ValueError):
            parse_auto_realtime_ack(b"\x1A\x00")

    def test_imu_calibration_nine_values(self):
        info = b"\x29" + b"".join(i32(n * 1_000_000) for n in range(1, 10))
        result = parse_imu_calibration_response(info)
        self.assertIsInstance(result, ImuCalibrationResponse)
        self.assertEqual(result.values, tuple(float(n) for n in range(1, 10)))

    def test_uuid_response_preserves_raw_key_bytes(self):
        uuid = bytes(range(16))
        self.assertEqual(parse_uuid_response(bytes((0x21,)) + uuid), uuid)

    def test_imu_calibration_rejects_bad_length(self):
        with self.assertRaises(ValueError):
            parse_imu_calibration_response(b"\x29" + bytes(32))


if __name__ == "__main__":
    unittest.main()
