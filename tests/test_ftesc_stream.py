import random
import unittest
from scripts.ftesc_frame import encode_frame
from scripts.ftesc_stream import FrameStreamDecoder

class FrameStreamDecoderTests(unittest.TestCase):
    def setUp(self):
        self.short = encode_frame(b"\x00\x01\x02")
        self.extended = encode_frame(bytes(range(256)))

    def test_every_split_point_short_frame(self):
        for split in range(len(self.short) + 1):
            decoder = FrameStreamDecoder()
            frames = decoder.feed(self.short[:split]) + decoder.feed(self.short[split:])
            self.assertEqual([f.payload for f in frames], [b"\x00\x01\x02"])
            self.assertEqual(decoder.buffered_bytes, 0)

    def test_every_split_point_extended_frame(self):
        expected = bytes(range(256))
        for split in range(len(self.extended) + 1):
            decoder = FrameStreamDecoder()
            frames = decoder.feed(self.extended[:split]) + decoder.feed(self.extended[split:])
            self.assertEqual([f.payload for f in frames], [expected])
            self.assertEqual(decoder.buffered_bytes, 0)

    def test_one_byte_at_a_time(self):
        decoder, frames = FrameStreamDecoder(), []
        for byte in self.extended:
            frames.extend(decoder.feed(bytes([byte])))
        self.assertEqual([f.payload for f in frames], [bytes(range(256))])

    def test_concatenated_frames(self):
        decoder = FrameStreamDecoder()
        frames = decoder.feed(self.short + self.extended + self.short)
        self.assertEqual([f.payload for f in frames],
                         [b"\x00\x01\x02", bytes(range(256)), b"\x00\x01\x02"])

    def test_random_chunk_boundaries(self):
        wire, rng = self.short + self.extended + self.short, random.Random(0xF17E5)
        for _ in range(100):
            decoder, frames, offset = FrameStreamDecoder(), [], 0
            while offset < len(wire):
                width = rng.randint(1, 17)
                frames.extend(decoder.feed(wire[offset:offset + width]))
                offset += width
            self.assertEqual(len(frames), 3)
            self.assertEqual(decoder.buffered_bytes, 0)

    def test_leading_garbage_resynchronizes(self):
        decoder = FrameStreamDecoder()
        frames = decoder.feed(b"\x00\x01garbage" + self.short)
        self.assertEqual([f.payload for f in frames], [b"\x00\x01\x02"])
        self.assertGreaterEqual(decoder.discarded_bytes, 7)

    def test_bad_crc_discards_one_byte_then_finds_next_frame(self):
        bad = bytearray(self.short)
        bad[-3] ^= 0x80
        decoder = FrameStreamDecoder()
        frames = decoder.feed(bytes(bad) + self.short)
        self.assertEqual([f.payload for f in frames], [b"\x00\x01\x02"])
        self.assertGreater(decoder.invalid_candidates, 0)

    def test_bad_terminator_resynchronizes(self):
        bad = self.short[:-1] + b"\x00"
        decoder = FrameStreamDecoder()
        frames = decoder.feed(bad + self.short)
        self.assertEqual([f.payload for f in frames], [b"\x00\x01\x02"])

    def test_incomplete_frame_is_preserved_until_reset(self):
        decoder = FrameStreamDecoder()
        self.assertEqual(decoder.feed(self.short[:-1]), [])
        self.assertEqual(decoder.buffered_bytes, len(self.short) - 1)
        decoder.reset()
        self.assertEqual(decoder.buffered_bytes, 0)
        frames = decoder.feed(self.short)
        self.assertEqual([f.payload for f in frames], [b"\x00\x01\x02"])

    def test_statistics(self):
        decoder = FrameStreamDecoder()
        decoder.feed(b"noise" + self.short)
        stats = decoder.stats()
        self.assertEqual(stats.frames, 1)
        self.assertEqual(stats.buffered_bytes, 0)
        self.assertGreaterEqual(stats.discarded_bytes, 5)

if __name__ == "__main__":
    unittest.main()
