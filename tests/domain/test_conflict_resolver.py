import unittest
from domain.models.canonical_item import CanonicalMediaItem
from domain.models.canonical_ids import CanonicalIDs
from domain.models.conflict_policy import ConflictResolutionStrategy
from domain.services.conflict_resolver import resolve_conflict

class TestConflictResolver(unittest.TestCase):
    def test_merge_conflict_strategy(self):
        item1 = CanonicalMediaItem(title="Test Anime", aggregated_rating=8.0, ids=CanonicalIDs(mal="100"))
        item2 = CanonicalMediaItem(title="Test Anime", aggregated_rating=9.5, ids=CanonicalIDs(simkl="200"))
        merged = resolve_conflict(ConflictResolutionStrategy.MERGE, item1, item2)
        self.assertEqual(merged.aggregated_rating, 9.5)
        self.assertEqual(merged.ids.mal, "100")
        self.assertEqual(merged.ids.simkl, "200")

    def test_skip_conflict_strategy(self):
        item1 = CanonicalMediaItem(title="Original Show")
        item2 = CanonicalMediaItem(title="Incoming Show")
        resolved = resolve_conflict(ConflictResolutionStrategy.SKIP, item1, item2)
        self.assertEqual(resolved.title, "Original Show")

if __name__ == "__main__":
    unittest.main()
