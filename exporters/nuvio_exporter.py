import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict
from models import CanonicalMediaItem


def export_nuvio_payload(
    items: List[CanonicalMediaItem], out_dir: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    nuvio_items = []
    for item in items:
        raw_ids = asdict(item.ids)
        ids_dict = {k: v for k, v in raw_ids.items() if v is not None and v != ""}

        mtype_val = item.media_type.value if hasattr(item.media_type, "value") else str(item.media_type)
        status_val = item.aggregated_status.value if (item.aggregated_status and hasattr(item.aggregated_status, "value")) else str(item.aggregated_status)

        nuvio_items.append({
            "uuid": item.uuid,
            "title": item.title,
            "media_type": mtype_val,
            "year": item.year,
            "start_date": item.start_date,
            "end_date": item.end_date,
            "ids": ids_dict,
            "status": status_val,
            "rating": item.aggregated_rating,
            "sources": list(item.sources.keys())
        })

    payload = {
        "collection_name": "Media List Sync Collection",
        "version": "1.0",
        "total_items": len(nuvio_items),
        "items": nuvio_items
    }

    if out_dir is not None:
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        with open(out_path / "nuvio_custom_collection.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    return payload
