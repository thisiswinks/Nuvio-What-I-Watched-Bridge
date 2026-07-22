import unittest
from pathlib import Path
import tempfile
import json
import os

from extractors.base import BaseExtractor
from extractors.mal_xml import MALXMLExtractor
from extractors.trakt_json import TraktJSONExtractor
from extractors.nuvio_json import NuvioJSONExtractor
from extractors.simkl_api import SimklAPIExtractor


class TestExtractors(unittest.TestCase):
    def test_mal_xml_extractor(self):
        mal_path = Path("/Users/winks/Downloads/animelist_1784747731_-_11369504.xml")
        extractor = MALXMLExtractor(mal_path)
        self.setIsInstance(extractor, BaseExtractor) if hasattr(self, "setIsInstance") else self.assertIsInstance(extractor, BaseExtractor)
        items = extractor.extract()
        if mal_path.exists():
            self.assertGreater(len(items), 0)
            first = items[0]
            self.assertIn("series_animedb_id", first)
            self.assertIn("series_title", first)

        # Test non-existent file
        non_existent = MALXMLExtractor(Path("/tmp/non_existent_mal_file.xml"))
        self.assertEqual(non_existent.extract(), [])

    def test_trakt_json_extractor(self):
        trakt_dir = Path("/Users/winks/Downloads/trakt-export-geekwinks")
        extractor = TraktJSONExtractor(trakt_dir)
        self.assertIsInstance(extractor, BaseExtractor)
        items = extractor.extract()
        if trakt_dir.exists():
            self.assertGreater(len(items), 0)
            first = items[0]
            self.assertIn("_source_file", first)

        # Test non-existent dir
        non_existent = TraktJSONExtractor(Path("/tmp/non_existent_trakt_dir"))
        self.assertEqual(non_existent.extract(), [])

    def test_nuvio_json_extractor(self):
        nuvio_path = Path("/Users/winks/Downloads/nuvio_custom_collection_2026-07-22.json")
        extractor = NuvioJSONExtractor(nuvio_path)
        self.assertIsInstance(extractor, BaseExtractor)
        items = extractor.extract()
        if nuvio_path.exists():
            self.assertGreater(len(items), 0)

        # Test non-existent file
        non_existent = NuvioJSONExtractor(Path("/tmp/non_existent_nuvio.json"))
        self.assertEqual(non_existent.extract(), [])

    def test_simkl_api_extractor_cache(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            simkl_cache_dir = tmp_path / "data" / "raw"
            simkl_file_dir = simkl_cache_dir / "simkl"
            simkl_file_dir.mkdir(parents=True, exist_ok=True)
            cache_file = simkl_file_dir / "all_items.json"

            sample_data = {"anime": [{"title": "Death Note"}], "movies": []}
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(sample_data, f)

            extractor = SimklAPIExtractor(
                client_id="dummy_id",
                access_token="dummy_token",
                raw_cache_dir=simkl_cache_dir,
            )
            self.assertIsInstance(extractor, BaseExtractor)
            data = extractor.extract()
            self.assertEqual(data, sample_data)

    def test_simkl_api_extractor_offline_no_cache(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            simkl_cache_dir = tmp_path / "data" / "raw"
            extractor = SimklAPIExtractor(
                client_id="",
                access_token="",
                raw_cache_dir=simkl_cache_dir,
            )
            data = extractor.extract()
            self.assertEqual(data, [])


if __name__ == "__main__":
    unittest.main()
