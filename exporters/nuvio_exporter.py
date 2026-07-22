import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict
from models import CanonicalMediaItem, MediaType, MediaStatus


def _parse_timestamp_ms(date_val: Optional[Any]) -> int:
    if not date_val:
        return int(time.time() * 1000)
    if isinstance(date_val, (int, float)):
        # If seconds instead of ms
        if date_val < 10000000000:
            return int(date_val * 1000)
        return int(date_val)
    if isinstance(date_val, str):
        try:
            dt = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
            return int(dt.timestamp() * 1000)
        except Exception:
            pass
        try:
            dt = datetime.strptime(date_val[:10], "%Y-%m-%d")
            return int(dt.timestamp() * 1000)
        except Exception:
            pass
    return int(time.time() * 1000)


def export_nuvio_payload(
    items: List[CanonicalMediaItem], out_dir: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    nuvio_custom_items = []
    p_items = []

    for item in items:
        raw_ids = asdict(item.ids)
        ids_dict = {k: v for k, v in raw_ids.items() if v is not None and v != ""}

        mtype_val = item.media_type.value if hasattr(item.media_type, "value") else str(item.media_type)
        status_val = item.aggregated_status.value if (item.aggregated_status and hasattr(item.aggregated_status, "value")) else str(item.aggregated_status)

        nuvio_custom_items.append({
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

        # Build p_items for Nuvio sync_push_watched_items RPC endpoint
        content_id = item.ids.imdb or (str(item.ids.tmdb) if item.ids.tmdb else None) or (str(item.ids.tvdb) if item.ids.tvdb else None) or (str(item.ids.trakt) if item.ids.trakt else None)
        if not content_id:
            content_id = item.title

        content_type = "series" if (item.media_type in (MediaType.SHOW, MediaType.ANIME) or mtype_val in ("show", "anime")) else "movie"

        # Determine watched timestamp
        last_watched = None
        for src in item.sources.values():
            if src.last_watched_at:
                last_watched = src.last_watched_at
                break
        watched_ts = _parse_timestamp_ms(last_watched)

        if content_type == "series":
            if item.episodes:
                for ep in item.episodes:
                    season_num = ep.get("season", 1) if isinstance(ep, dict) else 1
                    ep_num = ep.get("episode", 1) if isinstance(ep, dict) else 1
                    ep_watched = ep.get("watched_at") if isinstance(ep, dict) else last_watched
                    p_items.append({
                        "content_id": str(content_id),
                        "content_type": "series",
                        "title": item.title,
                        "season": season_num,
                        "episode": ep_num,
                        "watched_at": _parse_timestamp_ms(ep_watched),
                        "ids": ids_dict
                    })
            else:
                # Add show entry
                p_items.append({
                    "content_id": str(content_id),
                    "content_type": "series",
                    "title": item.title,
                    "season": 1,
                    "episode": 1,
                    "watched_at": watched_ts,
                    "ids": ids_dict
                })
        else:
            p_items.append({
                "content_id": str(content_id),
                "content_type": "movie",
                "title": item.title,
                "season": None,
                "episode": None,
                "watched_at": watched_ts,
                "ids": ids_dict
            })


    custom_payload = {
        "collection_name": "Media List Sync Collection",
        "version": "1.0",
        "total_items": len(nuvio_custom_items),
        "items": nuvio_custom_items
    }

    rpc_watched_payload = {
        "p_items": p_items,
        "p_profile_id": 1
    }

    if out_dir is not None:
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        with open(out_path / "nuvio_custom_collection.json", "w", encoding="utf-8") as f:
            json.dump(custom_payload, f, indent=2)
        with open(out_path / "nuvio_watched_sync.json", "w", encoding="utf-8") as f:
            json.dump(rpc_watched_payload, f, indent=2)

    return custom_payload

