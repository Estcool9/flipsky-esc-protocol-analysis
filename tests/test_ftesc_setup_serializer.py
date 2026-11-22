import struct
import unittest

from scripts.ftesc_setup_serializer import SetupValueError, encode_setup_block, encode_setup_value


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
