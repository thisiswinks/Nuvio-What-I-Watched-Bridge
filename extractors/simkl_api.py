import json
import urllib.request
from pathlib import Path
from typing import Any, Union, Optional
from extractors.base import BaseExtractor


class SimklAPIExtractor(BaseExtractor):
    def __init__(
        self,
        client_id: str = "",
        access_token: Optional[str] = None,
        raw_cache_dir: Union[str, Path] = Path("data/raw"),
    ):
        self.client_id = client_id
        self.access_token = access_token
        self.raw_cache_dir = Path(raw_cache_dir)

    def extract(self) -> Any:
        cache_file = self.raw_cache_dir / "simkl" / "all_items.json"
        if cache_file.exists() and cache_file.is_file():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        if not self.client_id or not self.access_token:
            return []

        req = urllib.request.Request("https://api.simkl.com/sync/all-items/")
        req.add_header("simkl-client-id", self.client_id)
        req.add_header("Authorization", f"Bearer {self.access_token}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                return data
        except Exception:
            return []
