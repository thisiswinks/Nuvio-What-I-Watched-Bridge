import uuid
from collections import defaultdict
from typing import Dict, Any, List, Optional, Union
from models import (
    CanonicalMediaItem,
    CanonicalIDs,
    SourceRecord,
    MediaType,
    MediaStatus,
)


def _parse_rating(val: Optional[Any]) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        r = float(val)
        return r if r > 0 else None
    except (ValueError, TypeError):
        return None


def _parse_status(val: Optional[Any]) -> MediaStatus:
    if val is None:
        return MediaStatus.COMPLETED

    if isinstance(val, (int, str)):
        s = str(val).strip().lower().replace("-", "_").replace(" ", "_")
        if s in ("completed", "complete", "watched", "finished", "2"):
            return MediaStatus.COMPLETED
        if s in ("watching", "currently_watching", "1"):
            return MediaStatus.WATCHING
        if s in ("on_hold", "onhold", "hold", "paused", "3"):
            return MediaStatus.ON_HOLD
        if s in (
            "plan_to_watch",
            "plantowatch",
            "watchlist",
            "plan_to_read",
            "planning",
            "6",
        ):
            return MediaStatus.PLAN_TO_WATCH
        if s in ("dropped", "drop", "4"):
            return MediaStatus.DROPPED

    return MediaStatus.COMPLETED


def _parse_year(val: Optional[Any], date_str: Optional[str] = None) -> Optional[int]:
    if val is not None:
        try:
            y = int(val)
            if 1900 <= y <= 2100:
                return y
        except (ValueError, TypeError):
            pass
    if date_str and isinstance(date_str, str) and len(date_str) >= 4:
        try:
            y = int(date_str[:4])
            if 1900 <= y <= 2100:
                return y
        except (ValueError, TypeError):
            pass
    return None


def _extract_canonical_ids(
    raw: Dict[str, Any], default_source: str = ""
) -> CanonicalIDs:
    ids_dict: Dict[str, Any] = {}

    for key in ("ids", "episode", "movie", "show", "anime"):
        val = raw.get(key)
        if isinstance(val, dict):
            if key == "ids":
                ids_dict.update(val)
            elif "ids" in val and isinstance(val["ids"], dict):
                ids_dict.update(val["ids"])


    def get_id(keys: List[str]) -> Optional[Any]:
        for k in keys:
            if k in ids_dict and ids_dict[k] is not None and ids_dict[k] != "":
                return ids_dict[k]
            if k in raw and raw[k] is not None and raw[k] != "":
                return raw[k]
        return None

    imdb = get_id(["imdb", "imdb_id", "imdbId"])
    tmdb = get_id(["tmdb", "tmdb_id", "tmdbId"])
    tvdb = get_id(["tvdb", "tvdb_id", "tvdbId"])
    mal = get_id(["mal", "mal_id", "malId", "series_animedb_id"])
    kitsu = get_id(["kitsu", "kitsu_id", "kitsuId"])
    anidb = get_id(["anidb", "anidb_id", "anidbId"])
    simkl = get_id(["simkl", "simkl_id", "simklId"])
    trakt = get_id(["trakt", "trakt_id", "traktId"])
    nuvio = get_id(["nuvio", "nuvio_id", "nuvioId"])

    if nuvio is None and default_source == "nuvio":
        raw_id = raw.get("id")
        if raw_id and isinstance(raw_id, str):
            nuvio = raw_id

    def parse_imdb(val: Optional[Any]) -> Optional[str]:
        if not val:
            return None
        v = str(val).strip()
        if not v or v in ("0", "null", "none", "None", "tt0000000"):
            return None
        return v

    def parse_int_or_str(val: Optional[Any]) -> Optional[Union[str, int]]:
        if val is None:
            return None
        if isinstance(val, int):
            return val if val > 0 else None
        if isinstance(val, str):
            v = val.strip()
            if not v or v in ("0", "null", "none", "None", "0000"):
                return None
            if v.isdigit():
                iv = int(v)
                return iv if iv > 0 else None
            return v
        return None

    return CanonicalIDs(
        imdb=parse_imdb(imdb),
        tmdb=parse_int_or_str(tmdb),
        tvdb=parse_int_or_str(tvdb),
        mal=parse_int_or_str(mal),
        kitsu=parse_int_or_str(kitsu),
        anidb=parse_int_or_str(anidb),
        simkl=parse_int_or_str(simkl),
        trakt=parse_int_or_str(trakt),
        nuvio=parse_imdb(nuvio),
    )


