import urllib.request
import urllib.error
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SimklSyncAdapter:
    def __init__(self, client_id: str, access_token: str, batch_size: int = 100):
        self.client_id = client_id
        self.access_token = access_token
        self.batch_size = batch_size
        self.base_url = "https://api.simkl.com"

    def add_to_history(self, anime_items: List[Dict[str, Any]]) -> bool:
        """Batch add items to Simkl history up to batch_size (100 items per call)."""
        url = f"{self.base_url}/sync/add-to-history"
        success = True
        
        for i in range(0, len(anime_items), self.batch_size):
            chunk = anime_items[i:i+self.batch_size]
            payload = {"shows": chunk}
            data = json.dumps(payload).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "simkl-api-key": self.client_id,
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status not in (200, 201):
                        success = False
            except urllib.error.HTTPError as e:
                logger.error(f"Simkl API add-to-history HTTP error {e.code}: {e.read().decode('utf-8', errors='ignore')}")
                success = False
            except Exception as e:
                logger.error(f"Simkl API add-to-history failed: {e}")
                success = False
                
        return success
