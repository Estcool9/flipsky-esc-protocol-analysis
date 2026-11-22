import struct
import unittest

from scripts.ftesc_setup_serializer import SetupValueError, decode_profile_block, encode_profile_block, encode_setup_block, encode_setup_value


class SetupValueSerializerTests(unittest.TestCase):
    def test_float_tet_7_scaled_signed_16(self):
        self.assertEqual(encode_setup_value(val_type=1, value_tet=7, value_dou=-1.25, eval_scl=100),
                         struct.pack(">h", -125))

    def test_float_tet_7_rounds_away_from_zero(self):
        self.assertEqual(encode_setup_value(val_type=1, value_tet=7, value_dou=1.235, eval_scl=100),
                         struct.pack(">h", 124))

    def test_float_tet_8_scaled_signed_32(self):
        self.assertEqual(encode_setup_value(val_type=1, value_tet=8, value_dou=12.5, eval_scl=1000),
                         struct.pack(">i", 12500))

    def test_float_tet_9_ieee754_big_endian(self):
        self.assertEqual(encode_setup_value(val_type=1, value_tet=9, value_dou=1.5),
                         struct.pack(">f", 1.5))

    def test_integer_tet_widths(self):
        self.assertEqual(encode_setup_value(val_type=2, value_tet=1, value_int=0xAB), b"\xAB")
        self.assertEqual(encode_setup_value(val_type=2, value_tet=3, value_int=0x1234), b"\x12\x34")
        self.assertEqual(encode_setup_value(val_type=2, value_tet=4, value_int=-2), b"\xFF\xFE")
        self.assertEqual(encode_setup_value(val_type=2, value_tet=5, value_int=0x12345678), b"\x12\x34\x56\x78")
        self.assertEqual(encode_setup_value(val_type=2, value_tet=6, value_int=-2), b"\xFF\xFF\xFF\xFE")

    def test_other_value_types_emit_one_byte(self):
        for val_type in (4, 6, 7):
            self.assertEqual(encode_setup_value(val_type=val_type, value_tet=1, value_int=1), b"\x01")

    def test_profile_block_uses_value_sequence_order(self):
        values = {
            "alpha": {"valType": 2, "valueTET": 1, "value_int": 1},
            "beta": {"valType": 2, "valueTET": 1, "value_int": 2},
        }
        encoded = encode_profile_block(0x12345678, ["beta", "alpha"], values)
        self.assertEqual(encoded, bytes.fromhex("12 34 56 78 02 01"))

    def test_signed_byte_tets_and_value_types(self):
        self.assertEqual(encode_setup_value(val_type=2, value_tet=2, value_int=-12), b"\\xF4")
        for val_type in (4, 6, 7):
            self.assertEqual(encode_setup_value(val_type=val_type, value_tet=1, value_int=-3), b"\\xFD")

    def test_decode_profile_block_all_observed_types(self):
        marker = 0xD2C6EF10
        metadata = {
            "f16": {"valType": 1, "valueTET": 7, "value_dou": 1.235, "evalScl": 100},
            "f32": {"valType": 1, "valueTET": 8, "value_dou": -1.234, "evalScl": 1000},
            "fieee": {"valType": 1, "valueTET": 9, "value_dou": 3.5},
            "u8": {"valType": 2, "valueTET": 1, "value_int": 255},
            "i8": {"valType": 2, "valueTET": 2, "value_int": -12},
            "u16": {"valType": 2, "valueTET": 3, "value_int": 0x1234},
            "i16": {"valType": 2, "valueTET": 4, "value_int": -123},
            "u32": {"valType": 2, "valueTET": 5, "value_int": 0x12345678},
            "i32": {"valType": 2, "valueTET": 6, "value_int": -123456},
            "flag4": {"valType": 4, "valueTET": 1, "value_int": -3},
            "flag6": {"valType": 6, "valueTET": 1, "value_int": 2},
            "flag7": {"valType": 7, "valueTET": 1, "value_int": 3},
        }
        order = list(metadata)
        encoded = encode_profile_block(marker, order, metadata)
        decoded = decode_profile_block(encoded, marker, order, metadata)
        self.assertEqual(decoded.next_offset, len(encoded))
        self.assertEqual(decoded.values["f16"]["value_dou"], 1.24)
        self.assertEqual(decoded.values["f32"]["value_dou"], -1.234)
        self.assertEqual(decoded.values["fieee"]["value_dou"], 3.5)
        self.assertEqual(decoded.values["u8"]["value_int"], 255)
        self.assertEqual(decoded.values["i8"]["value_int"], -12)
        self.assertEqual(decoded.values["u16"]["value_int"], 0x1234)
        self.assertEqual(decoded.values["i16"]["value_int"], -123)
        self.assertEqual(decoded.values["u32"]["value_int"], 0x12345678)
        self.assertEqual(decoded.values["i32"]["value_int"], -123456)
        self.assertEqual(decoded.values["flag4"]["value_int"], -3)

    def test_decode_two_consecutive_marker_blocks(self):
        first_meta = {"a": {"valType": 2, "valueTET": 1, "value_int": 1}}
        second_meta = {"b": {"valType": 2, "valueTET": 1, "value_int": 2}}
        first = encode_profile_block(0xD2C6EF10, ["a"], first_meta)
        second = encode_profile_block(0x4879187D, ["b"], second_meta)
        combined = first + second
        decoded_first = decode_profile_block(combined, 0xD2C6EF10, ["a"], first_meta)
        decoded_second = decode_profile_block(
            combined, 0x4879187D, ["b"], second_meta, offset=decoded_first.next_offset
        )
        self.assertEqual(decoded_first.values["a"]["value_int"], 1)
        self.assertEqual(decoded_second.values["b"]["value_int"], 2)
        self.assertEqual(decoded_second.next_offset, len(combined))

    def test_decode_profile_block_rejects_bad_marker_and_truncation(self):
        metadata = {"a": {"valType": 2, "valueTET": 1, "value_int": 1}}
        encoded = encode_profile_block(0xD2C6EF10, ["a"], metadata)
        with self.assertRaises(SetupValueError):
            decode_profile_block(encoded, 0x4879187D, ["a"], metadata)
        with self.assertRaises(SetupValueError):
            decode_profile_block(encoded[:-1], 0xD2C6EF10, ["a"], metadata)

    def test_profile_block_rejects_missing_sequence_value(self):
        with self.assertRaises(SetupValueError):
            encode_profile_block(0, ["missing"], {})

    def test_marker_and_vector_order(self):
        block = encode_setup_block(0xD2C6EF10, [
            {"valType": "2", "valueTET": "1", "value_int": "3"},
            {"valType": "1", "valueTET": "7", "value_dou": "1.25", "evalScl": "100"},
        ])
        self.assertEqual(block, b"\xD2\xC6\xEF\x10\x03\x00\x7D")

    def test_rejects_unknown_type(self):
        with self.assertRaises(SetupValueError):
            encode_setup_value(val_type=2, value_tet=0, value_int=0)

    def test_rejects_out_of_range_values(self):
        with self.assertRaises(SetupValueError):
            encode_setup_value(val_type=2, value_tet=3, value_int=65536)
        with self.assertRaises(SetupValueError):
            encode_setup_value(val_type=1, value_tet=7, value_dou=1000, eval_scl=100)

    def test_rejects_non_finite_scaled_values(self):
        with self.assertRaises(SetupValueError):
            encode_setup_value(val_type=1, value_tet=7, value_dou=float("inf"), eval_scl=1)


if __name__ == "__main__":
    unittest.main()