def _parse_episode(raw_entry: Dict[str, Any], ep_obj: Dict[str, Any]) -> Dict[str, Any]:
    ep_ids = _extract_canonical_ids(ep_obj, default_source="trakt")
    return {
        "season": ep_obj.get("season", 1),
        "episode": ep_obj.get("number") or ep_obj.get("episode") or 1,
        "watched_at": raw_entry.get("watched_at") or raw_entry.get("last_watched_at"),
        "title": ep_obj.get("title"),
        "ids": ep_ids,
    }


def normalize_mal_item(raw: Dict[str, Any]) -> CanonicalMediaItem:
    ids = _extract_canonical_ids(raw, default_source="mal")
    title = (
        raw.get("series_title")
        or raw.get("title")
        or "Unknown Title"
    )
    title_orig = (
        raw.get("series_title_original")
        or raw.get("japanese_title")
        or raw.get("title_original")
    )
    start_date = raw.get("my_start_date") or raw.get("start_date")
    if start_date == "0000-00-00":
        start_date = None
    end_date = raw.get("my_finish_date") or raw.get("end_date")
    if end_date == "0000-00-00":
        end_date = None

    year = _parse_year(raw.get("year"), start_date)
    score = _parse_rating(raw.get("my_score") or raw.get("score"))
    status = _parse_status(raw.get("my_status") or raw.get("status"))

    series_type = str(raw.get("series_type", "")).lower()
    media_type = MediaType.ANIME
    if series_type == "movie":
        media_type = MediaType.ANIME  # In MAL anime movies are anime

    source_rec = SourceRecord(
        source_name="mal",
        present=True,
        status=raw.get("my_status"),
        rating=score,
        watch_count=int(raw.get("my_times_watched", 0) or 0),
        last_watched_at=end_date,
        raw=raw,
    )

    return CanonicalMediaItem(
        uuid=str(uuid.uuid4()),
        media_type=media_type,
        title=title,
        title_original=title_orig,
        year=year,
        start_date=start_date,
        end_date=end_date,
        ids=ids,
        aggregated_status=status,
        aggregated_rating=score,
        sources={"mal": source_rec},
    )


def normalize_trakt_item(raw: Dict[str, Any]) -> CanonicalMediaItem:
    ids = _extract_canonical_ids(raw, default_source="trakt")

    # Determine item title, year, and media_type
    movie_obj = raw.get("movie") if isinstance(raw.get("movie"), dict) else None
    show_obj = raw.get("show") if isinstance(raw.get("show"), dict) else None
    episode_obj = raw.get("episode") if isinstance(raw.get("episode"), dict) else None

    title = "Unknown Title"
    year = None
    media_type = MediaType.MOVIE

    type_str = str(raw.get("type", "")).lower()

    if movie_obj:
        title = movie_obj.get("title", title)
        year = movie_obj.get("year")
        media_type = MediaType.MOVIE
    elif show_obj:
        title = show_obj.get("title", title)
        year = show_obj.get("year")
        media_type = MediaType.SHOW
    elif episode_obj:
        title = episode_obj.get("title", title)
        media_type = MediaType.SHOW
    elif "title" in raw:
        title = raw["title"]
        year = raw.get("year")

    if type_str == "show" or type_str == "episode":
        media_type = MediaType.SHOW
    elif type_str == "movie":
        media_type = MediaType.MOVIE
    elif type_str == "anime":
        media_type = MediaType.ANIME

    episodes = []
    if episode_obj:
        episodes.append(_parse_episode(raw, episode_obj))

    year_val = _parse_year(year, raw.get("last_watched_at") or raw.get("watched_at"))
    score = _parse_rating(raw.get("rating") or raw.get("user_rating"))

    # Determine status from file context or watched timestamps
    status_raw = raw.get("status")
    if not status_raw:
        if raw.get("last_watched_at") or raw.get("watched_at") or raw.get("plays", 0) > 0:
            status_raw = "completed"
        elif "_source_file" in raw and "watchlist" in str(raw["_source_file"]).lower():
            status_raw = "plan_to_watch"

    status = _parse_status(status_raw)

    source_rec = SourceRecord(
        source_name="trakt",
        present=True,
        status=status_raw,
        rating=score,
        watch_count=int(raw.get("plays", 1 if status == MediaStatus.COMPLETED else 0)),
        last_watched_at=raw.get("last_watched_at") or raw.get("watched_at"),
        raw=raw,
    )

    return CanonicalMediaItem(
        uuid=str(uuid.uuid4()),
        media_type=media_type,
        title=title,
        year=year_val,
        ids=ids,
        aggregated_status=status,
        aggregated_rating=score,
        sources={"trakt": source_rec},
        episodes=episodes,
    )



