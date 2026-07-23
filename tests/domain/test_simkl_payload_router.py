import json
import os
import unittest
from domain.models.canonical_ids import CanonicalIDs
from domain.models.canonical_item import CanonicalMediaItem
from domain.services.simkl_payload_router import (
    AnimeSyncMode,
    SimklPayloadRouter,
    SimklRoute,
)


def make_item(**kwargs) -> CanonicalMediaItem:
    ids = kwargs.pop("ids", None) or CanonicalIDs()
    item = CanonicalMediaItem(title=kwargs.pop("title", "Test Title"), ids=ids)
    for key, value in kwargs.items():
        setattr(item, key, value)
    return item


class LegacyStyleItem:
    """Duck-typed stand-in for the legacy models.CanonicalMediaItem shape."""

    def __init__(self, title, media_type, ids, episodes=None, year=None):
        self.title = title
        self.media_type = media_type
        self.ids = ids
        self.episodes = episodes or []
        self.year = year


class TestNativeRouting(unittest.TestCase):
    def setUp(self):
        self.router = SimklPayloadRouter(AnimeSyncMode.AUTO_NATIVE_PREFERRED)

    def test_native_cour_split_flat_episode(self):
        item = make_item(
            media_type="anime", is_anime=True,
            ids=CanonicalIDs(mal="25777", tmdb="1429", tvdb="267440"),
            absolute_episode=4, watched_date="2026-07-01T20:00:00Z",
        )
        route = self.router.route(item)
        self.assertEqual(route.path, "native")
        self.assertEqual(route.envelope, "anime")
        self.assertEqual(route.entry["ids"]["mal"], 25777)
        # Core anti-misroute guarantee: shared parent ids are excluded on Path B
        self.assertNotIn("tmdb", route.entry["ids"])
        self.assertNotIn("tvdb", route.entry["ids"])
        self.assertEqual(route.entry["episodes"], [
            {"number": 4, "watched_at": "2026-07-01T20:00:00Z"}
        ])

    def test_native_absolute_long_runner(self):
        item = make_item(
            media_type="anime", is_anime=True,
            ids=CanonicalIDs(mal="21", anidb="69"),
            absolute_episode=403,
        )
        route = self.router.route(item)
        self.assertEqual(route.path, "native")
        self.assertEqual(route.entry["episodes"], [{"number": 403}])

    def test_native_episodes_never_carry_season_key(self):
        item = make_item(
            media_type="anime", is_anime=True,
            ids=CanonicalIDs(mal="25777"), season=2, absolute_episode=4,
        )
        route = self.router.route(item)
        for ep in route.entry["episodes"]:
            self.assertNotIn("season", ep)

    def test_digit_ids_emitted_as_ints(self):
        item = make_item(
            media_type="anime", is_anime=True,
            ids=CanonicalIDs(mal="25777", simkl="439744"), absolute_episode=1,
        )
        route = self.router.route(item)
        self.assertEqual(route.entry["ids"]["mal"], 25777)
        self.assertEqual(route.entry["ids"]["simkl"], 439744)

    def test_empty_string_ids_ignored(self):
        item = make_item(
            media_type="anime", is_anime=True,
            ids=CanonicalIDs(mal="", tmdb="1429"), season=3, episode=13,
        )
        route = self.router.route(item)
        # mal is an empty sentinel, so native is not available -> hybrid
        self.assertEqual(route.path, "hybrid")


class TestHybridRouting(unittest.TestCase):
    def setUp(self):
        self.router = SimklPayloadRouter(AnimeSyncMode.AUTO_NATIVE_PREFERRED)

    def test_hybrid_split_cour_coordinates(self):
        item = make_item(
            title="Shingeki no Kyojin", year=2013,
            media_type="anime", is_anime=True,
            ids=CanonicalIDs(tmdb="1429"), season=3, episode=13,
        )
        route = self.router.route(item)
        self.assertEqual(route.path, "hybrid")
        self.assertEqual(route.envelope, "shows")
        self.assertTrue(route.entry["use_tvdb_anime_seasons"])
        self.assertEqual(route.entry["seasons"], [
            {"number": 3, "episodes": [{"number": 13}]}
        ])
        self.assertEqual(route.entry["title"], "Shingeki no Kyojin")
        self.assertEqual(route.entry["year"], 2013)

    def test_hybrid_sends_both_tmdb_and_tvdb(self):
        item = make_item(
            media_type="anime", is_anime=True,
            ids=CanonicalIDs(tmdb="1429", tvdb="267440"), season=2, episode=4,
        )
        route = self.router.route(item)
        self.assertEqual(route.entry["ids"]["tmdb"], 1429)
        self.assertEqual(route.entry["ids"]["tvdb"], 267440)

    def test_native_ids_with_only_seasonal_coords_falls_back_to_hybrid(self):
        # Native id present but no absolute episode: Simkl must do the mapping.
        item = make_item(
            media_type="anime", is_anime=True,
            ids=CanonicalIDs(mal="25777", tvdb="267440"), season=2, episode=4,
        )
        route = self.router.route(item)
        self.assertEqual(route.path, "hybrid")

    def test_native_preferred_over_hybrid_when_both_possible(self):
        item = make_item(
            media_type="anime", is_anime=True,
            ids=CanonicalIDs(mal="25777", tvdb="267440"),
            season=2, episode=4, absolute_episode=4,
        )
        route = self.router.route(item)
        self.assertEqual(route.path, "native")
        self.assertNotIn("tvdb", route.entry["ids"])


