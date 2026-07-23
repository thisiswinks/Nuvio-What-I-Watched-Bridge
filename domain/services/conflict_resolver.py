from domain.models.canonical_item import CanonicalMediaItem
from domain.models.conflict_policy import ConflictResolutionStrategy

def resolve_conflict(strategy: ConflictResolutionStrategy, item1: CanonicalMediaItem, item2: CanonicalMediaItem) -> CanonicalMediaItem:
    if strategy == ConflictResolutionStrategy.MERGE:
        # Merge missing IDs from item2 into item1
        item1.ids = item1.ids.merge(item2.ids)
        # Choose highest rating
        if item2.aggregated_rating is not None:
            if item1.aggregated_rating is None or item2.aggregated_rating > item1.aggregated_rating:
                item1.aggregated_rating = item2.aggregated_rating
        return item1
    elif strategy == ConflictResolutionStrategy.SKIP:
        return item1
    elif strategy == ConflictResolutionStrategy.EDIT:
        # Return merged item with updated timestamp
        item1.ids = item1.ids.merge(item2.ids)
        return item1
    return item1
