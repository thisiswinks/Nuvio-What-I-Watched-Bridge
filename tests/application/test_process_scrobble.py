import unittest
from domain.models.canonical_ids import CanonicalIDs
from application.use_cases.process_scrobble import process_scrobble


class MockOtakuMapper:
    def lookup(self, ids, title):
        if ids.mal == "100":
            return {"mal_id": "100", "simkl_id": "5000", "kitsu_id": "800", "anidb_id": "900", "episode_offset": 0}
        return None


class TestProcessScrobble(unittest.TestCase):
    def test_scrobble_below_threshold_returns_none(self):
        result = process_scrobble(
            title="Test Anime",
            media_type="anime",
            season=1, episode=5,
            watched_date="2026-07-23",
            ids={"mal": "100"},
            scrobble_threshold_percent=85,
            progress_percent=50
        )
        self.assertIsNone(result)

    def test_scrobble_above_threshold_returns_item(self):
        result = process_scrobble(
            title="Test Anime",
            media_type="anime",
            season=1, episode=5,
            watched_date="2026-07-23",
            ids={"mal": "100", "trakt": "200"},
            scrobble_threshold_percent=85,
            progress_percent=100
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.title, "Test Anime")
        self.assertEqual(result.ids.mal, "100")
        self.assertEqual(result.ids.trakt, "200")
        self.assertEqual(result.episode, 5)

    def test_scrobble_with_enrichment(self):
        result = process_scrobble(
            title="Test Anime",
            media_type="anime",
            season=1, episode=5,
            watched_date="2026-07-23",
            ids={"mal": "100"},
            otaku_mapper=MockOtakuMapper()
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.ids.simkl, "5000")
        self.assertEqual(result.ids.kitsu, "800")
        self.assertTrue(result.is_anime)

    def test_scrobble_exact_threshold(self):
        result = process_scrobble(
            title="Test Movie",
            media_type="movie",
            season=None, episode=None,
            watched_date="2026-07-23",
            ids={"imdb": "tt123456"},
            scrobble_threshold_percent=85,
            progress_percent=85
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.ids.imdb, "tt123456")


if __name__ == "__main__":
    unittest.main()
