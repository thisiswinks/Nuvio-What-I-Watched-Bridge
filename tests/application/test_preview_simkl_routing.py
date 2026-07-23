import unittest

from application.use_cases.preview_simkl_routing import preview_simkl_routing
from domain.models.canonical_ids import CanonicalIDs
from domain.models.canonical_item import CanonicalMediaItem


def anime(title, **kw):
    ids = kw.pop("ids")
    item = CanonicalMediaItem(title=title, media_type="anime", is_anime=True, ids=ids)
    for k, v in kw.items():
        setattr(item, k, v)
    return item


class TestPreviewSimklRouting(unittest.TestCase):
    def test_summarizes_paths_per_item(self):
        items = [
            anime("Native", ids=CanonicalIDs(mal="21"), absolute_episode=403),
            anime("Hybrid", ids=CanonicalIDs(tmdb="1429"), season=3, episode=13),
            anime("Quarantined", ids=CanonicalIDs(tmdb="1429")),
            CanonicalMediaItem(title="Inception", media_type="movie",
                               ids=CanonicalIDs(imdb="tt1375666")),
        ]
        preview = preview_simkl_routing(items)
        self.assertEqual(preview["total"], 4)
        self.assertEqual(preview["summary"]["native"], 1)
        self.assertEqual(preview["summary"]["hybrid"], 1)
        self.assertEqual(preview["summary"]["needs_identity"], 1)
        self.assertEqual(preview["summary"]["standard"], 1)
        # Every route carries an actionable explanation.
        for route in preview["routes"]:
            self.assertTrue(route["reason"])

    def test_mode_is_echoed_and_gates_routing(self):
        item = anime("H", ids=CanonicalIDs(tmdb="1429"), season=3, episode=13)
        preview = preview_simkl_routing([item], anime_mode="native_only")
        self.assertEqual(preview["anime_mode"], "native_only")
        # native_only refuses the hybrid candidate
        self.assertEqual(preview["routes"][0]["path"], "needs_identity")

    def test_unknown_mode_raises(self):
        with self.assertRaises(ValueError):
            preview_simkl_routing([], anime_mode="turbo")


if __name__ == "__main__":
    unittest.main()
