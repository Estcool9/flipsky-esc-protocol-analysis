import unittest
from scripts.ftesc_frame import (
    DEFAULT_MAX_PAYLOAD, END_MARKER, EXTENDED_MARKER, SHORT_MARKER,
    FrameError, NeedMoreData, crc16_modbus, decode_frame, decode_frames, encode_frame,
)

class CrcTests(unittest.TestCase):
    def test_modbus_check_vector(self):
        self.assertEqual(crc16_modbus(b"123456789"), 0x4B37)
    def test_empty_crc_initial_value(self):
        self.assertEqual(crc16_modbus(b""), 0xFFFF)

class FrameTests(unittest.TestCase):
    def test_short_round_trip(self):
        payload = bytes.fromhex("01020304")
        wire = encode_frame(payload)
        self.assertEqual((wire[0], wire[1], wire[-1]), (SHORT_MARKER, 4, END_MARKER))
        self.assertEqual(decode_frame(wire).payload, payload)
    def test_extended_round_trip(self):
        payload = bytes(range(256))
        wire = encode_frame(payload)
        self.assertEqual(wire[:3], bytes((EXTENDED_MARKER, 1, 0)))
        self.assertEqual(decode_frame(wire).payload, payload)
    def test_255_bytes_encoded_short(self):
        p = b"A" * 255
        self.assertEqual(encode_frame(p)[0], SHORT_MARKER)
        self.assertEqual(decode_frame(encode_frame(p)).payload, p)
    def test_extended_255_accepted_by_receiver(self):
        p = b"B" * 255
        wire = bytes((EXTENDED_MARKER, 0, 255)) + p + crc16_modbus(p).to_bytes(2, "big") + bytes((END_MARKER,))
        self.assertEqual(decode_frame(wire).payload, p)
    def test_default_maximum_10000(self):
        p = b"Z" * DEFAULT_MAX_PAYLOAD
        self.assertEqual(decode_frame(encode_frame(p)).length, DEFAULT_MAX_PAYLOAD)
    def test_empty_rejected(self):
        with self.assertRaises(FrameError):
            encode_frame(b"")
    def test_bb_254_rejected(self):
        p = b"Q" * 254
        wire = bytes((EXTENDED_MARKER, 0, 254)) + p + b"\x00\x00" + bytes((END_MARKER,))
        with self.assertRaises(FrameError):
            decode_frame(wire)
    def test_crc_corruption_rejected(self):
        wire = bytearray(encode_frame(b"payload")); wire[-3] ^= 1
        with self.assertRaisesRegex(FrameError, "CRC mismatch"):
            decode_frame(wire)
    def test_bad_terminator_rejected(self):
        wire = bytearray(encode_frame(b"payload")); wire[-1] = 0
        with self.assertRaisesRegex(FrameError, "terminator"):
            decode_frame(wire)
    def test_truncated_frame_raises_need_more_data(self):
        with self.assertRaises(NeedMoreData):
            decode_frame(b"\xAA")
        with self.assertRaises(NeedMoreData):
            decode_frame(encode_frame(b"payload")[:-1])
    def test_concatenated_frames(self):
        a, b = encode_frame(b"one"), encode_frame(b"two" * 100)
        self.assertEqual([x.payload for x in decode_frames(a + b)], [b"one", b"two" * 100])

if __name__ == "__main__":
    unittest.main()
