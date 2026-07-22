import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Union
from models import CanonicalMediaItem, MediaType, MediaStatus


def export_mal_payload(
    items: List[CanonicalMediaItem], out_dir: Optional[Union[str, Path]] = None
) -> str:
    root = ET.Element("myanimelist")

    myinfo = ET.SubElement(root, "myinfo")
    ET.SubElement(myinfo, "user_id").text = "0"
    ET.SubElement(myinfo, "user_name").text = "ExportUser"
    ET.SubElement(myinfo, "user_export_type").text = "1"

    anime_count = 0

    for item in items:
        is_anime = (
            item.media_type == MediaType.ANIME
            or item.media_type == "anime"
            or (item.ids and item.ids.mal is not None)
        )
        if not is_anime:
            continue

        anime_count += 1
        anime_elem = ET.SubElement(root, "anime")

        mal_id = str(item.ids.mal) if item.ids and item.ids.mal else "0"
        ET.SubElement(anime_elem, "series_animedb_id").text = mal_id
        ET.SubElement(anime_elem, "series_title").text = item.title or ""
        ET.SubElement(anime_elem, "series_type").text = "TV"

        score_val = str(int(round(item.aggregated_rating))) if item.aggregated_rating else "0"
        ET.SubElement(anime_elem, "my_score").text = score_val

        status_map = {
            MediaStatus.COMPLETED: "Completed",
            MediaStatus.WATCHING: "Watching",
            MediaStatus.ON_HOLD: "On-Hold",
            MediaStatus.DROPPED: "Dropped",
            MediaStatus.PLAN_TO_WATCH: "Plan to Watch",
        }
        status_str = status_map.get(item.aggregated_status, "Completed")
        ET.SubElement(anime_elem, "my_status").text = status_str

    ET.SubElement(myinfo, "user_total_anime").text = str(anime_count)

    ET.indent(root, space="  ", level=0)
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8").decode("utf-8")

    if out_dir is not None:
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        with open(out_path / "mal_import.xml", "w", encoding="utf-8") as f:
            f.write(xml_str)

    return xml_str
