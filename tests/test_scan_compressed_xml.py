import unittest
import zlib

from scripts.scan_compressed_xml import scan_zlib_xml


class ScanCompressedXmlTests(unittest.TestCase):
    def test_finds_xml_streams_and_reports_qcompress_prefix(self):
        xml = b"<?xml version='1.0'?><ValueSetups><Values/></ValueSetups>"
        stream = zlib.compress(xml)
        data = len(xml).to_bytes(4, "big") + stream
        result = scan_zlib_xml(data)
        self.assertEqual(len(result.xml_streams), 1)
        item = result.xml_streams[0]
        self.assertEqual(item.root_tag, "ValueSetups")
        self.assertEqual(item.offset, 4)
        self.assertTrue(item.qcompress_prefix_matches)

    def test_deduplicates_equal_xml_streams(self):
        xml = b"<ValueSetups><Values><a/></Values></ValueSetups>"
        stream = zlib.compress(xml)
        result = scan_zlib_xml(b"noise" + stream + b"noise" + stream)
        self.assertEqual(len(result.xml_streams), 2)
        self.assertEqual(len(result.unique_xml), 1)
        self.assertEqual(result.xml_streams[1].duplicate_of_offset, result.xml_streams[0].offset)

    def test_ignores_non_xml_zlib_streams(self):
        data = b"prefix" + zlib.compress(bytes(range(256))) + b"tail"
        result = scan_zlib_xml(data)
        self.assertEqual(len(result.xml_streams), 0)

    def test_rejects_incomplete_stream(self):
        xml = b"<ValueSetups><Values/></ValueSetups>"
        data = zlib.compress(xml)[:-3]
        result = scan_zlib_xml(data)
        self.assertEqual(len(result.xml_streams), 0)

    def test_root_filter_and_output_limit(self):
        a = zlib.compress(b"<Other/>")
        b = zlib.compress(b"<ValueSetups/>")
        result = scan_zlib_xml(a + b, root_tag="ValueSetups")
        self.assertEqual([x.root_tag for x in result.unique_xml], ["ValueSetups"])
        with self.assertRaises(ValueError):
            scan_zlib_xml(b, max_output_size=0)


if __name__ == "__main__":
    unittest.main()
