import json
from pathlib import Path
from typing import List, Dict, Any, Union
from extractors.base import BaseExtractor


class TraktJSONExtractor(BaseExtractor):
    def __init__(self, trakt_dir: Union[str, Path]):
        self.trakt_dir = Path(trakt_dir)

    def extract(self) -> List[Dict[str, Any]]:
        if not self.trakt_dir.exists() or not self.trakt_dir.is_dir():
            return []
        results: List[Dict[str, Any]] = []
        for json_file in sorted(self.trakt_dir.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for entry in data:
                            if isinstance(entry, dict):
                                entry["_source_file"] = json_file.name
                                results.append(entry)
                    elif isinstance(data, dict):
                        data["_source_file"] = json_file.name
                        results.append(data)
            except Exception:
                continue
        return results
