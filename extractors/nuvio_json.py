import json
from pathlib import Path
from typing import List, Dict, Any, Union
from extractors.base import BaseExtractor


class NuvioJSONExtractor(BaseExtractor):
    def __init__(self, nuvio_file: Union[str, Path]):
        self.nuvio_file = Path(nuvio_file)

    def _extract_items_recursive(self, node: Any, results: List[Dict[str, Any]]) -> None:
        if isinstance(node, dict):
            if any(k in node for k in ("tmdbId", "imdbId", "tvdbId", "catalogId", "mediaType", "addonId")):
                results.append(node)
            for v in node.values():
                self._extract_items_recursive(v, results)
        elif isinstance(node, list):
            for elem in node:
                self._extract_items_recursive(elem, results)

    def extract(self) -> List[Dict[str, Any]]:
        if not self.nuvio_file.exists() or not self.nuvio_file.is_file():
            return []
        try:
            with open(self.nuvio_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                results: List[Dict[str, Any]] = []
                self._extract_items_recursive(data, results)
                return results
        except Exception:
            return []
