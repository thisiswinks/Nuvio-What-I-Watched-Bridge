import unittest
import os
import tempfile
from unittest.mock import patch


class TestSimklAnimeMode(unittest.TestCase):
    def _write_yaml(self, mode_line: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".yaml")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write("providers:\n  simkl:\n    enabled: true\n" + mode_line)
        return path

    def test_reads_mode_from_yaml(self):
        from config import get_simkl_anime_mode
        path = self._write_yaml('    anime_mode: "native_only"\n')
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_simkl_anime_mode(path), "native_only")
        os.unlink(path)

    def test_env_overrides_yaml(self):
        from config import get_simkl_anime_mode
        path = self._write_yaml('    anime_mode: "native_only"\n')
        with patch.dict(os.environ, {"SIMKL_ANIME_MODE": "tvdb_hybrid_only"}, clear=True):
            self.assertEqual(get_simkl_anime_mode(path), "tvdb_hybrid_only")
        os.unlink(path)

    def test_default_when_absent(self):
        from config import get_simkl_anime_mode
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                get_simkl_anime_mode("/nonexistent.yaml"), "auto_native_preferred"
            )

    def test_unknown_mode_fails_loud(self):
        from config import get_simkl_anime_mode
        path = self._write_yaml('    anime_mode: "turbo"\n')
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                get_simkl_anime_mode(path)
        os.unlink(path)


class TestConfig(unittest.TestCase):
    def test_load_config_env_vars(self):
        env = {
            "SIMKL_CLIENT_ID": "test_client_id_123",
            "SIMKL_CLIENT_SECRET": "test_client_secret_456",
            "SIMKL_ACCESS_TOKEN": "test_access_token_789",
            "TRAKT_EXPORT_DIR": "/tmp/trakt_test",
            "MAL_EXPORT_FILE": "/tmp/mal_test.xml",
            "NUVIO_EXPORT_FILE": "/tmp/nuvio_test.json",
        }
        with patch.dict(os.environ, env, clear=True):
            from config import load_config
            cfg = load_config()
            self.assertEqual(cfg.simkl_client_id, "test_client_id_123")
            self.assertEqual(cfg.simkl_client_secret, "test_client_secret_456")
            self.assertEqual(cfg.simkl_access_token, "test_access_token_789")
            self.assertEqual(cfg.trakt_export_dir, "/tmp/trakt_test")
            self.assertEqual(cfg.mal_export_file, "/tmp/mal_test.xml")
            self.assertEqual(cfg.nuvio_export_file, "/tmp/nuvio_test.json")

    def test_load_config_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            from config import load_config
            cfg = load_config()
            self.assertEqual(cfg.simkl_client_id, "")
            self.assertEqual(cfg.simkl_client_secret, "")
            self.assertIsNone(cfg.simkl_access_token)
            self.assertEqual(cfg.trakt_export_dir, "data/import/trakt")
            self.assertEqual(cfg.mal_export_file, "data/import/mal_animelist.xml")
            self.assertEqual(cfg.nuvio_export_file, "data/import/nuvio_collection.json")


if __name__ == "__main__":
    unittest.main()
