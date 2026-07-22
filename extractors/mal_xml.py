import gzip
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Union
from extractors.base import BaseExtractor


class MALXMLExtractor(BaseExtractor):
    def __init__(self, xml_path: Union[str, Path]):
        self.xml_path = Path(xml_path)

    def extract(self) -> List[Dict[str, Any]]:
        if not self.xml_path.exists():
            return []

        xml_content = None

        try:
            if self.xml_path.suffix.lower() == ".gz":
                with gzip.open(self.xml_path, "rb") as f:
                    xml_content = f.read()
            elif self.xml_path.suffix.lower() == ".zip":
                with zipfile.ZipFile(self.xml_path, "r") as zf:
                    for name in zf.namelist():
                        if name.endswith(".xml") and not name.startswith("__MACOSX"):
                            xml_content = zf.read(name)
                            break
            else:
                with open(self.xml_path, "rb") as f:
                    xml_content = f.read()
        except Exception:
            return []

        if not xml_content:
            return []

        try:
            root = ET.fromstring(xml_content)
            items = []
            for anime in root.findall("anime"):
                item = {}
                for child in anime:
                    item[child.tag] = child.text
                items.append(item)
            return items
        except Exception:
            return []
