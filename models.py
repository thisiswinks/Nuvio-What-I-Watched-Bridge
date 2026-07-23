from dataclasses import dataclass, field
from enum import Enum
import uuid as uuid_module
from typing import Optional, Dict, Any, List, Union


class MediaType(str, Enum):
    MOVIE = "movie"
    SHOW = "show"
    ANIME = "anime"


class MediaStatus(str, Enum):
    COMPLETED = "completed"
    WATCHING = "watching"
    ON_HOLD = "on_hold"
    PLAN_TO_WATCH = "plan_to_watch"
    DROPPED = "dropped"


@dataclass
class CanonicalIDs:
    imdb: Optional[str] = None
    tmdb: Optional[Union[str, int]] = None
    tvdb: Optional[Union[str, int]] = None
    mal: Optional[Union[str, int]] = None
    kitsu: Optional[Union[str, int]] = None
    anidb: Optional[Union[str, int]] = None
    simkl: Optional[Union[str, int]] = None
    trakt: Optional[Union[str, int]] = None
    nuvio: Optional[str] = None

    def matching_id_count(self, other: "CanonicalIDs") -> int:
        count = 0
        fields = [
            "imdb",
            "tmdb",
            "tvdb",
            "mal",
            "kitsu",
            "anidb",
            "simkl",
            "trakt",
            "nuvio",
        ]
        for f in fields:
            val1 = getattr(self, f)
            val2 = getattr(other, f)
            if (
                val1 is not None
                and val2 is not None
                and val1 != ""
                and val2 != ""
                and str(val1) == str(val2)
            ):
                count += 1
        return count

    def merge(self, other: "CanonicalIDs") -> "CanonicalIDs":
        fields = [
            "imdb",
            "tmdb",
            "tvdb",
            "mal",
            "kitsu",
            "anidb",
            "simkl",
            "trakt",
            "nuvio",
        ]
        kwargs = {}
        for f in fields:
            val1 = getattr(self, f)
            val2 = getattr(other, f)
            kwargs[f] = val1 if (val1 is not None and val1 != "") else val2
        return CanonicalIDs(**kwargs)


@dataclass
class SourceRecord:
    source_name: str
    present: bool = True
    status: Optional[str] = None
    rating: Optional[float] = None
    watch_count: int = 0
    last_watched_at: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalMediaItem:
    uuid: str = field(default_factory=lambda: str(uuid_module.uuid4()))
    media_type: MediaType = MediaType.MOVIE
    title: str = ""
    title_original: Optional[str] = None
    year: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    ids: CanonicalIDs = field(default_factory=CanonicalIDs)
    aggregated_status: Optional[MediaStatus] = None
    aggregated_rating: Optional[float] = None
    sources: Dict[str, SourceRecord] = field(default_factory=dict)
    episodes: List[Dict[str, Any]] = field(default_factory=list)
    history_logs: List[Dict[str, Any]] = field(default_factory=list)

    def deduplicate_episodes(self) -> None:
        if not self.episodes:
            return
        episodes_by_key = {}
        for ep in self.episodes:
            s = ep.get("season")
            e = ep.get("episode")
            key = (s if s is not None else 1, e if e is not None else 1)
            
            if key not in episodes_by_key:
                episodes_by_key[key] = dict(ep)
            else:
                existing = episodes_by_key[key]
                w1 = existing.get("watched_at")
                w2 = ep.get("watched_at")
                if w1 and w2:
                    existing["watched_at"] = min(w1, w2)
                elif w2:
                    existing["watched_at"] = w2
                
                if not existing.get("title") and ep.get("title"):
                    existing["title"] = ep.get("title")
                    
                if "ids" in ep and isinstance(ep["ids"], CanonicalIDs):
                    if "ids" in existing and isinstance(existing["ids"], CanonicalIDs):
                        existing["ids"] = existing["ids"].merge(ep["ids"])
                    else:
                        existing["ids"] = ep["ids"]
                        
        self.episodes = sorted(
            episodes_by_key.values(),
            key=lambda x: (
                x.get("season") if x.get("season") is not None else 1,
                x.get("episode") if x.get("episode") is not None else 1
            )
        )