def normalize_simkl_item(raw: Dict[str, Any]) -> CanonicalMediaItem:
    ids = _extract_canonical_ids(raw, default_source="simkl")
    title = raw.get("title") or raw.get("name") or "Unknown Title"

    type_str = str(raw.get("media_type") or raw.get("type", "")).lower()
    if type_str in ("anime", "animes"):
        media_type = MediaType.ANIME
    elif type_str in ("movie", "movies"):
        media_type = MediaType.MOVIE
    else:
        media_type = MediaType.SHOW

    year = _parse_year(raw.get("year"), raw.get("last_watched_at"))
    score = _parse_rating(raw.get("user_rating") or raw.get("rating") or raw.get("score"))
    status = _parse_status(raw.get("status"))

    source_rec = SourceRecord(
        source_name="simkl",
        present=True,
        status=raw.get("status"),
        rating=score,
        watch_count=int(raw.get("watched_episodes_count", 0) or (1 if status == MediaStatus.COMPLETED else 0)),
        last_watched_at=raw.get("last_watched_at"),
        raw=raw,
    )

    return CanonicalMediaItem(
        uuid=str(uuid.uuid4()),
        media_type=media_type,
        title=title,
        year=year,
        ids=ids,
        aggregated_status=status,
        aggregated_rating=score,
        sources={"simkl": source_rec},
    )


def normalize_nuvio_item(raw: Dict[str, Any]) -> CanonicalMediaItem:
    ids = _extract_canonical_ids(raw, default_source="nuvio")
    title = raw.get("title") or raw.get("name") or "Unknown Title"

    media_type_str = str(raw.get("mediaType") or raw.get("media_type") or raw.get("type", "")).upper()
    if media_type_str == "ANIME":
        media_type = MediaType.ANIME
    elif media_type_str in ("TV", "SHOW", "SERIES"):
        media_type = MediaType.SHOW
    else:
        media_type = MediaType.MOVIE

    year = _parse_year(raw.get("year"))
    score = _parse_rating(raw.get("rating") or raw.get("score"))
    status = _parse_status(raw.get("status"))

    source_rec = SourceRecord(
        source_name="nuvio",
        present=True,
        status=raw.get("status"),
        rating=score,
        raw=raw,
    )

    return CanonicalMediaItem(
        uuid=str(uuid.uuid4()),
        media_type=media_type,
        title=title,
        year=year,
        ids=ids,
        aggregated_status=status,
        aggregated_rating=score,
        sources={"nuvio": source_rec},
    )



