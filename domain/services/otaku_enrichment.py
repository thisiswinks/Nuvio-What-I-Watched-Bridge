from domain.models.canonical_item import CanonicalMediaItem
from typing import Any, Optional

def enrich_canonical_item(item: CanonicalMediaItem, otaku_mapper: Optional[Any] = None) -> CanonicalMediaItem:
    """Selective enrichment: preserves existing valid IDs while adding missing cross-database IDs."""
    if not otaku_mapper:
        return item
    match = otaku_mapper.lookup(item.ids, item.title)
    if match:
        # Preserve existing IDs, add missing IDs ONLY
        if not item.ids.mal and match.get("mal_id"):
            item.ids.mal = str(match["mal_id"])
        if not item.ids.simkl and match.get("simkl_id"):
            item.ids.simkl = str(match["simkl_id"])
        if not item.ids.kitsu and match.get("kitsu_id"):
            item.ids.kitsu = str(match["kitsu_id"])
        if not item.ids.anidb and match.get("anidb_id"):
            item.ids.anidb = str(match["anidb_id"])
        
        # Calculate absolute episode if season/episode offset present
        offset = match.get("episode_offset", 0)
        if item.episode is not None:
            item.absolute_episode = item.episode + offset
        item.is_anime = True
    return item
