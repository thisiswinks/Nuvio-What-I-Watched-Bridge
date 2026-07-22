import unittest
from models import (
    CanonicalMediaItem,
    CanonicalIDs,
    SourceRecord,
    MediaType,
    MediaStatus,
)
from deduplicator import DeduplicationResult, merge_items, deduplicate_items


class TestDeduplicator(unittest.TestCase):
    def test_multi_id_match_auto_confirmed_merge(self):
        """>=2 matching external IDs -> auto-confirmed merge combining all IDs, sources, and history logs."""
        item1 = CanonicalMediaItem(
            uuid="uuid-1",
            media_type=MediaType.SHOW,
            title="Steins;Gate",
            year=2011,
            start_date="2011-04-06",
            ids=CanonicalIDs(imdb="tt1910272", tvdb="203491", mal="9253"),
            sources={
                "mal": SourceRecord(
                    source_name="mal", rating=10.0, status="completed"
                )
            },
            history_logs=[{"action": "watched", "date": "2020-01-01"}],
        )
        item2 = CanonicalMediaItem(
            uuid="uuid-2",
            media_type=MediaType.SHOW,
            title="Steins;Gate",
            year=2011,
            start_date="2011-04-06",
            ids=CanonicalIDs(imdb="tt1910272", tvdb="203491", simkl=41530),
            sources={
                "simkl": SourceRecord(
                    source_name="simkl", rating=8.0, status="completed"
                )
            },
            history_logs=[{"action": "watched", "date": "2021-05-05"}],
        )

        result = deduplicate_items([item1, item2])
        self.assertEqual(len(result.confirmed), 1)
        self.assertEqual(len(result.flagged), 0)

        merged = result.confirmed[0]
        # IDs combined
        self.assertEqual(merged.ids.imdb, "tt1910272")
        self.assertEqual(merged.ids.tvdb, "203491")
        self.assertEqual(merged.ids.mal, "9253")
        self.assertEqual(merged.ids.simkl, 41530)
        # Sources combined
        self.assertIn("mal", merged.sources)
        self.assertIn("simkl", merged.sources)
        # History logs combined
        self.assertEqual(len(merged.history_logs), 2)
        # Rating average: (10.0 + 8.0) / 2 = 9.0
        self.assertEqual(merged.aggregated_rating, 9.0)

    def test_title_and_date_match_auto_confirmed_merge(self):
        """Title (normalized) + Start Date / Release Date matching -> auto-confirmed merge."""
        item1 = CanonicalMediaItem(
            uuid="uuid-1",
            media_type=MediaType.MOVIE,
            title="Inception",
            year=2010,
            start_date="2010-07-16",
            ids=CanonicalIDs(imdb="tt1375666"),
            sources={
                "trakt": SourceRecord(source_name="trakt", rating=9.0)
            },
        )
        item2 = CanonicalMediaItem(
            uuid="uuid-2",
            media_type=MediaType.MOVIE,
            title="inception!",
            year=2010,
            start_date="2010-07-16",
            ids=CanonicalIDs(tmdb=27205),
            sources={
                "simkl": SourceRecord(source_name="simkl", rating=9.0)
            },
        )

        result = deduplicate_items([item1, item2])
        self.assertEqual(len(result.confirmed), 1)
        self.assertEqual(len(result.flagged), 0)
        merged = result.confirmed[0]
        self.assertEqual(merged.ids.imdb, "tt1375666")
        self.assertEqual(merged.ids.tmdb, 27205)

    def test_single_id_match_with_conflicting_dates_or_titles_flagged(self):
        """1 matching external ID with conflicting dates/titles -> flagged for reconciliation."""
        item1 = CanonicalMediaItem(
            uuid="uuid-1",
            media_type=MediaType.SHOW,
            title="Fullmetal Alchemist",
            year=2003,
            start_date="2003-10-04",
            ids=CanonicalIDs(imdb="tt0421357"),
        )
        item2 = CanonicalMediaItem(
            uuid="uuid-2",
            media_type=MediaType.SHOW,
            title="Fullmetal Alchemist: Brotherhood",
            year=2009,
            start_date="2009-04-05",
            ids=CanonicalIDs(imdb="tt0421357"),  # Single matching ID, but different year/title
        )

        result = deduplicate_items([item1, item2])
        self.assertEqual(len(result.flagged), 1)
        self.assertEqual(len(result.confirmed), 2)  # items remain separate/flagged
        self.assertIn("1 matching external ID", result.flagged[0]["reason"])

    def test_title_match_with_missing_or_conflicting_dates_flagged(self):
        """Title match with missing or conflicting start/end dates -> flagged for reconciliation."""
        # Case A: Conflicting dates
        item1 = CanonicalMediaItem(
            uuid="uuid-1",
            media_type=MediaType.MOVIE,
            title="Avatar",
            year=2009,
            start_date="2009-12-18",
            ids=CanonicalIDs(imdb="tt0499549"),
        )
        item2 = CanonicalMediaItem(
            uuid="uuid-2",
            media_type=MediaType.MOVIE,
            title="Avatar",
            year=2022,
            start_date="2022-12-16",
            ids=CanonicalIDs(tmdb=76600),
        )

        result_conflict = deduplicate_items([item1, item2])
        self.assertEqual(len(result_conflict.flagged), 1)
        self.assertIn("conflicting", result_conflict.flagged[0]["reason"].lower())

        # Case B: Missing dates with matching title auto-merges
        item3 = CanonicalMediaItem(
            uuid="uuid-3",
            media_type=MediaType.MOVIE,
            title="The Matrix",
            year=1999,
            start_date="1999-03-31",
            ids=CanonicalIDs(imdb="tt0133093"),
        )
        item4 = CanonicalMediaItem(
            uuid="uuid-4",
            media_type=MediaType.MOVIE,
            title="The Matrix",
            year=None,
            start_date=None,
            ids=CanonicalIDs(tmdb=603),
        )

        result_missing = deduplicate_items([item3, item4])
        self.assertEqual(len(result_missing.confirmed), 1)



if __name__ == "__main__":
    unittest.main()
