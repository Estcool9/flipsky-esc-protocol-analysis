import unittest

from scripts.ftesc_can import (
    CAN_ESC_REALTIME_DATA_0,
    CAN_ESC_REALTIME_DATA_1,
    CAN_ESC_REALTIME_DATA_2,
    CanRealtimeData0,
    CanRealtimeData1,
    CanRealtimeData2,
    decode_can_identifier,
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

    def test_rejects_wrong_fixed_identifier_prefix(self):
        with self.assertRaises(ValueError):
            decode_can_identifier(0x00002A0B)

    def test_unchecksummed_command_is_marked_unknown(self):
        frame = parse_can_frame(encode_can_identifier(1, 0x15), b"12345")
        self.assertIsNone(frame.crc_valid)


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
