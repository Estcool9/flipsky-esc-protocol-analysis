import unittest

from scripts.ftesc_firmware import (
    FIRMWARE_BLOCK_SIZE,
    MAX_NATIVE_IMAGE_SIZE,
    build_erase_info,
    build_write_info,
    firmware_image_crc16,
    iter_firmware_write_frames,
    iter_firmware_write_info,
    transform_firmware_block,
)
from scripts.ftesc_frame import decode_frame


class FirmwareBlockCodecTests(unittest.TestCase):
    def test_erase_info_uses_uint32_big_endian_size(self):
        self.assertEqual(build_erase_info(0x12345), bytes.fromhex("16 00 01 23 45"))

    def test_erase_info_rejects_native_size_overflow(self):
        with self.assertRaises(ValueError):
            build_erase_info(MAX_NATIVE_IMAGE_SIZE + 1)

    def test_first_byte_uses_d0_mask(self):
        self.assertEqual(transform_firmware_block(b"\x00"), b"\xD0")

    def test_second_byte_uses_first_table_byte(self):
        self.assertEqual(transform_firmware_block(b"\x00\x00"), bytes.fromhex("D0 C6"))

    def test_xor_transform_is_symmetric(self):
        data = bytes(range(FIRMWARE_BLOCK_SIZE))
        self.assertEqual(transform_firmware_block(transform_firmware_block(data)), data)

    def test_block_transform_rejects_more_than_240_bytes(self):
        with self.assertRaises(ValueError):
            transform_firmware_block(bytes(FIRMWARE_BLOCK_SIZE + 1))

    def test_write_info_prepends_command_and_transforms_block(self):
        self.assertEqual(build_write_info(b"\x00\x00"), bytes.fromhex("18 D0 C6"))

    def test_image_is_split_into_240_byte_blocks(self):
        image = bytes((i & 0xFF) for i in range(FIRMWARE_BLOCK_SIZE + 1))
        infos = list(iter_firmware_write_info(image))
        self.assertEqual([len(item) for item in infos], [241, 2])
        self.assertEqual(infos[0][0], 0x18)
        self.assertEqual(infos[1][0], 0x18)
        # The XOR sequence resets at the start of each block.
        self.assertEqual(infos[1][1], image[-1] ^ 0xD0)

    def test_write_frame_decodes_to_expected_info(self):
        frame = next(iter_firmware_write_frames(b"\x01\x02"))
        decoded = decode_frame(frame)
        self.assertEqual(decoded.payload, build_write_info(b"\x01\x02"))

    def test_empty_image_rejected(self):
        with self.assertRaises(ValueError):
            list(iter_firmware_write_info(b""))

    def test_crc16_image_helper_uses_modbus(self):
        self.assertEqual(firmware_image_crc16(b"123456789"), 0x4B37)


if __name__ == "__main__":
    unittest.main()
