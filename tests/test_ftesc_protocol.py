import unittest

from scripts.ftesc_frame import FrameError, decode_frame, encode_frame
from scripts.ftesc_protocol import (
    CommandId,
    build_info,
    decode_command_frame,
    encode_command,
    parse_all_esc_ids,
    parse_auto_realtime_config,
    parse_info,
    parse_motor_telemetry_02_or_20,
    parse_realtime_data_00,
    parse_realtime_data_00_v17_angular_extension,
    parse_realtime_data_00_v17_extension,
)


def put_signed(buf: bytearray, offset: int, size: int, value: int) -> None:
    buf[offset:offset + size] = value.to_bytes(size, "big", signed=True)


class CommandEnvelopeTests(unittest.TestCase):
    def test_build_info_prepends_command(self):
        self.assertEqual(build_info(CommandId.OBTAIN_DATA_ONCE), b"\x00")

    def test_encode_decode_command_frame(self):
        wire = encode_command(CommandId.OBTAIN_DATA_ONCE)
        frame, message = decode_command_frame(wire)
        self.assertEqual(frame.payload, b"\x00")
        self.assertEqual(message.command, 0x00)
        self.assertEqual(message.data, b"")

    def test_control_request_info_length_is_15(self):
        data = bytes(range(14))
        wire = encode_command(CommandId.CONTROL_AND_OBTAIN_DATA_ONCE, data)
        self.assertEqual(decode_frame(wire).payload, b"\x02" + data)
        self.assertEqual(len(decode_frame(wire).payload), 15)

    def test_info_requires_command_byte(self):
        with self.assertRaises(ValueError):
            parse_info(b"")


class RealtimeTelemetryTests(unittest.TestCase):
    def make_data(self, extended=False):
        d = bytearray(44 if extended else 28)
        d[0] = 4
        d[1] = 0
        put_signed(d, 2, 2, 4800)
        put_signed(d, 4, 4, 2_500_000)
        put_signed(d, 8, 4, -1_200_000)
        put_signed(d, 12, 4, 1200)
        put_signed(d, 16, 2, 2500)
        put_signed(d, 18, 2, 5500)
        put_signed(d, 20, 2, 4200)
        put_signed(d, 22, 2, 1250)
        put_signed(d, 24, 4, 12_345_678)
        if extended:
            d[28:40] = bytes(range(12))
            put_signed(d, 40, 4, 900)
        return bytes(d)

    def test_base_realtime_response(self):
        parsed = parse_realtime_data_00(b"\x00" + self.make_data())
        self.assertEqual(parsed.controller_id, 4)
        self.assertEqual(parsed.battery_voltage_v, 48.0)
        self.assertEqual(parsed.battery_current_a, 2.5)
        self.assertEqual(parsed.motor_current_a, -1.2)
        self.assertEqual(parsed.motor_erpm, 1200)
        self.assertEqual(parsed.duty_cycle, 0.25)
        self.assertEqual(parsed.mosfet_temperature_c, 55.0)
        self.assertEqual(parsed.motor_temperature_c, 42.0)
        self.assertEqual(parsed.cpu_utilization, 0.125)
        self.assertAlmostEqual(parsed.encoder_angle_degrees, 12.345678)
        self.assertIsNone(parsed.pas_rpm)

    def test_extended_auto_report_contains_reserved_and_pas_rpm(self):
        parsed = parse_realtime_data_00(b"\x00" + self.make_data(extended=True))
        self.assertEqual(parsed.reserved_extension, bytes(range(12)))
        self.assertEqual(parsed.pas_rpm, 900)

    def test_v17_angular_extension_converts_micro_radians_to_degrees(self):
        d = bytearray(self.make_data(extended=True))
        put_signed(d, 28, 4, 1_000_000)
        put_signed(d, 32, 4, -500_000)
        put_signed(d, 36, 4, 0)
        angles = parse_realtime_data_00_v17_angular_extension(b"\x00" + d)
        self.assertAlmostEqual(angles[0], 57.295779513, places=8)
        self.assertAlmostEqual(angles[1], -28.647889756, places=8)
        self.assertEqual(angles[2], 0.0)

    def test_v17_angular_extension_requires_extended_response(self):
        with self.assertRaises(ValueError):
            parse_realtime_data_00_v17_angular_extension(b"\x00" + self.make_data())


    def test_v17_extension_includes_three_angles_and_pas_rpm(self):
        d = bytearray(self.make_data(extended=True))
        put_signed(d, 28, 4, 1_000_000)
        put_signed(d, 32, 4, -500_000)
        put_signed(d, 36, 4, 0)
        put_signed(d, 40, 4, 900)
        parsed = parse_realtime_data_00_v17_extension(b"\x00" + d)
        self.assertAlmostEqual(parsed.angular_value_1_degrees, 57.295779513, places=8)
        self.assertAlmostEqual(parsed.angular_value_2_degrees, -28.647889756, places=8)
        self.assertEqual(parsed.angular_value_3_degrees, 0.0)
        self.assertEqual(parsed.pas_rpm, 900)

    def test_v17_extension_rejects_wrong_command(self):
        with self.assertRaises(ValueError):
            parse_realtime_data_00_v17_extension(b"\x01" + self.make_data(extended=True))

    def test_realtime_response_rejects_wrong_size(self):
        with self.assertRaises(ValueError):
            parse_realtime_data_00(b"\x00" + bytes(27))


class MotorTelemetryTests(unittest.TestCase):
    def make_data(self, pas=False):
        d = bytearray(31 if pas else 27)
        d[0] = 0  # error code
        put_signed(d, 1, 2, 4800)
        put_signed(d, 3, 4, 2_500_000)
        put_signed(d, 7, 4, -1_200_000)
        put_signed(d, 11, 4, 1200)
        put_signed(d, 15, 2, 2500)
        put_signed(d, 17, 2, 5500)
        put_signed(d, 19, 2, 4200)
        put_signed(d, 21, 2, 1250)
        put_signed(d, 23, 4, 12_345_678)
        if pas:
            put_signed(d, 27, 4, 900)
        return d

    def test_command_02_common_response(self):
        parsed = parse_motor_telemetry_02_or_20(b"\x02" + self.make_data())
        self.assertEqual(parsed.battery_voltage_v, 48.0)
        self.assertEqual(parsed.motor_current_a, -1.2)
        self.assertAlmostEqual(parsed.encoder_angle_degrees, 12.345678)

    def test_command_20_response(self):
        parsed = parse_motor_telemetry_02_or_20(b"\x20" + self.make_data())
        self.assertEqual(parsed.motor_erpm, 1200)

    def test_pas_mode_extension(self):
        parsed = parse_motor_telemetry_02_or_20(b"\x02" + self.make_data(pas=True))
        self.assertEqual(parsed.pas_rpm, 900)

    def test_motor_response_rejects_other_command(self):
        with self.assertRaises(ValueError):
            parse_motor_telemetry_02_or_20(b"\x00" + bytes(27))


class OtherResponseTests(unittest.TestCase):
    def test_master_and_slave_ids(self):
        self.assertEqual(parse_all_esc_ids(b"\x1e\x05\x06\x07"), (5, (6, 7)))

    def test_can_id_over_can_response(self):
        self.assertEqual(parse_all_esc_ids(b"\\x01\\x02\\x03"), (2, (3,)))

    def test_auto_realtime_config(self):
        info = b"\x1a\x01\x00\x64\x12\x34\x56\x78"
        self.assertEqual(parse_auto_realtime_config(info), (1, 100, 0x12345678))


if __name__ == "__main__":
    unittest.main()
