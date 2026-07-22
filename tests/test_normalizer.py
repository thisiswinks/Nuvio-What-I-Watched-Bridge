import unittest
from normalizer import (
    normalize_mal_item,
    normalize_trakt_item,
    normalize_simkl_item,
    normalize_nuvio_item,
    normalize_all_sources,
)
from models import MediaType, MediaStatus, CanonicalMediaItem


class TestNormalizer(unittest.TestCase):
    def test_normalize_mal_item(self):
        raw_mal = {
            "series_animedb_id": "53787",
            "series_title": "AI no Idenshi",
            "series_type": "TV",
            "series_episodes": "12",
            "my_start_date": "2023-08-07",
            "my_finish_date": "2023-09-29",
            "my_score": "8",
            "my_status": "Completed",
        }
        item = normalize_mal_item(raw_mal)
        self.assertIsInstance(item, CanonicalMediaItem)
        self.assertEqual(item.title, "AI no Idenshi")
        self.assertEqual(item.media_type, MediaType.ANIME)
        self.assertEqual(str(item.ids.mal), "53787")

        self.assertEqual(item.year, 2023)
        self.assertEqual(item.start_date, "2023-08-07")
        self.assertEqual(item.end_date, "2023-09-29")
        self.assertEqual(item.aggregated_rating, 8.0)
        self.assertEqual(item.aggregated_status, MediaStatus.COMPLETED)
        self.assertIn("mal", item.sources)
        self.assertTrue(item.sources["mal"].present)
        self.assertEqual(item.sources["mal"].rating, 8.0)

    def test_normalize_trakt_item_movie(self):
        raw_trakt_movie = {
            "type": "movie",
            "movie": {
                "title": "Batman Begins",
                "year": 2005,
                "ids": {
                    "imdb": "tt0372784",
                    "tmdb": 272,
                    "trakt": 228,
                    "slug": "batman-begins-2005",
                },
            },
            "rating": 9,
            "last_watched_at": "2026-07-21T00:06:00.000Z",
        }
        item = normalize_trakt_item(raw_trakt_movie)
        self.assertIsInstance(item, CanonicalMediaItem)
        self.assertEqual(item.title, "Batman Begins")
        self.assertEqual(item.media_type, MediaType.MOVIE)
        self.assertEqual(item.year, 2005)
        self.assertEqual(item.ids.imdb, "tt0372784")
        self.assertEqual(item.ids.tmdb, 272)
        self.assertEqual(item.ids.trakt, 228)
        self.assertEqual(item.aggregated_rating, 9.0)
        self.assertEqual(item.aggregated_status, MediaStatus.COMPLETED)
        self.assertIn("trakt", item.sources)

    def test_normalize_trakt_item_show(self):
        raw_trakt_show = {
            "show": {
                "title": "Star Trek: Strange New Worlds",
                "year": 2022,
                "ids": {
                    "imdb": "tt12327578",
                    "tmdb": 103516,
                    "tvdb": 382389,
                    "trakt": 162206,
                },
            },
            "plays": 10,
        }
        item = normalize_trakt_item(raw_trakt_show)
        self.assertEqual(item.title, "Star Trek: Strange New Worlds")
        self.assertEqual(item.media_type, MediaType.SHOW)
        self.assertEqual(item.ids.imdb, "tt12327578")
        self.assertEqual(item.ids.tmdb, 103516)
        self.assertEqual(item.ids.tvdb, 382389)
        self.assertEqual(item.ids.trakt, 162206)

    def test_normalize_simkl_item(self):
        raw_simkl = {
            "title": "Death Note",
            "year": 2006,
            "media_type": "anime",
            "status": "completed",
            "user_rating": 10,
            "ids": {
                "simkl": 41530,
                "imdb": "tt0877057",
                "tmdb": 13916,
                "tvdb": 79457,
                "mal": 1535,
                "kitsu": 1380,
                "anidb": 4563,
            },
        }
        item = normalize_simkl_item(raw_simkl)
        self.assertIsInstance(item, CanonicalMediaItem)
        self.assertEqual(item.title, "Death Note")
        self.assertEqual(item.media_type, MediaType.ANIME)
        self.assertEqual(item.year, 2006)
        self.assertEqual(item.ids.simkl, 41530)
        self.assertEqual(item.ids.imdb, "tt0877057")
        self.assertEqual(item.ids.tmdb, 13916)
        self.assertEqual(item.ids.tvdb, 79457)
        self.assertEqual(item.ids.mal, 1535)
        self.assertEqual(item.ids.kitsu, 1380)
        self.assertEqual(item.ids.anidb, 4563)
        self.assertEqual(item.aggregated_rating, 10.0)
        self.assertEqual(item.aggregated_status, MediaStatus.COMPLETED)
        self.assertIn("simkl", item.sources)

    def test_normalize_nuvio_item(self):
        raw_nuvio = {
            "id": "folder-IHPHVHSB",
            "title": "Top Streaming Movies",
            "mediaType": "MOVIE",
            "status": "watching",
            "rating": 7.5,
            "ids": {
                "nuvio": "folder-IHPHVHSB",
                "imdb": "tt1234567",
                "tmdb": 98765,
            },
        }
        item = normalize_nuvio_item(raw_nuvio)
        self.assertIsInstance(item, CanonicalMediaItem)
        self.assertEqual(item.title, "Top Streaming Movies")
        self.assertEqual(item.media_type, MediaType.MOVIE)
        self.assertEqual(item.ids.nuvio, "folder-IHPHVHSB")
        self.assertEqual(item.ids.imdb, "tt1234567")
        self.assertEqual(item.ids.tmdb, 98765)
        self.assertEqual(item.aggregated_status, MediaStatus.WATCHING)
        self.assertEqual(item.aggregated_rating, 7.5)
        self.assertIn("nuvio", item.sources)

    def test_all_external_ids_mapping_and_preservation(self):
        raw_all_ids = {
            "title": "Universal Identity Test",
            "media_type": "show",
            "ids": {
                "imdb": "tt9999999",
                "tmdb": 88888,
                "tvdb": 77777,
                "mal": 66666,
                "kitsu": 55555,
                "anidb": 44444,
                "simkl": 33333,
                "trakt": 22222,
                "nuvio": "nuvio-11111",
            },
        }
        item = normalize_simkl_item(raw_all_ids)
        self.assertEqual(item.ids.imdb, "tt9999999")
        self.assertEqual(item.ids.tmdb, 88888)
        self.assertEqual(item.ids.tvdb, 77777)
        self.assertEqual(item.ids.mal, 66666)
        self.assertEqual(item.ids.kitsu, 55555)
        self.assertEqual(item.ids.anidb, 44444)
        self.assertEqual(item.ids.simkl, 33333)
        self.assertEqual(item.ids.trakt, 22222)
        self.assertEqual(item.ids.nuvio, "nuvio-11111")

    def test_normalize_all_sources(self):
        extracted = {
            "mal": [
                {
                    "series_animedb_id": "101",
                    "series_title": "Anime 1",
                    "my_status": "Completed",
                }
            ],
            "trakt": [
                {
                    "type": "movie",
                    "movie": {"title": "Movie 1", "ids": {"trakt": 201}},
                }
            ],
            "simkl": [
                {
                    "title": "Show 1",
                    "media_type": "show",
                    "ids": {"simkl": 301},
                }
            ],
            "nuvio": [
                {
                    "id": "nuvio-401",
                    "title": "Nuvio List 1",
                    "mediaType": "TV",
                }
            ],
        }
        normalized = normalize_all_sources(extracted)
        self.assertEqual(len(normalized), 4)

        titles = [i.title for i in normalized]
        self.assertIn("Anime 1", titles)
        self.assertIn("Movie 1", titles)
        self.assertIn("Show 1", titles)
        self.assertIn("Nuvio List 1", titles)

    def test_normalize_all_sources_pregroups_trakt_episodes(self):
        trakt_ep1 = {
            "_source_file": "watched-shows-1.json",
            "show": {
                "ids": {"imdb": "tt9679542", "tmdb": 86031},
                "title": "Dr. Stone",
                "year": 2019,
            },
            "episode": {"season": 1, "number": 1, "title": "Stone World"},
            "watched_at": "2023-04-20T10:00:00.000Z",
        }
        trakt_ep2 = {
            "_source_file": "watched-shows-1.json",
            "show": {
                "ids": {"imdb": "tt9679542", "tmdb": 86031},
                "title": "Dr. Stone",
                "year": 2019,
            },
            "episode": {"season": 1, "number": 2, "title": "King of the Stone World"},
            "watched_at": "2023-04-21T10:00:00.000Z",
        }
        extracted = {"trakt": [trakt_ep1, trakt_ep2]}
        normalized = normalize_all_sources(extracted)

        dr_stone_items = [item for item in normalized if item.title == "Dr. Stone"]
        self.assertEqual(len(dr_stone_items), 1)
        self.assertEqual(len(dr_stone_items[0].episodes), 2)
        self.assertEqual(dr_stone_items[0].sources["trakt"].watch_count, 2)


if __name__ == "__main__":
    unittest.main()

