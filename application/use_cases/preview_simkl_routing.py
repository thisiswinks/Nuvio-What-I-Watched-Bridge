"""Dry-run preview of how items would be routed to Simkl.

Runs the pure ``SimklPayloadRouter`` over a list of canonical items and returns
a per-item explanation (path, envelope, reason, payload) plus a summary. No
network calls and no credentials: this is the transparency/dry-run surface from
issue #3 (effective routing preview, per-item route explanation).
"""
from typing import Any, Dict, List

from domain.services.simkl_payload_router import AnimeSyncMode, SimklPayloadRouter


def preview_simkl_routing(
    items: List[Any],
    anime_mode: str = AnimeSyncMode.AUTO_NATIVE_PREFERRED.value,
) -> Dict[str, Any]:
    router = SimklPayloadRouter(anime_mode)
    routes: List[Dict[str, Any]] = []
    summary = {"native": 0, "hybrid": 0, "standard": 0, "needs_identity": 0}

    for item in items:
        route = router.route(item)
        summary[route.path] = summary.get(route.path, 0) + 1
        routes.append({
            "title": getattr(item, "title", ""),
            "media_type": str(getattr(getattr(item, "media_type", ""), "value",
                                    getattr(item, "media_type", ""))),
            "path": route.path,
            "envelope": route.envelope,
            "reason": route.reason,
            "entry": route.entry,
        })

    return {
        "anime_mode": AnimeSyncMode(anime_mode).value,
        "total": len(items),
        "summary": summary,
        "routes": routes,
    }
