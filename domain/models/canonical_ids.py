from dataclasses import dataclass
from typing import Optional

@dataclass
class CanonicalIDs:
    trakt: Optional[str] = None
    slug: Optional[str] = None
    imdb: Optional[str] = None
    tmdb: Optional[str] = None
    tvdb: Optional[str] = None
    mal: Optional[str] = None
    kitsu: Optional[str] = None
    anidb: Optional[str] = None
    simkl: Optional[str] = None

    def merge(self, other: "CanonicalIDs") -> "CanonicalIDs":
        """Merge missing IDs from another CanonicalIDs instance without overwriting existing non-null IDs."""
        return CanonicalIDs(
            trakt=self.trakt or other.trakt,
            slug=self.slug or other.slug,
            imdb=self.imdb or other.imdb,
            tmdb=self.tmdb or other.tmdb,
            tvdb=self.tvdb or other.tvdb,
            mal=self.mal or other.mal,
            kitsu=self.kitsu or other.kitsu,
            anidb=self.anidb or other.anidb,
            simkl=self.simkl or other.simkl,
        )
