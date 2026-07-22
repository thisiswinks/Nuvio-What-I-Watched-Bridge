import json
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Union
from extractors.base import BaseExtractor


class TraktJSONExtractor(BaseExtractor):
    def __init__(self, trakt_path: Union[str, Path]):
        self.trakt_path = Path(trakt_path)

    def extract(self) -> List[Dict[str, Any]]:
        if not self.trakt_path.exists():
            return []

        results: List[Dict[str, Any]] = []

        # 1. If passed a zip file directly
        if self.trakt_path.is_file() and self.trakt_path.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(self.trakt_path, "r") as zf:
                    for name in sorted(zf.namelist()):
                        if name.endswith(".json") and not name.startswith("__MACOSX"):
                            try:
                                with zf.open(name) as f:
                                    data = json.load(f)
                                    filename = Path(name).name
                                    if isinstance(data, list):
                                        for entry in data:
                                            if isinstance(entry, dict):
                                                entry["_source_file"] = filename
                                                results.append(entry)
                                    elif isinstance(data, dict):
                                        data["_source_file"] = filename
                                        results.append(data)
                            except Exception:
                                continue
            except Exception:
                pass
            return results

        # 2. If passed a directory
        if self.trakt_path.is_dir():
            for json_file in sorted(self.trakt_path.glob("*.json")):
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

        return results
