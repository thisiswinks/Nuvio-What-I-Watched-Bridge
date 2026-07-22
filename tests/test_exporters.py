import unittest
import tempfile
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from models import CanonicalMediaItem, CanonicalIDs, MediaType, MediaStatus, SourceRecord
from exporters.master_exporter import export_master_files
from exporters.reconciliation import export_reconciliation
from exporters.simkl_exporter import export_simkl_payload
from exporters.trakt_exporter import export_trakt_payload
from exporters.mal_exporter import export_mal_payload
from exporters.nuvio_exporter import export_nuvio_payload


class TestExporters(unittest.TestCase):
    def setUp(self):
        self.movie_item = CanonicalMediaItem(
            uuid="uuid-movie-1",
            media_type=MediaType.MOVIE,
            title="Inception",
            year=2010,
            ids=CanonicalIDs(imdb="tt1375666", tmdb="27205", simkl=12345),
            aggregated_status=MediaStatus.COMPLETED,
            aggregated_rating=9.0,
            sources={"trakt": SourceRecord(source_name="trakt")}
        )
        self.show_item = CanonicalMediaItem(
            uuid="uuid-show-1",
            media_type=MediaType.SHOW,
            title="Breaking Bad",
            year=2008,
            ids=CanonicalIDs(imdb="tt0903747", tvdb="81189", trakt=1388),
            aggregated_status=MediaStatus.COMPLETED,
            aggregated_rating=10.0,
            sources={"simkl": SourceRecord(source_name="simkl")}
        )
        self.anime_item = CanonicalMediaItem(
            uuid="uuid-anime-1",
            media_type=MediaType.ANIME,
            title="Steins;Gate",
            year=2011,
            ids=CanonicalIDs(mal="9253", tvdb="203491", imdb="tt1910272"),
            aggregated_status=MediaStatus.COMPLETED,
            aggregated_rating=10.0,
            sources={"mal": SourceRecord(source_name="mal")}
        )
        self.sample_items = [self.movie_item, self.show_item, self.anime_item]

    def test_export_master_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir)
            export_master_files(self.sample_items, out_dir)

            movies_file = out_dir / "movies.json"
            shows_file = out_dir / "shows.json"
            anime_file = out_dir / "anime.json"
            combined_file = out_dir / "combined_full.json"
            summary_file = out_dir / "summary.md"

            self.assertTrue(movies_file.exists())
            self.assertTrue(shows_file.exists())
            self.assertTrue(anime_file.exists())
            self.assertTrue(combined_file.exists())
            self.assertTrue(summary_file.exists())

            with open(movies_file, "r", encoding="utf-8") as f:
                movies_data = json.load(f)
                self.assertEqual(len(movies_data), 1)
                self.assertEqual(movies_data[0]["title"], "Inception")

            with open(shows_file, "r", encoding="utf-8") as f:
                shows_data = json.load(f)
                self.assertEqual(len(shows_data), 1)
                self.assertEqual(shows_data[0]["title"], "Breaking Bad")

            with open(anime_file, "r", encoding="utf-8") as f:
                anime_data = json.load(f)
                self.assertEqual(len(anime_data), 1)
                self.assertEqual(anime_data[0]["title"], "Steins;Gate")

            with open(combined_file, "r", encoding="utf-8") as f:
                combined_data = json.load(f)
                self.assertEqual(len(combined_data), 3)

            summary_text = summary_file.read_text(encoding="utf-8")
            self.assertIn("Total Combined Items", summary_text)
            self.assertIn("Movies", summary_text)

    def test_export_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir)
            flagged = [
                {
                    "reason": "Single ID match with year conflict",
                    "item1": "Show A",
                    "item2": "Show A Remake",
                    "year1": 2010,
                    "year2": 2020
                }
            ]
            export_reconciliation(flagged, out_dir)

            json_file = out_dir / "reconciliation_flagged.json"
            md_file = out_dir / "reconciliation.md"

            self.assertTrue(json_file.exists())
            self.assertTrue(md_file.exists())

            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertEqual(len(data), 1)
                self.assertEqual(data[0]["item1"], "Show A")

            md_text = md_file.read_text(encoding="utf-8")
            self.assertIn("Reconciliation Report", md_text)
            self.assertIn("Show A vs Show A Remake", md_text)

    def test_export_simkl_payload(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir)
            payload = export_simkl_payload(self.sample_items, out_dir)

            self.assertIn("movies", payload)
            self.assertIn("shows", payload)
            self.assertIn("anime", payload)

            self.assertEqual(len(payload["movies"]), 1)
            self.assertEqual(payload["movies"][0]["title"], "Inception")
            self.assertEqual(payload["movies"][0]["ids"]["imdb"], "tt1375666")

            self.assertEqual(len(payload["shows"]), 1)
            self.assertEqual(payload["shows"][0]["title"], "Breaking Bad")

            self.assertEqual(len(payload["anime"]), 1)
            self.assertEqual(payload["anime"][0]["title"], "Steins;Gate")

            import_file = out_dir / "simkl_import.json"
            self.assertTrue(import_file.exists())

    def test_export_trakt_payload(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir)
            payload = export_trakt_payload(self.sample_items, out_dir)

            self.assertIn("movies", payload)
            self.assertIn("shows", payload)

            self.assertEqual(len(payload["movies"]), 1)
            self.assertEqual(payload["movies"][0]["title"], "Inception")
            self.assertEqual(payload["movies"][0]["ids"]["imdb"], "tt1375666")

            self.assertEqual(len(payload["shows"]), 2)  # Breaking Bad & Steins;Gate mapped as shows
            
            import_file = out_dir / "trakt_import.json"
            self.assertTrue(import_file.exists())

    def test_export_mal_payload(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir)
            xml_str = export_mal_payload(self.sample_items, out_dir)

            self.assertTrue(xml_str.startswith('<?xml'))
            self.assertIn("<myanimelist>", xml_str)
            self.assertIn("Steins;Gate", xml_str)

            root = ET.fromstring(xml_str.replace('<?xml version="1.0" encoding="UTF-8"?>', '').strip())
            self.assertEqual(root.tag, "myanimelist")
            anime_elements = root.findall("anime")
            self.assertEqual(len(anime_elements), 1)

            import_file = out_dir / "mal_import.xml"
            self.assertTrue(import_file.exists())

    def test_export_nuvio_payload(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir)
            payload = export_nuvio_payload(self.sample_items, out_dir)

            self.assertIn("collection_name", payload)
            self.assertIn("items", payload)
            self.assertEqual(len(payload["items"]), 3)

            item = payload["items"][0]
            self.assertIn("uuid", item)
            self.assertIn("title", item)
            self.assertIn("ids", item)

            import_file = out_dir / "nuvio_custom_collection.json"
            self.assertTrue(import_file.exists())


if __name__ == "__main__":
    unittest.main()