def normalize_all_sources(
    extracted: Dict[str, List[Dict[str, Any]]]
) -> List[CanonicalMediaItem]:
    from otaku_mapper import OtakuMapper

    mapper = OtakuMapper()
    normalized_items: List[CanonicalMediaItem] = []

    # Identify Trakt source keys vs non-Trakt keys
    trakt_keys = [k for k in extracted.keys() if "trakt" in k.lower()]
    non_trakt_keys = [k for k in extracted.keys() if "trakt" not in k.lower()]

    # 1. Pre-group Trakt show scrobbles by parent show ID
    trakt_raw_list: List[Dict[str, Any]] = []
    for k in trakt_keys:
        items = extracted.get(k)
        if not items:
            continue
        if isinstance(items, dict):
            for sub_key, sub_items in items.items():
                if isinstance(sub_items, list):
                    for sub_item in sub_items:
                        if isinstance(sub_item, dict):
                            if "media_type" not in sub_item:
                                sub_item["media_type"] = sub_key
                            trakt_raw_list.append(sub_item)
        elif isinstance(items, list):
            trakt_raw_list.extend([i for i in items if isinstance(i, dict)])

    trakt_show_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    trakt_other: List[Dict[str, Any]] = []

    for raw in trakt_raw_list:
        show_obj = raw.get("show") if isinstance(raw.get("show"), dict) else None
        s_ids = (
            show_obj.get("ids")
            if (show_obj and isinstance(show_obj.get("ids"), dict))
            else None
        )

        key = None
        if s_ids:
            if s_ids.get("imdb"):
                key = f"imdb:{s_ids['imdb']}"
            elif s_ids.get("tmdb"):
                key = f"tmdb:{s_ids['tmdb']}"
            elif s_ids.get("tvdb"):
                key = f"tvdb:{s_ids['tvdb']}"
            elif s_ids.get("trakt"):
                key = f"trakt:{s_ids['trakt']}"

        if key:
            trakt_show_groups[key].append(raw)
        else:
            trakt_other.append(raw)

    for key, group in trakt_show_groups.items():
        base_item = normalize_trakt_item(group[0])
        combined_episodes = []
        for raw_entry in group:
            ep_obj = (
                raw_entry.get("episode")
                if isinstance(raw_entry.get("episode"), dict)
                else None
            )
            if ep_obj:
                combined_episodes.append(_parse_episode(raw_entry, ep_obj))
        base_item.episodes = combined_episodes
        if "trakt" in base_item.sources:
            base_item.sources["trakt"].watch_count = len(group)
            watched_times = [
                r.get("watched_at") or r.get("last_watched_at")
                for r in group
                if (r.get("watched_at") or r.get("last_watched_at"))
            ]
            if watched_times:
                base_item.sources["trakt"].last_watched_at = max(watched_times)

        enriched_ids, is_anime = mapper.enrich_item_ids(base_item.ids, base_item.title)
        base_item.ids = enriched_ids
        if is_anime:
            base_item.media_type = MediaType.ANIME
        normalized_items.append(base_item)

    for raw in trakt_other:
        item = normalize_trakt_item(raw)
        enriched_ids, is_anime = mapper.enrich_item_ids(item.ids, item.title)
        item.ids = enriched_ids
        if is_anime:
            item.media_type = MediaType.ANIME
        normalized_items.append(item)

    # 2. Process non-Trakt sources
    for source_key in non_trakt_keys:
        items = extracted.get(source_key)
        if not items:
            continue

        item_list: List[Dict[str, Any]] = []
        if isinstance(items, dict):
            for sub_key, sub_items in items.items():
                if isinstance(sub_items, list):
                    for sub_item in sub_items:
                        if isinstance(sub_item, dict):
                            if "media_type" not in sub_item:
                                sub_item["media_type"] = sub_key
                            item_list.append(sub_item)
        elif isinstance(items, list):
            item_list = [i for i in items if isinstance(i, dict)]

        source_lower = source_key.lower()

        for raw_item in item_list:
            if "mal" in source_lower:
                item = normalize_mal_item(raw_item)
            elif "simkl" in source_lower:
                item = normalize_simkl_item(raw_item)
            elif "nuvio" in source_lower:
                item = normalize_nuvio_item(raw_item)
            else:
                if "series_animedb_id" in raw_item:
                    item = normalize_mal_item(raw_item)
                elif "trakt" in raw_item.get("ids", {}) or "_source_file" in raw_item:
                    item = normalize_trakt_item(raw_item)
                elif "simkl" in raw_item.get("ids", {}):
                    item = normalize_simkl_item(raw_item)
                else:
                    item = normalize_simkl_item(raw_item)

            enriched_ids, is_anime = mapper.enrich_item_ids(item.ids, item.title)
            item.ids = enriched_ids
            if is_anime:
                item.media_type = MediaType.ANIME

            normalized_items.append(item)

    return normalized_items


