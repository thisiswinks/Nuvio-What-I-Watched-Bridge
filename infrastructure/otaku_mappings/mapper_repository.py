import json
import os
import urllib.request
import urllib.error
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OtakuMapperRepository:
    def __init__(self, data_file: str = "data/mappings/anime_lists.json", url: str = "https://raw.githubusercontent.com/Fribb/anime-lists/master/anime-list-full.json"):
        self.data_file = data_file
        self.url = url
        self.mal_index: Dict[str, Any] = {}
        self.title_index: Dict[str, Any] = {}
        self.etag_file = self.data_file + ".etag"

    def check_and_update(self) -> bool:
        """Check ETag and update mappings file if needed."""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        current_etag = ""
        if os.path.exists(self.etag_file):
            with open(self.etag_file, "r", encoding="utf-8") as f:
                current_etag = f.read().strip()
                
        req = urllib.request.Request(self.url, method="HEAD")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                remote_etag = resp.headers.get("ETag", "").strip()
                
            if remote_etag and remote_etag == current_etag and os.path.exists(self.data_file):
                logger.info("Otaku mappings are up to date.")
                return True
                
            # Need update
            logger.info("Downloading new Otaku mappings...")
            get_req = urllib.request.Request(self.url)
            with urllib.request.urlopen(get_req, timeout=30) as get_resp:
                if get_resp.status == 200:
                    data = get_resp.read().decode("utf-8")
                    # Validate JSON before writing
                    json.loads(data)
                    
                    tmp_file = self.data_file + ".tmp"
                    with open(tmp_file, "w", encoding="utf-8") as f:
                        f.write(data)
                    os.replace(tmp_file, self.data_file)
                    
                    if remote_etag:
                        with open(self.etag_file, "w", encoding="utf-8") as f:
                            f.write(remote_etag)
                    return True
        except urllib.error.HTTPError as e:
            logger.error(f"Otaku mappings update HTTP error: {e.code}")
        except json.JSONDecodeError:
            logger.error("Otaku mappings downloaded invalid JSON.")
        except Exception as e:
            logger.error(f"Otaku mappings update failed: {e}")
            
        return False

    def load_indexes(self):
        """Load mappings into memory indexes."""
        if not os.path.exists(self.data_file):
            return
            
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    if "mal_id" in item and item["mal_id"]:
                        self.mal_index[str(item["mal_id"])] = item
                    # Also index by title for broader lookup
                    title = item.get("title", "")
                    if title:
                        self.title_index[title] = item
        except Exception as e:
            logger.error(f"Failed to load Otaku mappings index: {e}")

    def lookup(self, ids: Any, title: str) -> Optional[Dict[str, Any]]:
        """Lookup item by MAL ID or Title."""
        if ids.mal and ids.mal in self.mal_index:
            return self.mal_index[ids.mal]
        if title and title in self.title_index:
            return self.title_index[title]
        return None
