import json
import tempfile
import unittest
from pathlib import Path

from scripts.new_re_project import create_project, detect_file_kind, inspect_artifact


class NewReProjectTests(unittest.TestCase):
    def test_detects_common_file_kinds(self):
        self.assertEqual(detect_file_kind(b"MZ\x90\x00"), "PE/DOS executable candidate")
        self.assertEqual(detect_file_kind(b"\x7fELF\x02"), "ELF")
        self.assertEqual(detect_file_kind(b"PK\x03\x04"), "ZIP")
        self.assertEqual(detect_file_kind(b"%PDF-1.7"), "PDF")
        self.assertEqual(detect_file_kind(b"unknown"), "unknown")

    def test_inventory_hashes_without_copying_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sample.exe"
            source.write_bytes(b"MZtest-binary")
            info = inspect_artifact(source)
            self.assertEqual(info["size_bytes"], len(b"MZtest-binary"))
            self.assertFalse(info["copied_into_project"])
            self.assertFalse(info["executed"])
            root = create_project("sample-analysis", Path(tmp) / "projects", source)
            self.assertFalse((root / "artifacts/original/sample.exe").exists())
            manifest = json.loads((root / "project-manifest.json").read_text())
            self.assertEqual(manifest["artifact"]["sha256"], info["sha256"])
            self.assertTrue((root / "docs/EVIDENCE_LEDGER.md").exists())
            self.assertTrue((root / "docs/ANALYSIS_CHECKPOINT.md").exists())

    def test_rejects_unsafe_project_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("../escape", "bad/name", "", ".."):
                with self.subTest(name=name):
                    with self.assertRaises(ValueError):
                        create_project(name, Path(tmp))

    def test_refuses_non_empty_existing_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "analysis"
            root.mkdir()
            (root / "keep.txt").write_text("x")
            with self.assertRaises(FileExistsError):
                create_project("analysis", Path(tmp))


if __name__ == "__main__":
    unittest.main()
