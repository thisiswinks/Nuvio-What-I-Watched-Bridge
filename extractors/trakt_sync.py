import urllib.request
import urllib.parse
import json
import logging
from typing import List, Dict, Any, Optional
from extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


class TraktSyncExtractor(BaseExtractor):
    """
    Live API extractor for Trakt.tv watch history.
    Polls /sync/history/episodes and /sync/history/movies using Trakt API v2.
    """
    def __init__(
        self,
        client_id: str,
        access_token: Optional[str] = None,
        since_iso: Optional[str] = None,
        api_url: str = "https://api.trakt.tv"
    ):
        self.client_id = client_id
        self.access_token = access_token
        self.since_iso = since_iso
        self.api_url = api_url.rstrip("/")

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "trakt-api-version": "2",
            "trakt-api-key": self.client_id
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _fetch_endpoint(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}?{query}"
            
        req = urllib.request.Request(url, headers=self._get_headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if isinstance(data, list):
                        return data
        except Exception as e:
            logger.error(f"Failed to fetch Trakt history from {url}: {e}")
        return []

    def fetch_episodes(self, limit: int = 100) -> List[Dict[str, Any]]:
        params = {"limit": limit, "extended": "full"}
        if self.since_iso:
            params["start_at"] = self.since_iso
        data = self._fetch_endpoint("sync/history/episodes", params)
        for item in data:
            item["_source_file"] = "trakt_api_episodes.json"
        return data

    def fetch_movies(self, limit: int = 100) -> List[Dict[str, Any]]:
        params = {"limit": limit, "extended": "full"}
        if self.since_iso:
            params["start_at"] = self.since_iso
        data = self._fetch_endpoint("sync/history/movies", params)
        for item in data:
            item["_source_file"] = "trakt_api_movies.json"
        return data

    def extract(self) -> List[Dict[str, Any]]:
        episodes = self.fetch_episodes()
        movies = self.fetch_movies()
        return episodes + movies
