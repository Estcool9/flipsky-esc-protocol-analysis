import unittest

from scripts.ftesc_responses import (
    BooleanAck,
    ImuCalibrationResponse,
    SignalAdcResponse,
    parse_auto_realtime_ack,
    parse_can_forward_response,
    parse_motor_signal_setup_response,
    parse_v16_motor_setup_response,
    parse_v16_motor_signal_setup_response,
    parse_setup_write_ack,
    parse_topflow_setup_response,
    parse_firmware_version_response,
    parse_motor_identify_response,
    parse_text_response,
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

    def test_can_forward_response_uses_slave_command_as_info_command(self):
        result = parse_can_forward_response(bytes.fromhex("04 01 02"), 0x04)
        self.assertEqual(result.slave_command, 0x04)
        self.assertEqual(result.slave_data, bytes((1, 2)))

    def test_motor_signal_setup_response_two_blocks(self):
        from scripts.ftesc_setup_serializer import encode_profile_block
        first = {"a": {"valType": 2, "valueTET": 1, "value_int": 1}}
        second = {"b": {"valType": 2, "valueTET": 1, "value_int": 2}}
        data = encode_profile_block(0xD2C6EF10, ["a"], first)
        data += encode_profile_block(0x4879187D, ["b"], second)
        result = parse_motor_signal_setup_response(bytes((0x1C,)) + data, ["a"], first, ["b"], second)
        self.assertTrue(result.success)
        self.assertEqual(result.secret_key_status, 0)
        self.assertEqual(result.first_block.values["a"]["value_int"], 1)
        self.assertEqual(result.second_block.values["b"]["value_int"], 2)

    def test_v16_motor_setup_response_single_marker_block(self):
        from scripts.ftesc_setup_serializer import encode_profile_block
        metadata = {"motor": {"valType": 2, "valueTET": 1, "value_int": 42}}
        data = encode_profile_block(0xD2C6EF10, ["motor"], metadata)
        result = parse_v16_motor_setup_response(bytes((0x09,)) + data + b"\xAA", ["motor"], metadata)
        self.assertEqual(result.command, 0x09)
        self.assertEqual(result.block.values["motor"]["value_int"], 42)
        self.assertEqual(result.trailing_data, b"\xAA")

    def test_v16_motor_signal_setup_response_single_marker_block(self):
        from scripts.ftesc_setup_serializer import encode_profile_block
        metadata = {"signal": {"valType": 2, "valueTET": 4, "value_int": -7}}
        data = encode_profile_block(0x4879187D, ["signal"], metadata)
        result = parse_v16_motor_signal_setup_response(bytes((0x0A,)) + data, ["signal"], metadata)
        self.assertEqual(result.command, 0x0A)
        self.assertEqual(result.block.values["signal"]["value_int"], -7)
        self.assertEqual(result.trailing_data, b"")

    def test_v16_single_setup_response_rejects_marker_mismatch(self):
        from scripts.ftesc_setup_serializer import encode_profile_block, SetupValueError
        metadata = {"signal": {"valType": 2, "valueTET": 1, "value_int": 1}}
        wrong_marker = encode_profile_block(0xD2C6EF10, ["signal"], metadata)
        with self.assertRaises(SetupValueError):
            parse_v16_motor_signal_setup_response(bytes((0x0A,)) + wrong_marker, ["signal"], metadata)

    def test_topflow_setup_response_uses_generic_metadata(self):
        from scripts.ftesc_setup_serializer import encode_profile_block
        metadata = {"x": {"valType": 2, "valueTET": 1, "value_int": 3}}
        data = encode_profile_block(0x54464346, ["x"], metadata)
        result = parse_topflow_setup_response(bytes((0x3B,)) + data, 0x3B, ["x"], metadata)
        self.assertEqual(result.block.values["x"]["value_int"], 3)
        self.assertTrue(result.success)

    def test_setup_status_ack_commands(self):
        for command in (0x1B, 0x1D, 0x3A, 0x3D):
            result = parse_setup_write_ack(bytes((command,)), command)
            self.assertTrue(result.acknowledged)
        with self.assertRaises(ValueError):
            parse_setup_write_ack(bytes((0x1B, 0x00)), 0x1B)

    def test_firmware_version_response_layout(self):
        info = bytes((0x11, 1, 7, 0xEF)) + b"FTESC-1.7" + bytes((3,))
        result = parse_firmware_version_response(info)
        self.assertEqual((result.major, result.minor, result.boot_mode_flag), (1, 7, 0xEF))
        self.assertEqual(result.hardware_name, "FTESC-1.7")
        self.assertEqual(result.hardware_serial_number, 3)

    def test_motor_identify_response_string_and_bool(self):
        result = parse_motor_identify_response(bytes((0x0F,)) + b"motor ok" + bytes((1,)))
        self.assertEqual(result.label, "motor ok")
        self.assertTrue(result.success)

    def test_terminal_and_samples_text(self):
        self.assertEqual(parse_text_response(bytes((0x14,)) + b"ready", 0x14).text, "ready")
        self.assertEqual(parse_text_response(bytes((0x24,)) + b"sample", 0x24).text, "sample")

    def test_uuid_response_preserves_raw_key_bytes(self):
        uuid = bytes(range(16))
        self.assertEqual(parse_uuid_response(bytes((0x21,)) + uuid), uuid)

    def test_imu_calibration_rejects_bad_length(self):
        with self.assertRaises(ValueError):
            parse_imu_calibration_response(b"\x29" + bytes(32))


if __name__ == "__main__":
    unittest.main()
