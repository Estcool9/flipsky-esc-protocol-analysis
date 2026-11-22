import unittest

from scripts.vesc_uart import encode_frame
from scripts.vesc_stream import VescStreamDecoder


class VescStreamDecoderTests(unittest.TestCase):
    def test_fragmented_frame_is_buffered_until_complete(self):
        frame = encode_frame(b"\\x04\\x10\\x20")
        decoder = VescStreamDecoder()
        self.assertEqual(decoder.feed(frame[:2]), [])
        self.assertEqual(decoder.buffered_bytes, 2)
        self.assertEqual(decoder.feed(frame[2:]), [__import__(
            "scripts.vesc_uart", fromlist=["decode_frame"]
        ).decode_frame(frame)])
        self.assertEqual(decoder.buffered_bytes, 0)

    def test_concatenated_frames(self):
        frames = [encode_frame(bytes((cmd,))) for cmd in (0x04, 0x05, 0x06)]
        decoded = VescStreamDecoder().feed(b"".join(frames))
        self.assertEqual([item.info for item in decoded], [b"\\x04", b"\\x05", b"\\x06"])

    def test_leading_noise_is_discarded(self):
        decoder = VescStreamDecoder()
        decoded = decoder.feed(b"noise" + encode_frame(b"\\x04"))
        self.assertEqual([item.info for item in decoded], [b"\\x04"])
        self.assertEqual(decoder.stats.discarded_bytes, 5)

    def test_bad_crc_recovers_to_following_frame(self):
        bad = bytearray(encode_frame(b"\\x04"))
        bad[-2] ^= 0x80
        good = encode_frame(b"\\x05")
        decoder = VescStreamDecoder()
        decoded = decoder.feed(bytes(bad) + good)
        self.assertEqual([item.info for item in decoded], [b"\\x05"])
        self.assertGreater(decoder.stats.discarded_bytes, 0)

    def test_medium_and_long_frames(self):
        medium = encode_frame(b"\\x20" + bytes(255))
        long_frame = encode_frame(b"\\x21" + bytes(65535))
        decoder = VescStreamDecoder()
        decoded = decoder.feed(medium + long_frame)
        self.assertEqual([len(item.info) for item in decoded], [256, 65536])

    def test_configured_length_limit_rejects_oversized_candidate(self):
        decoder = VescStreamDecoder(max_info_length=16)
        oversized_header = bytes.fromhex("04 00 00 20")
        decoded = decoder.feed(oversized_header + encode_frame(b"\\x04"))
        self.assertEqual([item.info for item in decoded], [b"\\x04"])

    def test_reset_clears_buffer_and_statistics(self):
        decoder = VescStreamDecoder()
        decoder.feed(b"\\x02")
        self.assertEqual(decoder.buffered_bytes, 1)
        decoder.reset()
        self.assertEqual(decoder.stats.frames, 0)
        self.assertEqual(decoder.stats.discarded_bytes, 0)
        self.assertEqual(decoder.buffered_bytes, 0)


if __name__ == "__main__":
    unittest.main()
