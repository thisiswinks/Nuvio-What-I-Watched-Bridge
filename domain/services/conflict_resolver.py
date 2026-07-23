from domain.models.canonical_item import CanonicalMediaItem
from domain.models.conflict_policy import ConflictResolutionStrategy
import copy

def resolve_conflict(strategy: ConflictResolutionStrategy, item1: CanonicalMediaItem, item2: CanonicalMediaItem) -> CanonicalMediaItem:
    # Non-mutating base resolutions
    if strategy in (ConflictResolutionStrategy.PROMPT, ConflictResolutionStrategy.KEEP_SEPARATE, ConflictResolutionStrategy.DELETE, ConflictResolutionStrategy.SKIP):
        return item1
        
    # Mutating strategies operate on a copy to prevent side effects
    result_item = copy.deepcopy(item1)
    
    if strategy == ConflictResolutionStrategy.MERGE:
        # Merge missing IDs from item2 into item1
        result_item.ids = result_item.ids.merge(item2.ids)
        # Choose highest rating
        if item2.aggregated_rating is not None:
            if result_item.aggregated_rating is None or item2.aggregated_rating > result_item.aggregated_rating:
                result_item.aggregated_rating = item2.aggregated_rating
        return result_item
    elif strategy == ConflictResolutionStrategy.EDIT:
        # Return merged item with updated timestamp
        result_item.ids = result_item.ids.merge(item2.ids)
        return result_item
        
    return item1
