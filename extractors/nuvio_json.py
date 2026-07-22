import json
from pathlib import Path
from typing import List, Dict, Any, Union
from extractors.base import BaseExtractor


class NuvioJSONExtractor(BaseExtractor):
    def __init__(self, nuvio_file: Union[str, Path]):
        self.nuvio_file = Path(nuvio_file)

    def extract(self) -> List[Dict[str, Any]]:
        if not self.nuvio_file.exists() or not self.nuvio_file.is_file():
            return []
        try:
            with open(self.nuvio_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return [data]
                return []
        except Exception:
            return []
