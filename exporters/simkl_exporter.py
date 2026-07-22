import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict
from models import CanonicalMediaItem, MediaType


def export_simkl_payload(
    items: List[CanonicalMediaItem], out_dir: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    payload: Dict[str, List[Dict[str, Any]]] = {
        "movies": [],
        "shows": [],
        "anime": []
    }

    for item in items:
        raw_ids = asdict(item.ids)
        ids_dict = {k: v for k, v in raw_ids.items() if v is not None and v != ""}

        entry: Dict[str, Any] = {}
        if item.title:
            entry["title"] = item.title
        if item.year:
            entry["year"] = item.year
        if ids_dict:
            entry["ids"] = ids_dict
        if item.aggregated_rating is not None:
            entry["rating"] = item.aggregated_rating

        mtype = item.media_type
        if mtype == MediaType.MOVIE or mtype == "movie":
            payload["movies"].append(entry)
        elif mtype == MediaType.SHOW or mtype == "show":
            payload["shows"].append(entry)
        elif mtype == MediaType.ANIME or mtype == "anime":
            payload["anime"].append(entry)

    if out_dir is not None:
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        with open(out_path / "simkl_import.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    return payload
