import logging
from typing import TYPE_CHECKING, Any, Dict, List
from domain.models.canonical_item import CanonicalMediaItem
from domain.models.outbox_state import ProviderOutboxState
from domain.services.simkl_payload_router import (
    AnimeSyncMode,
    SimklPayloadRouter,
)
from datetime import datetime, timezone

if TYPE_CHECKING:  # avoid application -> concrete infrastructure coupling at runtime
    from infrastructure.api_clients.nuvio_supabase import NuvioSupabaseAdapter

logger = logging.getLogger(__name__)


def _normalized_id_set(ids: Dict[str, Any]):
    """Type-normalized (str) id pairs for matching str-stored vs int-echoed ids."""
    return frozenset((k, str(v)) for k, v in ids.items())


def _entry_matches(entry: Dict[str, Any], echo: Dict[str, Any]) -> bool:
    entry_ids = _normalized_id_set(entry.get("ids", {}) or {})
    echo_ids = _normalized_id_set(echo.get("ids", {}) or {})
    if not entry_ids or not echo_ids:
        return False
    return bool(entry_ids & echo_ids)


def flush_outbox(
    items: List[CanonicalMediaItem],
    mal_adapter=None,
    simkl_adapter=None,
    nuvio_adapter: "NuvioSupabaseAdapter" = None,
    nuvio_profile_id: int = None,
    simkl_anime_mode: str = AnimeSyncMode.AUTO_NATIVE_PREFERRED.value,
) -> dict:
    """Flush pending outbox items to all enabled provider APIs.
    
    Returns a summary dict with counts of synced, errored, and skipped items per provider.
    """
    results = {
        "myanimelist": {"synced": 0, "errored": 0, "skipped": 0},
        "simkl": {"synced": 0, "errored": 0, "skipped": 0},
        "nuvio_sync": {"synced": 0, "errored": 0, "skipped": 0},
    }

    # MAL: sequential with 600ms rate delay
    if mal_adapter:
        for item in items:
            state = item.outbox.get("myanimelist")
            if not state or state.status != "pending":
                results["myanimelist"]["skipped"] += 1
                continue
            if not item.ids.mal:
                state.status = "unmatched"
                results["myanimelist"]["skipped"] += 1
                continue
            try:
                success = mal_adapter.update_anime_status(
                    mal_id=item.ids.mal,
                    status="completed",
                    num_watched_episodes=item.episode or 1
                )
                if success:
                    state.status = "synced"
                    state.last_synced_at = datetime.now(timezone.utc).isoformat()
                    results["myanimelist"]["synced"] += 1
                else:
                    state.status = "error"
                    state.retry_count += 1
                    results["myanimelist"]["errored"] += 1
            except Exception as e:
                state.status = "error"
                state.error_message = str(e)
                state.retry_count += 1
                results["myanimelist"]["errored"] += 1
                logger.error(f"MAL flush error for {item.title}: {e}")

    # Simkl: route each item onto the correct anime path, then batch.
    if simkl_adapter:
        router = SimklPayloadRouter(simkl_anime_mode)
        routed: Dict[str, List[dict]] = {"movies": [], "shows": [], "anime": []}
        correlation = []  # (entry, item) pairs, in send order
        for item in items:
            state = item.outbox.get("simkl")
            if not state or state.status != "pending":
                results["simkl"]["skipped"] += 1
                continue
            route = router.route(item)
            if route.path == "needs_identity":
                # Quarantine: never guess identity from a shared parent id.
                state.status = "unmatched"
                state.error_message = route.reason
                results["simkl"]["skipped"] += 1
                logger.info(f"Simkl quarantined '{item.title}': {route.reason}")
                continue
            routed[route.envelope].append(route.entry)
            correlation.append((route.entry, item))

        if correlation:
            try:
                result = simkl_adapter.sync_history(routed)
                # Attribute per-entry outcomes back to originating items by value
                # (not object identity): the adapter — or a future non-Python
                # one — may return reconstructed entries, so match on content.
                now = datetime.now(timezone.utc).isoformat()
                for entry, item in correlation:
                    state = item.outbox["simkl"]
                    failed_reason = next(
                        (err["reason"] for err in result.errors
                         if any(entry == fe for fe in err.get("entries", []))),
                        None,
                    )
                    if failed_reason is not None:
                        # Transport/HTTP failure: outcome uncertain, retryable.
                        state.status = "error"
                        state.retry_count += 1
                        state.error_message = failed_reason[:500]
                        results["simkl"]["errored"] += 1
                    elif any(_entry_matches(entry, echo) for echo in result.not_found):
                        # Simkl could not resolve this identity: permanent, not
                        # transient. Quarantine rather than mark as a retryable
                        # error so it is not resent every cycle.
                        state.status = "unmatched"
                        state.error_message = "Simkl reported not_found"
                        results["simkl"]["skipped"] += 1
                    else:
                        state.status = "synced"
                        state.last_synced_at = now
                        results["simkl"]["synced"] += 1
            except Exception as e:
                for _entry, item in correlation:
                    state = item.outbox["simkl"]
                    state.status = "error"
                    state.error_message = str(e)[:500]
                    state.retry_count += 1
                results["simkl"]["errored"] += len(correlation)
                logger.error(f"Simkl flush error: {e}")

    # Nuvio Supabase: batched RPC
    if nuvio_adapter and nuvio_profile_id:
        pending_nuvio = [item for item in items 
                         if item.outbox.get("nuvio_sync") and item.outbox["nuvio_sync"].status == "pending"]
        if pending_nuvio:
            payload = [{"title": item.title, "type": item.media_type, "watched_date": item.watched_date} for item in pending_nuvio]
            try:
                success = nuvio_adapter.push_watched_items(profile_id=nuvio_profile_id, items=payload)
                for item in pending_nuvio:
                    if success:
                        item.outbox["nuvio_sync"].status = "synced"
                        item.outbox["nuvio_sync"].last_synced_at = datetime.now(timezone.utc).isoformat()
                        results["nuvio_sync"]["synced"] += 1
                    else:
                        item.outbox["nuvio_sync"].status = "error"
                        item.outbox["nuvio_sync"].retry_count += 1
                        results["nuvio_sync"]["errored"] += 1
            except Exception as e:
                for item in pending_nuvio:
                    item.outbox["nuvio_sync"].status = "error"
                    item.outbox["nuvio_sync"].error_message = str(e)
                    item.outbox["nuvio_sync"].retry_count += 1
                results["nuvio_sync"]["errored"] += len(pending_nuvio)
                logger.error(f"Nuvio Supabase flush error: {e}")

    return results
