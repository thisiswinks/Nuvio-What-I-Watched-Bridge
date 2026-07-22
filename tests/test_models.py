import unittest
from models import (
    CanonicalMediaItem,
    CanonicalIDs,
    SourceRecord,
    MediaType,
    MediaStatus,
)


class TestModels(unittest.TestCase):
    def test_canonical_media_item_creation(self):
        item = CanonicalMediaItem(
            uuid="test-uuid-1234",
            media_type=MediaType.SHOW,
            title="Steins;Gate",
            title_original="シュタインズ・ゲート",
            year=2011,
            start_date="2011-04-06",
            end_date="2011-09-14",
            ids=CanonicalIDs(mal="9253", tvdb="203491", imdb="tt1910272"),
            aggregated_status=MediaStatus.COMPLETED,
            aggregated_rating=9.5,
        )
        self.assertEqual(item.uuid, "test-uuid-1234")
        self.assertEqual(item.media_type, MediaType.SHOW)
        self.assertEqual(item.title, "Steins;Gate")
        self.assertEqual(item.title_original, "シュタインズ・ゲート")
        self.assertEqual(item.year, 2011)
        self.assertEqual(item.start_date, "2011-04-06")
        self.assertEqual(item.end_date, "2011-09-14")
        self.assertEqual(item.ids.mal, "9253")
        self.assertEqual(item.ids.tvdb, "203491")
        self.assertEqual(item.ids.imdb, "tt1910272")
        self.assertEqual(item.aggregated_status, MediaStatus.COMPLETED)
        self.assertEqual(item.aggregated_rating, 9.5)

    def test_canonical_ids_matching_id_count(self):
        ids1 = CanonicalIDs(
            imdb="tt1910272",
            tmdb="38023",
            tvdb="203491",
            mal="9253",
            kitsu="6004",
            anidb="7702",
            simkl=41530,
            trakt=32544,
            nuvio="nuvio-123",
        )
        # Matches 3 IDs: imdb, tvdb, mal
        ids2 = CanonicalIDs(
            imdb="tt1910272",
            tmdb="99999",
            tvdb="203491",
            mal="9253",
            kitsu="8888",
        )
        # Matches 0 IDs
        ids3 = CanonicalIDs(
            imdb="tt0000000",
            tmdb="11111",
        )

        self.assertEqual(ids1.matching_id_count(ids2), 3)
        self.assertEqual(ids1.matching_id_count(ids3), 0)
        self.assertEqual(ids2.matching_id_count(ids3), 0)

    def test_canonical_ids_merge(self):
        ids1 = CanonicalIDs(
            imdb="tt1910272",
            mal="9253",
            simkl=41530,
        )
        ids2 = CanonicalIDs(
            tvdb="203491",
            mal="9253",  # same
            trakt=32544,
        )

        merged = ids1.merge(ids2)
        self.assertEqual(merged.imdb, "tt1910272")
        self.assertEqual(merged.tvdb, "203491")
        self.assertEqual(merged.mal, "9253")
        self.assertEqual(merged.simkl, 41530)
        self.assertEqual(merged.trakt, 32544)
        self.assertIsNone(merged.tmdb)
        self.assertIsNone(merged.kitsu)
        self.assertIsNone(merged.anidb)
        self.assertIsNone(merged.nuvio)


if __name__ == "__main__":
    unittest.main()
