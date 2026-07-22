import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from models import CanonicalIDs, MediaType

MAPPING_URL = "https://raw.githubusercontent.com/Fribb/anime-lists/master/anime-list-mini.json"
LOCAL_CACHE_PATH = Path("data/otaku_mappings.json")


def _norm_title(title: Optional[str]) -> str:
    if not title:
        return ""
    cleaned = re.sub(r"[^\w\s]", "", title.lower())
    return re.sub(r"\s+", "", cleaned).strip()


class OtakuMapper:
    def __init__(self, cache_path: Path = LOCAL_CACHE_PATH):
        self.cache_path = cache_path
        self.by_tvdb: Dict[str, Dict[str, Any]] = {}
        self.by_tmdb: Dict[str, Dict[str, Any]] = {}
        self.by_imdb: Dict[str, Dict[str, Any]] = {}
        self.by_mal: Dict[str, Dict[str, Any]] = {}
        self.by_simkl: Dict[str, Dict[str, Any]] = {}
        self.by_kitsu: Dict[str, Dict[str, Any]] = {}
        self.by_anidb: Dict[str, Dict[str, Any]] = {}
        self.by_title: Dict[str, Dict[str, Any]] = {}
        self._loaded = False
        self.load_mappings()

    def load_mappings(self) -> None:
        if not self.cache_path.exists():
            try:
                self.cache_path.parent.mkdir(parents=True, exist_ok=True)
                req = urllib.request.Request(MAPPING_URL, headers={"User-Agent": "MediaSyncPipeline/1.0"})
                with urllib.request.urlopen(req) as resp:
                    raw_bytes = resp.read()
                    with open(self.cache_path, "wb") as f:
                        f.write(raw_bytes)
            except Exception as e:
                print(f"Warning: Failed to download Otaku Mappings: {e}")
                return

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._index_entries(data)
                self._loaded = True
        except Exception as e:
            print(f"Warning: Failed to load local Otaku Mappings cache: {e}")

    def _index_entries(self, data: List[Dict[str, Any]]) -> None:
        for entry in data:
            # Index by TVDB
            tvdb = entry.get("tvdb_id")
            if tvdb:
                self.by_tvdb[str(tvdb)] = entry

            # Index by TMDB
            tmdb_val = entry.get("themoviedb_id")
            if isinstance(tmdb_val, dict):
                for sub_id in list(tmdb_val.values()):
                    if isinstance(sub_id, list):
                        for sid in sub_id:
                            self.by_tmdb[str(sid)] = entry
                    elif sub_id:
                        self.by_tmdb[str(sub_id)] = entry
            elif tmdb_val:
                self.by_tmdb[str(tmdb_val)] = entry

            # Index by IMDB
            imdb_val = entry.get("imdb_id")
            if isinstance(imdb_val, list):
                for idb in imdb_val:
                    if idb:
                        self.by_imdb[str(idb)] = entry
            elif imdb_val:
                self.by_imdb[str(imdb_val)] = entry

            # Index by MAL
            mal = entry.get("mal_id")
            if mal:
                self.by_mal[str(mal)] = entry

            # Index by SIMKL
            simkl = entry.get("simkl_id")
            if simkl:
                self.by_simkl[str(simkl)] = entry

            # Index by Kitsu
            kitsu = entry.get("kitsu_id")
            if kitsu:
                self.by_kitsu[str(kitsu)] = entry

            # Index by AniDB
            anidb = entry.get("anidb_id")
            if anidb:
                self.by_anidb[str(anidb)] = entry

            # Index by title / planet slug
            planet_id = entry.get("anime-planet_id")
            if planet_id:
                self.by_title[_norm_title(planet_id.replace("-", " "))] = entry

    def lookup(self, ids: CanonicalIDs, title: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self._loaded:
            return None

        # Check each ID individually, falling through if not found
        if ids.mal and str(ids.mal) in self.by_mal:
            return self.by_mal[str(ids.mal)]
        if ids.tmdb and str(ids.tmdb) in self.by_tmdb:
            return self.by_tmdb[str(ids.tmdb)]
        if ids.imdb and str(ids.imdb) in self.by_imdb:
            return self.by_imdb[str(ids.imdb)]
        if ids.tvdb and str(ids.tvdb) in self.by_tvdb:
            return self.by_tvdb[str(ids.tvdb)]
        if ids.simkl and str(ids.simkl) in self.by_simkl:
            return self.by_simkl[str(ids.simkl)]
        if ids.kitsu and str(ids.kitsu) in self.by_kitsu:
            return self.by_kitsu[str(ids.kitsu)]
        if ids.anidb and str(ids.anidb) in self.by_anidb:
            return self.by_anidb[str(ids.anidb)]

        if title:
            t_norm = _norm_title(title)
            if t_norm and t_norm in self.by_title:
                return self.by_title[t_norm]

        return None

    def enrich_item_ids(self, ids: CanonicalIDs, title: Optional[str] = None) -> Tuple[CanonicalIDs, bool]:
        match = self.lookup(ids, title)
        if not match:
            return ids, False

        mal_id = str(match["mal_id"]) if match.get("mal_id") else None
        simkl_id = match.get("simkl_id")
        kitsu_id = str(match["kitsu_id"]) if match.get("kitsu_id") else None
        anidb_id = str(match["anidb_id"]) if match.get("anidb_id") else None
        tvdb_id = str(match["tvdb_id"]) if match.get("tvdb_id") else None

        imdb_val = match.get("imdb_id")
        imdb_id = None
        if isinstance(imdb_val, list) and imdb_val:
            imdb_id = str(imdb_val[0])
        elif isinstance(imdb_val, str):
            imdb_id = imdb_val

        tmdb_val = match.get("themoviedb_id")
        tmdb_id = None
        if isinstance(tmdb_val, dict):
            for v in tmdb_val.values():
                if isinstance(v, list) and v:
                    tmdb_id = str(v[0])
                    break
                elif v:
                    tmdb_id = str(v)
                    break
        elif tmdb_val:
            tmdb_id = str(tmdb_val)

        enriched = CanonicalIDs(
            imdb=ids.imdb or imdb_id,
            tmdb=ids.tmdb or tmdb_id,
            tvdb=ids.tvdb or tvdb_id,
            mal=ids.mal or mal_id,
            kitsu=ids.kitsu or kitsu_id,
            anidb=ids.anidb or anidb_id,
            simkl=ids.simkl or simkl_id,
            trakt=ids.trakt,
            nuvio=ids.nuvio,
        )
        return enriched, True
