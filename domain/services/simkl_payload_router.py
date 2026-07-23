"""Pure routing of canonical media items onto Simkl's anime write contract.

Implements the two integration paths from https://api.simkl.org/guides/anime
(guide as published 2026-07; recorded in docs/adr/0001):

- Path B (native): anime with a native-database id (MAL/AniList/AniDB/Kitsu)
  and evidence-based absolute episode numbers -> ``anime[]`` envelope with
  flat episode numbers and no season coordinates.
- Path A (hybrid): anime with TMDB/TVDB identity and TVDB season/episode
  coordinates -> ``shows[]`` envelope with ``use_tvdb_anime_seasons: true``
  so Simkl resolves per-cour splits and absolute numbering itself.

A shared TMDB/TVDB parent id is never turned into a cour-specific identity
here; items that fit neither path quarantine as ``needs_identity``.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class AnimeSyncMode(str, Enum):
    AUTO_NATIVE_PREFERRED = "auto_native_preferred"
    TVDB_HYBRID_ONLY = "tvdb_hybrid_only"
    NATIVE_ONLY = "native_only"


NATIVE_ID_FIELDS = ("mal", "anilist", "anidb", "kitsu")
HYBRID_ID_FIELDS = ("tmdb", "tvdb")
SERIES_TYPES = ("show", "series")


@dataclass
class SimklRoute:
    path: str  # native | hybrid | standard | needs_identity
    envelope: Optional[str]  # anime | shows | movies | None
    entry: Optional[Dict[str, Any]]
    reason: str


def _clean_ids(ids: Any) -> Dict[str, Any]:
    """Extract non-empty ids, canonicalizing digit-only values to int."""
    cleaned: Dict[str, Any] = {}
    for field in ("imdb", "tmdb", "tvdb", "mal", "anilist", "kitsu", "anidb",
                  "simkl", "trakt", "slug"):
        value = getattr(ids, field, None)
        if value is None or value == "":
            continue
        if isinstance(value, str) and value.isdigit():
            value = int(value)
        cleaned[field] = value
    return cleaned


def _media_type_str(item: Any) -> str:
    media_type = getattr(item, "media_type", "")
    return str(getattr(media_type, "value", media_type)).lower()


def _episode_dicts(item: Any) -> List[Dict[str, Any]]:
    episodes = getattr(item, "episodes", None)
    return list(episodes) if isinstance(episodes, list) else []


def _flat_episodes(item: Any) -> List[Dict[str, Any]]:
    """Absolute-numbered episodes, only when provenance exists.

    Provenance = a scalar ``absolute_episode`` (set by the source or by
    Otaku-Mappings offset enrichment) or legacy episode entries that carry
    no season coordinate at all. Seasonal coordinates are never converted
    to absolute numbers here.
    """
    absolute = getattr(item, "absolute_episode", None)
    if absolute is not None:
        entry: Dict[str, Any] = {"number": absolute}
        watched = getattr(item, "watched_date", None)
        if watched:
            entry["watched_at"] = watched
        return [entry]
    flat: List[Dict[str, Any]] = []
    for ep in _episode_dicts(item):
        number = ep.get("absolute") if ep.get("absolute") is not None else ep.get("episode")
        if number is None or ep.get("season") is not None:
            return []
        entry = {"number": number}
        if ep.get("watched_at"):
            entry["watched_at"] = ep["watched_at"]
        flat.append(entry)
    return flat


def _seasonal_episodes(item: Any) -> List[Dict[str, Any]]:
    """TVDB-shaped ``seasons[]`` blocks, or [] when no coordinates exist."""
    season = getattr(item, "season", None)
    episode = getattr(item, "episode", None)
    if season is not None and episode is not None:
        entry: Dict[str, Any] = {"number": episode}
        watched = getattr(item, "watched_date", None)
        if watched:
            entry["watched_at"] = watched
        return [{"number": season, "episodes": [entry]}]
    grouped: Dict[Any, List[Dict[str, Any]]] = {}
    for ep in _episode_dicts(item):
        if ep.get("season") is None or ep.get("episode") is None:
            return []
        entry = {"number": ep["episode"]}
        if ep.get("watched_at"):
            entry["watched_at"] = ep["watched_at"]
        grouped.setdefault(ep["season"], []).append(entry)
    return [
        {"number": number, "episodes": eps}
        for number, eps in sorted(grouped.items())
    ]


class SimklPayloadRouter:
    def __init__(self, mode: Any = AnimeSyncMode.AUTO_NATIVE_PREFERRED):
        try:
            self.mode = AnimeSyncMode(mode)
        except ValueError:
            raise ValueError(
                f"Unknown Simkl anime_mode {mode!r}; expected one of "
                f"{[m.value for m in AnimeSyncMode]}"
            )

    def route(self, item: Any) -> SimklRoute:
        media_type = _media_type_str(item)
        is_anime = bool(getattr(item, "is_anime", False)) or media_type == "anime"
        ids = _clean_ids(getattr(item, "ids", None))

        if not ids:
            return self._quarantine(item, "no usable external ids")
        if media_type not in ("movie", "anime") + SERIES_TYPES:
            return self._quarantine(item, f"unknown media_type {media_type!r}")

        if not is_anime:
            return self._route_standard(item, media_type, ids)
        return self._route_anime(item, media_type, ids)

    # -- non-anime -------------------------------------------------------

    def _route_standard(self, item: Any, media_type: str, ids: Dict[str, Any]) -> SimklRoute:
        entry = self._base_entry(item, ids)
        if media_type == "movie":
            watched = getattr(item, "watched_date", None)
            if watched:
                entry["watched_at"] = watched
            return SimklRoute("standard", "movies", entry, "movie: standard entry")
        seasons = _seasonal_episodes(item)
        if not seasons:
            return self._quarantine(
                item,
                "series history write without episode coordinates would mark "
                "the entire show watched",
            )
        entry["seasons"] = seasons
        return SimklRoute("standard", "shows", entry, "show: standard seasonal entry")

    # -- anime -----------------------------------------------------------

    def _route_anime(self, item: Any, media_type: str, ids: Dict[str, Any]) -> SimklRoute:
        native = self._try_native(item, media_type, ids)
        hybrid = self._try_hybrid(item, ids)

        if self.mode == AnimeSyncMode.NATIVE_ONLY:
            if native:
                return native
            return self._quarantine(
                item, "native_only: no native id with absolute-episode provenance"
            )
        if self.mode == AnimeSyncMode.TVDB_HYBRID_ONLY:
            if hybrid:
                return hybrid
            if media_type == "movie":
                return self._route_standard(item, "movie", ids)
            return self._quarantine(
                item, "tvdb_hybrid_only: no tmdb/tvdb id with season coordinates"
            )
        if native:
            return native
        if hybrid:
            return hybrid
        if media_type == "movie":
            return self._route_standard(item, "movie", ids)
        # Episode-less anime typed as "anime" is ambiguous: a film is one unit
        # (safe to send), but a series would mark every episode watched. Without
        # a movie signal we cannot tell them apart, so we quarantine rather than
        # risk corrupting a whole series. Anime films must reach the router as
        # media_type="movie" (Nuvio playback events do this) to sync as a unit.
        native_present = any(k in ids for k in NATIVE_ID_FIELDS)
        if native_present:
            return self._quarantine(
                item,
                "episode-less anime with a native id is ambiguous between a film "
                "and a whole series; type anime films as media_type='movie' to "
                "sync them as a single unit",
            )
        return self._quarantine(
            item,
            "anime lacks both a native id with absolute-episode provenance and "
            "tmdb/tvdb season coordinates; refusing to guess identity from a "
            "shared parent id",
        )

    def _try_native(self, item: Any, media_type: str, ids: Dict[str, Any]) -> Optional[SimklRoute]:
        native_ids = {k: ids[k] for k in NATIVE_ID_FIELDS if k in ids}
        if not native_ids:
            return None
        if "simkl" in ids:
            native_ids["simkl"] = ids["simkl"]
        entry: Dict[str, Any] = {"ids": native_ids}
        title = getattr(item, "title", None)
        if title:
            entry["title"] = title
        year = getattr(item, "year", None)
        if year:
            entry["year"] = year
        if media_type == "movie":
            watched = getattr(item, "watched_date", None)
            if watched:
                entry["watched_at"] = watched
            return SimklRoute(
                "native", "anime", entry,
                "anime movie via native ids (Path B, single unit)",
            )
        episodes = _flat_episodes(item)
        if not episodes:
            return None
        entry["episodes"] = episodes
        return SimklRoute(
            "native", "anime", entry,
            "native id + absolute episode provenance (Path B)",
        )

    def _try_hybrid(self, item: Any, ids: Dict[str, Any]) -> Optional[SimklRoute]:
        hybrid_ids = {k: ids[k] for k in HYBRID_ID_FIELDS if k in ids}
        if not hybrid_ids:
            return None
        seasons = _seasonal_episodes(item)
        if not seasons:
            return None
        entry = self._base_entry(item, hybrid_ids)
        entry["use_tvdb_anime_seasons"] = True
        entry["seasons"] = seasons
        return SimklRoute(
            "hybrid", "shows", entry,
            "tmdb/tvdb id + TVDB season coordinates (Path A)",
        )

    # -- helpers ---------------------------------------------------------

    @staticmethod
    def _base_entry(item: Any, ids: Dict[str, Any]) -> Dict[str, Any]:
        entry: Dict[str, Any] = {}
        title = getattr(item, "title", None)
        if title:
            entry["title"] = title
        year = getattr(item, "year", None)
        if year:
            entry["year"] = year
        entry["ids"] = ids
        return entry

    @staticmethod
    def _quarantine(item: Any, reason: str) -> SimklRoute:
        return SimklRoute("needs_identity", None, None, reason)