class TestQuarantine(unittest.TestCase):
    def setUp(self):
        self.router = SimklPayloadRouter(AnimeSyncMode.AUTO_NATIVE_PREFERRED)

    def test_shared_parent_id_without_coordinates_quarantines(self):
        # Forbidden: deriving a cour-specific identity from a shared parent id.
        item = make_item(
            media_type="anime", is_anime=True, ids=CanonicalIDs(tmdb="1429"),
        )
        route = self.router.route(item)
        self.assertEqual(route.path, "needs_identity")
        self.assertIsNone(route.envelope)
        self.assertTrue(route.reason)

    def test_episodeless_anime_series_quarantines(self):
        # A bare series entry to /sync/history marks the whole show watched.
        item = make_item(
            media_type="anime", is_anime=True, ids=CanonicalIDs(mal="21"),
        )
        route = self.router.route(item)
        self.assertEqual(route.path, "needs_identity")

    def test_episodeless_show_quarantines(self):
        item = make_item(media_type="show", ids=CanonicalIDs(tvdb="81797"))
        route = self.router.route(item)
        self.assertEqual(route.path, "needs_identity")

    def test_unknown_media_type_quarantines(self):
        item = make_item(media_type="mixtape", ids=CanonicalIDs(imdb="tt1"))
        route = self.router.route(item)
        self.assertEqual(route.path, "needs_identity")

    def test_no_ids_at_all_quarantines(self):
        item = make_item(media_type="anime", is_anime=True, absolute_episode=3)
        route = self.router.route(item)
        self.assertEqual(route.path, "needs_identity")


class TestModeGates(unittest.TestCase):
    def test_native_only_refuses_hybrid(self):
        router = SimklPayloadRouter(AnimeSyncMode.NATIVE_ONLY)
        item = make_item(
            media_type="anime", is_anime=True,
            ids=CanonicalIDs(mal="25777", tvdb="267440"), season=2, episode=4,
        )
        route = router.route(item)
        self.assertEqual(route.path, "needs_identity")

    def test_tvdb_hybrid_only_refuses_native(self):
        router = SimklPayloadRouter(AnimeSyncMode.TVDB_HYBRID_ONLY)
        item = make_item(
            media_type="anime", is_anime=True,
            ids=CanonicalIDs(mal="25777"), absolute_episode=4,
        )
        route = router.route(item)
        self.assertEqual(route.path, "needs_identity")

    def test_tvdb_hybrid_only_routes_hybrid(self):
        router = SimklPayloadRouter(AnimeSyncMode.TVDB_HYBRID_ONLY)
        item = make_item(
            media_type="anime", is_anime=True,
            ids=CanonicalIDs(mal="25777", tvdb="267440"), season=2, episode=4,
        )
        route = router.route(item)
        self.assertEqual(route.path, "hybrid")

    def test_mode_from_string(self):
        router = SimklPayloadRouter("native_only")
        self.assertEqual(router.mode, AnimeSyncMode.NATIVE_ONLY)

    def test_unknown_mode_fails_loud(self):
        with self.assertRaises(ValueError):
            SimklPayloadRouter("yolo_mode")


