"""Offline FTESC V1.7 firmware block codec (static reverse engineering only).

No bootloader, serial port, BLE transport or ESC is accessed by this module.
"""
from __future__ import annotations

from collections.abc import Iterator

from scripts.ftesc_frame import crc16_modbus, encode_frame

CMD_ERASE_FIRMWARE = 0x16
CMD_WRITE_FIRMWARE = 0x18
FIRMWARE_BLOCK_SIZE = 0xF0  # 240 bytes, observed in the V1.7 update loop
MAX_NATIVE_IMAGE_SIZE = 0x30F98  # 200,600 bytes, caller-side V1.7 bound
UI_WARNING_IMAGE_SIZE = 150 * 1024  # UI text says "150Kbyte"; differs from native bound

# 239 table bytes read from V1.7 image VA 0x00530F61.
# The first byte of each block uses 0xD0; following bytes use this table.
_FIRMWARE_XOR_TABLE = bytes.fromhex(
    "c641a45dc18155d7d5bc6dc9157ee3c3b217934e59529758bde3ad6ff901a3e5f3325ae4159f721b1cb4d9463da9fd4a0103519cc199f965e87ec72db871775002497e063a50cc48193de87661fe84027804680ca24299ea629aa44033fe4712b47a33e85f218a5cc6660ac28d446d05db0bea19881d8551944c5f4c8c94d6f669b8e4860a814db6b1d8fc9d815d74d8026a730d10897dbc87cf43dd8628a341f53cbe2628759529a5f1048622b704fa89d311eb2e2388db533c3198be8b225ccbe00c38b6a8ec8a6dd0d825c37f46559568982873d2d02059a7db9d9d0776e04cb0cdc1ad40f05d5b0287919afa8a"
)


def transform_firmware_block(block: bytes | bytearray | memoryview) -> bytes:
    """Apply the V1.7 per-block XOR mask; same function encodes and decodes."""
    data = bytes(block)
    if len(data) > FIRMWARE_BLOCK_SIZE:
        raise ValueError(f"firmware block exceeds {FIRMWARE_BLOCK_SIZE} bytes")
    if not data:
        return b""
    key = bytes((0xD0,)) + _FIRMWARE_XOR_TABLE[:len(data) - 1]
    return bytes(value ^ mask_byte for value, mask_byte in zip(data, key))


def build_erase_info(image_size: int) -> bytes:
    """Build CMD 0x16 INFO: command byte followed by uint32 BE image size."""
    if not 0 <= image_size <= 0xFFFFFFFF:
        raise ValueError("image size must fit in uint32")
    if image_size > MAX_NATIVE_IMAGE_SIZE:
        raise ValueError(f"image exceeds V1.7 native bound of {MAX_NATIVE_IMAGE_SIZE} bytes")
    return bytes((CMD_ERASE_FIRMWARE,)) + image_size.to_bytes(4, "big")


def build_write_info(block: bytes | bytearray | memoryview) -> bytes:
    """Build CMD 0x18 INFO for one XOR-transformed firmware block."""
    data = bytes(block)
    if not 1 <= len(data) <= FIRMWARE_BLOCK_SIZE:
        raise ValueError(f"firmware block length must be 1..{FIRMWARE_BLOCK_SIZE}")
    return bytes((CMD_WRITE_FIRMWARE,)) + transform_firmware_block(data)


def iter_firmware_write_info(
    image: bytes | bytearray | memoryview,
) -> Iterator[bytes]:
    """Yield sequential CMD 0x18 INFO payloads, splitting at 240 bytes."""
    data = bytes(image)
    if not data:
        raise ValueError("firmware image must not be empty")
    if len(data) > MAX_NATIVE_IMAGE_SIZE:
        raise ValueError(f"image exceeds V1.7 native bound of {MAX_NATIVE_IMAGE_SIZE} bytes")
    for offset in range(0, len(data), FIRMWARE_BLOCK_SIZE):
        yield build_write_info(data[offset:offset + FIRMWARE_BLOCK_SIZE])


def iter_firmware_write_frames(
    image: bytes | bytearray | memoryview,
) -> Iterator[bytes]:
    """Yield offline UART frames for the CMD 0x18 blocks; never transmits them."""
    for info in iter_firmware_write_info(image):
        yield encode_frame(info)


def firmware_image_crc16(image: bytes | bytearray | memoryview) -> int:
    """Return the CRC16 computed over the complete image by the V1.7 updater.

    The native updater builds a size+CRC buffer after erase; its exact downstream
    consumer is not yet resolved, so this helper does not assign that CRC to a
    transmitted field.
    """
    return crc16_modbus(bytes(image))
