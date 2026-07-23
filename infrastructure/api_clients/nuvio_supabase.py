import urllib.request
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class NuvioSupabaseAdapter:
    def __init__(self, api_key: str, bearer_token: str, base_url: str = "https://api.nuvio.tv/rest/v1"):
        self.api_key = api_key
        self.bearer_token = bearer_token
        self.base_url = base_url.rstrip("/")

    def push_watched_items(self, profile_id: int, items: List[Dict[str, Any]]) -> bool:
        """Push watched items to Nuvio TV Supabase RPC sync_push_watched_items."""
        url = f"{self.base_url}/rpc/sync_push_watched_items"
        payload = {
            "p_items": items,
            "p_profile_id": profile_id
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "apikey": self.api_key,
                "authorization": f"Bearer {self.bearer_token}",
                "content-type": "application/json",
                "x-client-info": "WhatIWatchedSync/1.0"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status in (200, 201)
        except Exception as e:
            logger.error(f"Nuvio Supabase RPC push failed: {e}")
            return False
