import unittest
import subprocess
import tempfile
import sys
import os
import json
from pathlib import Path
from unittest.mock import patch


class TestMainCLI(unittest.TestCase):
    def test_cli_help(self):
        """Test --help flag prints usage and exits cleanly."""
        result = subprocess.run(
            [sys.executable, "main.py", "--help"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Media List Sync Pipeline", result.stdout)
        self.assertIn("--refresh-api", result.stdout)

    def test_cli_refresh_api_flag(self):
        """Test argument parser accepts --refresh-api flag."""
        from main import parse_args
        args = parse_args(["--refresh-api"])
        self.assertTrue(args.refresh_api)

        args_default = parse_args([])
        self.assertFalse(args_default.refresh_api)

    def test_end_to_end_execution(self):
        """Test full end-to-end execution of main pipeline creating all export files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "export"
            
            # Create dummy input files in temporary directory
            mal_file = Path(tmp_dir) / "mal.xml"
            mal_file.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<myanimelist>
    <myinfo>
        <user_id>1</user_id>
    </myinfo>
    <anime>
        <series_animedb_id>9253</series_animedb_id>
        <series_title>Steins;Gate</series_title>
        <series_type>TV</series_type>
        <my_status>Completed</my_status>
        <my_score>10</my_score>
    </anime>
</myanimelist>""", encoding="utf-8")

            trakt_dir = Path(tmp_dir) / "trakt"
            trakt_dir.mkdir()
            (trakt_dir / "watched_movies.json").write_text(json.dumps([
                {
                    "movie": {
                        "title": "Inception",
                        "year": 2010,
                        "ids": {"imdb": "tt1375666", "tmdb": 27205}
                    },
                    "watched_at": "2020-01-01T00:00:00.000Z"
                }
            ]), encoding="utf-8")

            nuvio_file = Path(tmp_dir) / "nuvio.json"
            nuvio_file.write_text(json.dumps([
                {
                    "title": "Breaking Bad",
                    "mediaType": "TV",
                    "year": 2008,
                    "ids": {"imdb": "tt0903747", "tvdb": 81189},
                    "status": "COMPLETED"
                }
            ]), encoding="utf-8")

            simkl_cache_dir = Path(tmp_dir) / "raw"
            simkl_file_dir = simkl_cache_dir / "simkl"
            simkl_file_dir.mkdir(parents=True)
            (simkl_file_dir / "all_items.json").write_text(json.dumps({
                "shows": [
                    {
                        "title": "Breaking Bad",
                        "year": 2008,
                        "ids": {"imdb": "tt0903747", "tvdb": 81189, "simkl": 1388},
                        "status": "completed"
                    }
                ]
            }), encoding="utf-8")

            env_patch = {
                "MAL_EXPORT_FILE": str(mal_file),
                "TRAKT_EXPORT_DIR": str(trakt_dir),
                "NUVIO_EXPORT_FILE": str(nuvio_file),
                "OUTPUT_DIR": str(out_dir),
                "SIMKL_CLIENT_ID": "dummy",
                "SIMKL_ACCESS_TOKEN": "dummy",
            }

            with patch.dict(os.environ, env_patch):
                with patch("sys.argv", ["main.py"]):
                    from main import main
                    main()

            # Verify all expected export files exist
            expected_files = [
                out_dir / "movies.json",
                out_dir / "shows.json",
                out_dir / "anime.json",
                out_dir / "combined_full.json",
                out_dir / "summary.md",
                out_dir / "reconciliation_flagged.json",
                out_dir / "reconciliation.md",
                out_dir / "simkl_import.json",
                out_dir / "trakt_import.json",
                out_dir / "mal_import.xml",
                out_dir / "nuvio_custom_collection.json",
            ]

            for file_path in expected_files:
                self.assertTrue(file_path.exists(), f"Expected file does not exist: {file_path}")


if __name__ == "__main__":
    unittest.main()
