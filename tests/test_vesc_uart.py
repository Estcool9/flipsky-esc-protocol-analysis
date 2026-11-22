import unittest

from scripts.vesc_uart import (
    NeedMoreData,
    VescFrameError,
    crc16_vesc,
    decode_frame,
    encode_frame,
    extract_complete_frame_length,
)


class VescUartCrcTests(unittest.TestCase):
    def test_flipsky_v1_vector_get_values(self):
        self.assertEqual(crc16_vesc(b"\x04"), 0x4084)
        self.assertEqual(encode_frame(b"\x04"), bytes.fromhex("02 01 04 40 84 03"))

    def test_crc_xmodem_check_vector(self):
        self.assertEqual(crc16_vesc(b"123456789"), 0x31C3)


class VescUartFrameTests(unittest.TestCase):
    def test_short_round_trip(self):
        frame = encode_frame(b"\x04")
        self.assertEqual(decode_frame(frame).info, b"\x04")
        self.assertEqual(extract_complete_frame_length(frame), len(frame))

    def test_medium_round_trip_and_big_endian_length(self):
        info = b"\x20" + bytes(range(255))
        frame = encode_frame(info)
        self.assertEqual(frame[:3], bytes.fromhex("03 01 00"))
        parsed = decode_frame(frame)
        self.assertEqual(parsed.info, info)

    def test_long_round_trip_and_big_endian_length(self):
        info = b"\x20" + bytes(65535)
        frame = encode_frame(info)
        self.assertEqual(frame[:4], bytes.fromhex("04 01 00 00"))
        self.assertEqual(decode_frame(frame).info, info)

    def test_empty_info_rejected(self):
        with self.assertRaises(VescFrameError):
            encode_frame(b"")

    def test_bad_start_terminator_crc_and_trailing_bytes_rejected(self):
        frame = bytearray(encode_frame(b"\x04"))
        frame[0] = 0xAA
        with self.assertRaises(VescFrameError):
            decode_frame(frame)
        frame = bytearray(encode_frame(b"\x04"))
        frame[-1] = 0xDD
        with self.assertRaises(VescFrameError):
            decode_frame(frame)
        frame = bytearray(encode_frame(b"\x04"))
        frame[-2] ^= 1
        with self.assertRaises(VescFrameError):
            decode_frame(frame)
        frame = encode_frame(b"\x04") + b"X"
        with self.assertRaises(VescFrameError):
            decode_frame(frame)

    def test_truncated_frame_is_distinct_from_invalid(self):
        with self.assertRaises(NeedMoreData):
            decode_frame(b"\x03\x00")
        with self.assertRaises(NeedMoreData):
            decode_frame(b"\x02\x01\x04")


if __name__ == "__main__":
    unittest.main()
