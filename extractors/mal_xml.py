import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Union
from extractors.base import BaseExtractor


class MALXMLExtractor(BaseExtractor):
    def __init__(self, xml_path: Union[str, Path]):
        self.xml_path = Path(xml_path)

    def extract(self) -> List[Dict[str, Any]]:
        if not self.xml_path.exists() or not self.xml_path.is_file():
            return []
        try:
            tree = ET.parse(self.xml_path)
            root = tree.getroot()
            items: List[Dict[str, Any]] = []
            for anime in root.findall("anime"):
                item: Dict[str, Any] = {}
                for child in anime:
                    item[child.tag] = child.text if child.text is not None else ""
                items.append(item)
            return items
        except Exception:
            return []
