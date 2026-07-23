from dataclasses import dataclass, field
from typing import Optional, Dict
from .canonical_ids import CanonicalIDs
from .outbox_state import ProviderOutboxState

@dataclass
class CanonicalMediaItem:
    title: str
    media_type: str = "anime"  # anime, movie, series
    year: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    absolute_episode: Optional[int] = None
    watched_date: Optional[str] = None
    aggregated_rating: Optional[float] = None
    is_anime: bool = False
    ids: CanonicalIDs = field(default_factory=CanonicalIDs)
    outbox: Dict[str, ProviderOutboxState] = field(default_factory=lambda: {
        "trakt": ProviderOutboxState(),
        "myanimelist": ProviderOutboxState(),
        "simkl": ProviderOutboxState(),
        "nuvio_sync": ProviderOutboxState()
    })
