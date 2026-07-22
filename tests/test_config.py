import unittest
import os
from unittest.mock import patch


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
            self.assertEqual(cfg.trakt_export_dir, "/Users/winks/Downloads/trakt-export-geekwinks")
            self.assertEqual(cfg.mal_export_file, "/Users/winks/Downloads/animelist_1784747731_-_11369504.xml")
            self.assertEqual(cfg.nuvio_export_file, "/Users/winks/Downloads/nuvio_custom_collection_2026-07-22.json")


if __name__ == "__main__":
    unittest.main()
