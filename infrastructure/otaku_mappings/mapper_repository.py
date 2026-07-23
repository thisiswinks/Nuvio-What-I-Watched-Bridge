import urllib.request
import json
import os
import logging
from typing import Dict, Any, Optional
from domain.models.canonical_ids import CanonicalIDs

logger = logging.getLogger(__name__)

class OtakuMapperRepository:
    FRIBB_URL = "https://raw.githubusercontent.com/Fribb/anime-lists/master/anime-list-full.json"

    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        self.cache_path = os.path.join(cache_dir, "fribb_mappings.json")
        self.etag_path = os.path.join(cache_dir, "fribb_mappings.etag")
        self.mappings: Dict[str, Any] = {}
        os.makedirs(cache_dir, exist_ok=True)
        self.load_cache()

    def check_and_update(self) -> bool:
        """Check ETag / Last-Modified headers and update only if remote has changed."""
        try:
            req = urllib.request.Request(self.FRIBB_URL, method="HEAD")
            with urllib.request.urlopen(req, timeout=5) as resp:
                remote_etag = resp.headers.get("ETag") or resp.headers.get("Last-Modified")
            
            cached_etag = None
            if os.path.exists(self.etag_path):
                with open(self.etag_path, "r") as f:
                    cached_etag = f.read().strip()
            
            if remote_etag and remote_etag == cached_etag and os.path.exists(self.cache_path):
                logger.info("Otaku mappings are up to date (ETag matched).")
                return False
            
            # Download updated mapping
            logger.info("Downloading updated Otaku mappings...")
            req_get = urllib.request.Request(self.FRIBB_URL)
            with urllib.request.urlopen(req_get, timeout=15) as resp_get:
                data = json.loads(resp_get.read().decode("utf-8"))
                with open(self.cache_path, "w") as f:
                    json.dump(data, f)
                if remote_etag:
                    with open(self.etag_path, "w") as f:
                        f.write(remote_etag)
            self.load_cache()
            return True
        except Exception as e:
            logger.warning(f"Background ETag check failed, using local cache: {e}")
            return False

    def load_cache(self):
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r") as f:
                    raw = json.load(f)
                    # Index by MAL ID & Title for O(1) lookup
                    for entry in raw:
                        mal_id = str(entry.get("mal_id", ""))
                        if mal_id:
                            self.mappings[mal_id] = entry
            except Exception as e:
                logger.error(f"Failed to load Otaku mapping cache: {e}")

    def lookup(self, ids: CanonicalIDs, title: str) -> Optional[Dict[str, Any]]:
        if ids.mal and ids.mal in self.mappings:
            return self.mappings[ids.mal]
        return None
