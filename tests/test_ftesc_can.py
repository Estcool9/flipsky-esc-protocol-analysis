import unittest

from scripts.ftesc_can import (
    CAN_ESC_REALTIME_DATA_0,
    CAN_ESC_REALTIME_DATA_1,
    CAN_ESC_REALTIME_DATA_2,
    CanRealtimeData0,
    CanRealtimeData1,
    CanRealtimeData2,
    decode_can_identifier,
    build_can_current_gear_crc16,
    build_can_brake_current_crc16,
    build_can_duty_gear_crc16,
    build_can_current_percent_crc16,
    build_can_current_percent_gear_crc16,
    build_can_brake_current_percent_crc16,
    build_can_erpm_gear_crc16,
    build_can_position_gear_crc16,
    build_can_id_current_crc16,
    build_can_current_gear,
    build_can_current_percent_gear,
    build_can_duty_gear,
    build_can_erpm_gear,
    build_can_position_gear,
    build_can_brake_current,
    build_can_brake_current_percent,
    decode_realtime_data,
    encode_can_identifier,
    parse_can_frame,
)
from scripts.ftesc_frame import crc16_modbus


def with_crc(payload):
    return payload + crc16_modbus(payload).to_bytes(2, "big")


class CanIdentifierTests(unittest.TestCase):
    def test_encode_and_decode_extended_identifier(self):
        raw = encode_can_identifier(0x2A, CAN_ESC_REALTIME_DATA_0)
        decoded = decode_can_identifier(raw)
        self.assertEqual(decoded.esc_id, 0x2A)
        self.assertEqual(decoded.command, CAN_ESC_REALTIME_DATA_0)

    def test_rejects_identifier_outside_29_bits(self):
        with self.assertRaises(ValueError):
            decode_can_identifier(0x20000000)

    def test_rejects_boolean_identifier(self):
        with self.assertRaises(ValueError):
            decode_can_identifier(True)

    def test_rejects_wrong_fixed_identifier_prefix(self):
        with self.assertRaises(ValueError):
            decode_can_identifier(0x00002A0B)

    def test_rejects_payload_over_classic_can_limit(self):
        with self.assertRaises(ValueError):
            parse_can_frame(encode_can_identifier(1, 0x15), bytes(9))

    def test_unchecksummed_command_is_marked_unknown(self):
        frame = parse_can_frame(encode_can_identifier(1, 0x15), b"12345")
        self.assertIsNone(frame.crc_valid)


class CanControlEncoderTests(unittest.TestCase):
    def test_crc_control_builders_encode_expected_commands(self):
        cases = [
            (build_can_current_gear_crc16(7, 1.23456, 2), 0x00, 7),
            (build_can_brake_current_crc16(7, -1.5), 0x01, 6),
            (build_can_duty_gear_crc16(7, 0.25, 1), 0x02, 7),
            (build_can_current_percent_crc16(7, 25.0), 0x03, 6),
            (build_can_current_percent_gear_crc16(7, 25.0, 3), 0x04, 7),
            (build_can_brake_current_percent_crc16(7, 12.5), 0x05, 6),
            (build_can_erpm_gear_crc16(7, -1234, 2), 0x12, 7),
            (build_can_position_gear_crc16(7, -0.5, 4), 0x13, 7),
            (build_can_id_current_crc16(7, 0.5), 0x14, 6),
        ]
        for frame, command, length in cases:
            self.assertEqual(frame.identifier.command, command)
            self.assertEqual(frame.identifier.esc_id, 7)
            self.assertEqual(len(frame.data), length)
            self.assertTrue(frame.crc_valid)
            self.assertTrue(parse_can_frame(frame.identifier.raw, frame.data).crc_valid)

    def test_non_crc_control_builders_encode_expected_commands(self):
        cases = [
            (build_can_current_gear(3, 1.0, 2), 0x15, 5),
            (build_can_current_percent_gear(3, 50.0, 2), 0x16, 5),
            (build_can_duty_gear(3, 0.25, 2), 0x17, 5),
            (build_can_erpm_gear(3, 1500, 2), 0x18, 5),
            (build_can_position_gear(3, 1.25, 2), 0x19, 5),
            (build_can_brake_current(3, 1.0), 0x1A, 4),
            (build_can_brake_current_percent(3, 50.0), 0x1B, 4),
        ]
        for frame, command, length in cases:
            self.assertEqual(frame.identifier.command, command)
            self.assertEqual(len(frame.data), length)
            self.assertIsNone(frame.crc_valid)

    def test_crc_current_builder_uses_truncation_toward_zero(self):
        frame = build_can_current_gear_crc16(1, 1.234569, 2)
        self.assertEqual(frame.data[:5], bytes.fromhex("00 01 E2 40 02"))

    def test_control_builder_rejects_invalid_gear_and_id(self):
        with self.assertRaises(ValueError):
            build_can_current_gear_crc16(1, 1.0, 5)
        with self.assertRaises(ValueError):
            build_can_current_gear_crc16(256, 1.0, 1)


class CanTelemetryTests(unittest.TestCase):
    def test_realtime_data_0_signed_currents(self):
        payload = with_crc(bytes.fromhex("00 27 10 FF FF 38"))
        result = decode_realtime_data(encode_can_identifier(7, CAN_ESC_REALTIME_DATA_0), payload)
        self.assertIsInstance(result, CanRealtimeData0)
        self.assertAlmostEqual(result.motor_current_a, 10.0)
        self.assertAlmostEqual(result.battery_current_a, -0.2)

    def test_realtime_data_1_erpm_and_duty(self):
        payload = with_crc(bytes.fromhex("00 01 F4 00 00 C8"))
        result = decode_realtime_data(encode_can_identifier(8, CAN_ESC_REALTIME_DATA_1), payload)
        self.assertIsInstance(result, CanRealtimeData1)
        self.assertEqual(result.motor_erpm, 500)
        self.assertAlmostEqual(result.duty, 0.2)

    def test_realtime_data_2_temperatures_and_voltage(self):
        payload = with_crc(bytes.fromhex("07 D0 09 C4 2E E0"))
        result = decode_realtime_data(encode_can_identifier(9, CAN_ESC_REALTIME_DATA_2), payload)
        self.assertIsInstance(result, CanRealtimeData2)
        self.assertAlmostEqual(result.mosfet_temperature_c, 20.0)
        self.assertAlmostEqual(result.motor_temperature_c, 25.0)
        self.assertAlmostEqual(result.battery_voltage_v, 120.0)

    def test_rejects_bad_crc(self):
        payload = bytearray(with_crc(bytes.fromhex("00 27 10 FF FF 38")))
        payload[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "CRC mismatch"):
            decode_realtime_data(encode_can_identifier(7, CAN_ESC_REALTIME_DATA_0), payload)

    def test_rejects_wrong_telemetry_length(self):
        with self.assertRaisesRegex(ValueError, "requires 8"):
            decode_realtime_data(encode_can_identifier(7, CAN_ESC_REALTIME_DATA_0), with_crc(b"123"))


if __name__ == "__main__":
    unittest.main()
