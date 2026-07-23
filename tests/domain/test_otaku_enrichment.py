import unittest
from domain.models.canonical_ids import CanonicalIDs
from domain.models.canonical_item import CanonicalMediaItem
from domain.services.otaku_enrichment import enrich_canonical_item

class MockOtakuMapper:
    def lookup(self, ids: CanonicalIDs, title: str):
        if ids.mal == "100" or title == "Attack on Titan":
            return {
                "mal_id": "100",
                "simkl_id": "5000",
                "kitsu_id": "800",
                "anidb_id": "900",
                "episode_offset": 0
            }
        return None

class TestOtakuEnrichment(unittest.TestCase):
    def test_selective_enrichment_does_not_overwrite_existing_id(self):
        item = CanonicalMediaItem(title="Attack on Titan", ids=CanonicalIDs(mal="100", simkl="9999"))
        enriched = enrich_canonical_item(item, otaku_mapper=MockOtakuMapper())
        # Existing simkl ID "9999" MUST NOT be overwritten by "5000" from mappings!
        self.assertEqual(enriched.ids.simkl, "9999")
        # Missing kitsu ID MUST be added!
        self.assertEqual(enriched.ids.kitsu, "800")
        self.assertTrue(enriched.is_anime)

    def test_enrichment_adds_missing_ids(self):
        item = CanonicalMediaItem(title="Attack on Titan", ids=CanonicalIDs(mal="100"))
        enriched = enrich_canonical_item(item, otaku_mapper=MockOtakuMapper())
        self.assertEqual(enriched.ids.simkl, "5000")
        self.assertEqual(enriched.ids.kitsu, "800")
        self.assertEqual(enriched.ids.anidb, "900")

if __name__ == "__main__":
    unittest.main()
