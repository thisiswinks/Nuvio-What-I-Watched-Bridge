import time
import urllib.request
import urllib.parse
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class MALSyncAdapter:
    def __init__(self, access_token: str, rate_delay_ms: int = 600):
        self.access_token = access_token
        self.rate_delay_ms = rate_delay_ms
        self.base_url = "https://api.myanimelist.net/v2"

    def update_anime_status(self, mal_id: str, status: str = "completed", num_watched_episodes: int = 1) -> bool:
        """Update MyAnimeList status with mandatory 600ms delay between calls."""
        url = f"{self.base_url}/anime/{mal_id}/my_list_status"
        params = urllib.parse.urlencode({
            "status": status,
            "num_watched_episodes": num_watched_episodes
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=params,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            method="PUT"
        )
        try:
            time.sleep(self.rate_delay_ms / 1000.0)  # Mandatory rate delay
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status in (200, 201)
        except Exception as e:
            logger.error(f"MAL API v2 update failed for anime ID {mal_id}: {e}")
            return False
