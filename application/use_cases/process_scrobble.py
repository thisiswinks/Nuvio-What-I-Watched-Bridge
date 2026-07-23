from domain.models.canonical_item import CanonicalMediaItem
from domain.models.conflict_policy import ConflictResolutionStrategy
from domain.services.otaku_enrichment import enrich_canonical_item
from typing import Optional, Any

def process_scrobble(
    title: str,
    media_type: str,
    season: Optional[int],
    episode: Optional[int],
    watched_date: str,
    ids: dict,
    scrobble_threshold_percent: int = 85,
    progress_percent: int = 100,
    otaku_mapper: Optional[Any] = None
) -> Optional[CanonicalMediaItem]:
    """Process a scrobble event from Nuvio TV into a CanonicalMediaItem.
    
    Only marks the item as 'watched' if progress_percent >= scrobble_threshold_percent.
    Always enriches via Otaku-Mappings if a mapper is provided.
    """
    from domain.models.canonical_ids import CanonicalIDs

    if progress_percent < scrobble_threshold_percent:
        return None  # Below threshold, not ready to scrobble

    canonical_ids = CanonicalIDs(
        trakt=ids.get("trakt"),
        imdb=ids.get("imdb"),
        tmdb=ids.get("tmdb"),
        tvdb=ids.get("tvdb"),
        mal=ids.get("mal"),
        anilist=ids.get("anilist"),
        kitsu=ids.get("kitsu"),
        anidb=ids.get("anidb"),
        simkl=ids.get("simkl"),
        slug=ids.get("slug"),
    )

    item = CanonicalMediaItem(
        title=title,
        media_type=media_type,
        season=season,
        episode=episode,
        watched_date=watched_date,
        ids=canonical_ids,
    )

    # Selectively enrich with Otaku-Mappings (preserves existing IDs)
    item = enrich_canonical_item(item, otaku_mapper=otaku_mapper)

    return item
