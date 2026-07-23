import unittest
import os
import json
import tempfile
from infrastructure.persistence.local_storage import LocalStorage


class TestLocalStorage(unittest.TestCase):
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_store.json")
            storage = LocalStorage(file_path=path)

            data = {
                "items": [{"title": "Test Anime", "media_type": "anime"}],
                "metadata": {"version": "1.0.0", "last_updated": "2026-07-23T00:00:00Z"}
            }
            result = storage.save(data)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(path))

            loaded = storage.load()
            self.assertEqual(len(loaded["items"]), 1)
            self.assertEqual(loaded["items"][0]["title"], "Test Anime")

    def test_load_missing_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "nonexistent.json")
            storage = LocalStorage(file_path=path)
            loaded = storage.load()
            self.assertEqual(loaded["items"], [])
            self.assertEqual(loaded["metadata"]["version"], "1.0.0")

    def test_atomic_save_no_corruption(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "atomic_test.json")
            storage = LocalStorage(file_path=path)

            # Save initial data
            storage.save({"items": [{"title": "Item1"}], "metadata": {"version": "1.0.0", "last_updated": None}})

            # Save updated data
            storage.save({"items": [{"title": "Item1"}, {"title": "Item2"}], "metadata": {"version": "1.0.0", "last_updated": None}})

            # Verify no temp files remain
            files_in_dir = os.listdir(tmpdir)
            self.assertEqual(len(files_in_dir), 1, "Only the target file should exist, no temp files")

            loaded = storage.load()
            self.assertEqual(len(loaded["items"]), 2)


if __name__ == "__main__":
    unittest.main()