class TestNonAnimeAndMovies(unittest.TestCase):
    def setUp(self):
        self.router = SimklPayloadRouter(AnimeSyncMode.AUTO_NATIVE_PREFERRED)

    def test_movie_routes_standard_without_flag(self):
        item = make_item(
            title="Inception", year=2010, media_type="movie",
            ids=CanonicalIDs(imdb="tt1375666"),
            watched_date="2026-07-02T21:00:00Z",
        )
        route = self.router.route(item)
        self.assertEqual(route.path, "standard")
        self.assertEqual(route.envelope, "movies")
        self.assertNotIn("use_tvdb_anime_seasons", route.entry)
        self.assertEqual(route.entry["watched_at"], "2026-07-02T21:00:00Z")

    def test_show_with_coordinates_routes_standard_without_flag(self):
        item = make_item(
            media_type="show", ids=CanonicalIDs(tvdb="81797"),
            season=2, episode=1,
        )
        route = self.router.route(item)
        self.assertEqual(route.path, "standard")
        self.assertEqual(route.envelope, "shows")
        self.assertNotIn("use_tvdb_anime_seasons", route.entry)

    def test_series_alias_treated_as_show(self):
        item = make_item(
            media_type="series", ids=CanonicalIDs(tvdb="81797"),
            season=1, episode=2,
        )
        route = self.router.route(item)
        self.assertEqual(route.envelope, "shows")

    def test_anime_movie_with_native_ids(self):
        item = make_item(
            title="Your Name", media_type="movie", is_anime=True,
            ids=CanonicalIDs(mal="32281", tmdb="372058"),
        )
        route = self.router.route(item)
        self.assertEqual(route.path, "native")
        self.assertEqual(route.envelope, "anime")
        self.assertNotIn("episodes", route.entry)
        self.assertNotIn("tmdb", route.entry["ids"])

    def test_anime_movie_without_native_ids_routes_movies(self):
        item = make_item(
            title="Your Name", media_type="movie", is_anime=True,
            ids=CanonicalIDs(tmdb="372058"),
        )
        route = self.router.route(item)
        self.assertEqual(route.path, "standard")
        self.assertEqual(route.envelope, "movies")

    def test_episode_zero_and_season_zero_are_valid_coordinates(self):
        item = make_item(
            media_type="anime", is_anime=True,
            ids=CanonicalIDs(tvdb="267440"), season=0, episode=0,
        )
        route = self.router.route(item)
        self.assertEqual(route.path, "hybrid")
        self.assertEqual(route.entry["seasons"], [
            {"number": 0, "episodes": [{"number": 0}]}
        ])


class TestLegacyModelSupport(unittest.TestCase):
    def setUp(self):
        self.router = SimklPayloadRouter(AnimeSyncMode.AUTO_NATIVE_PREFERRED)

    def test_legacy_anime_with_seasonal_episode_list_routes_hybrid(self):
        item = LegacyStyleItem(
            title="Attack on Titan", media_type="anime",
            ids=CanonicalIDs(tvdb="267440"),
            episodes=[
                {"season": 3, "episode": 13, "watched_at": "2026-07-01"},
                {"season": 3, "episode": 14},
            ],
        )
        route = self.router.route(item)
        self.assertEqual(route.path, "hybrid")
        self.assertEqual(route.entry["seasons"], [
            {"number": 3, "episodes": [
                {"number": 13, "watched_at": "2026-07-01"},
                {"number": 14},
            ]}
        ])

    def test_legacy_anime_flat_episode_list_routes_native(self):
        item = LegacyStyleItem(
            title="One Piece", media_type="anime",
            ids=CanonicalIDs(mal="21"),
            episodes=[{"episode": 403}, {"episode": 404}],
        )
        route = self.router.route(item)
        self.assertEqual(route.path, "native")
        self.assertEqual(route.entry["episodes"], [
            {"number": 403}, {"number": 404}
        ])


class TestContractVectors(unittest.TestCase):
    """Golden vectors: the portable Simkl contract the Kotlin port consumes."""

    def test_all_vectors_match_router_output(self):
        fixture = os.path.join(
            os.path.dirname(__file__), "..", "fixtures",
            "simkl_contract_vectors.json",
        )
        with open(fixture, "r", encoding="utf-8") as f:
            vectors = json.load(f)
        self.assertGreaterEqual(len(vectors["vectors"]), 8)
        for vector in vectors["vectors"]:
            with self.subTest(vector=vector["name"]):
                spec = vector["item"]
                item = make_item(
                    title=spec.get("title", ""),
                    media_type=spec["media_type"],
                    is_anime=spec.get("is_anime", False),
                    year=spec.get("year"),
                    season=spec.get("season"),
                    episode=spec.get("episode"),
                    absolute_episode=spec.get("absolute_episode"),
                    watched_date=spec.get("watched_date"),
                    ids=CanonicalIDs(**spec.get("ids", {})),
                )
                route = SimklPayloadRouter(vector["mode"]).route(item)
                self.assertEqual(route.path, vector["expected"]["path"])
                self.assertEqual(route.envelope, vector["expected"].get("envelope"))
                if "entry" in vector["expected"]:
                    self.assertEqual(route.entry, vector["expected"]["entry"])


if __name__ == "__main__":
    unittest.main()
