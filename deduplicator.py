from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
import re
from collections import defaultdict
from models import (
    CanonicalMediaItem,
    CanonicalIDs,
    SourceRecord,
    MediaStatus,
)


@dataclass
class DeduplicationResult:
    confirmed: List[CanonicalMediaItem] = field(default_factory=list)
    flagged: List[Dict[str, Any]] = field(default_factory=list)


def normalize_title(title: Optional[str]) -> str:
    if not title:
        return ""
    cleaned = re.sub(r"[^\w\s]", "", title.lower())
    cleaned = re.sub(r"\s+", "", cleaned).strip()
    return cleaned


def _extract_year(item: CanonicalMediaItem) -> Optional[int]:
    if item.year is not None:
        return item.year
    if item.start_date and isinstance(item.start_date, str) and len(item.start_date) >= 4:
        try:
            return int(item.start_date[:4])
        except ValueError:
            pass
    return None


def _dates_match(item1: CanonicalMediaItem, item2: CanonicalMediaItem) -> bool:
    if _dates_conflict(item1, item2):
        return False

    if item1.start_date and item2.start_date and item1.start_date == item2.start_date:
        return True

    y1 = _extract_year(item1)
    y2 = _extract_year(item2)
    if y1 is not None and y2 is not None and y1 == y2:
        return True

    return False


def _dates_conflict(item1: CanonicalMediaItem, item2: CanonicalMediaItem) -> bool:
    y1 = _extract_year(item1)
    y2 = _extract_year(item2)
    if y1 is not None and y2 is not None and y1 != y2:
        return True
    if item1.start_date and item2.start_date and item1.start_date != item2.start_date:
        return True
    if item1.end_date and item2.end_date and item1.end_date != item2.end_date:
        return True
    return False


def _dates_missing(item1: CanonicalMediaItem, item2: CanonicalMediaItem) -> bool:
    y1 = _extract_year(item1)
    y2 = _extract_year(item2)
    has_date1 = y1 is not None or bool(item1.start_date)
    has_date2 = y2 is not None or bool(item2.start_date)
    return not (has_date1 and has_date2)


def _titles_match(item1: CanonicalMediaItem, item2: CanonicalMediaItem) -> bool:
    t1 = normalize_title(item1.title)
    t2 = normalize_title(item2.title)
    if t1 and t2 and t1 == t2:
        return True
    t1_orig = normalize_title(item1.title_original)
    t2_orig = normalize_title(item2.title_original)
    if t1_orig and t2_orig and t1_orig == t2_orig:
        return True
    return False


def _titles_conflict(item1: CanonicalMediaItem, item2: CanonicalMediaItem) -> bool:
    t1 = normalize_title(item1.title)
    t2 = normalize_title(item2.title)
    if t1 and t2 and t1 != t2:
        return True
    return False


def merge_items(
    item1: CanonicalMediaItem, item2: CanonicalMediaItem
) -> CanonicalMediaItem:
    merged_ids = item1.ids.merge(item2.ids)

    merged_sources: Dict[str, SourceRecord] = dict(item1.sources)
    for k, v in item2.sources.items():
        if k not in merged_sources:
            merged_sources[k] = v
        else:
            s1 = merged_sources[k]
            s2 = v
            merged_sources[k] = SourceRecord(
                source_name=k,
                present=s1.present or s2.present,
                status=s1.status or s2.status,
                rating=s1.rating if s1.rating is not None else s2.rating,
                watch_count=max(s1.watch_count, s2.watch_count),
                last_watched_at=s1.last_watched_at or s2.last_watched_at,
                raw={**s1.raw, **s2.raw},
            )

    combined_logs = list(item1.history_logs) + list(item2.history_logs)
    unique_logs = []
    for log in combined_logs:
        if log not in unique_logs:
            unique_logs.append(log)

    combined_episodes = list(item1.episodes) + list(item2.episodes)
    unique_episodes = []
    for ep in combined_episodes:
        if ep not in unique_episodes:
            unique_episodes.append(ep)

    ratings = [
        src.rating for src in merged_sources.values() if src.rating is not None
    ]
    if ratings:
        avg_rating = round(sum(ratings) / len(ratings), 2)
    else:
        agg_ratings = [
            r
            for r in [item1.aggregated_rating, item2.aggregated_rating]
            if r is not None
        ]
        avg_rating = (
            round(sum(agg_ratings) / len(agg_ratings), 2)
            if agg_ratings
            else None
        )

    status = item1.aggregated_status or item2.aggregated_status
    if (
        item1.aggregated_status == MediaStatus.COMPLETED
        or item2.aggregated_status == MediaStatus.COMPLETED
    ):
        status = MediaStatus.COMPLETED

    title = item1.title or item2.title
    title_orig = item1.title_original or item2.title_original
    year = item1.year if item1.year is not None else item2.year
    start_date = item1.start_date or item2.start_date
    end_date = item1.end_date or item2.end_date

    return CanonicalMediaItem(
        uuid=item1.uuid,
        media_type=item1.media_type or item2.media_type,
        title=title,
        title_original=title_orig,
        year=year,
        start_date=start_date,
        end_date=end_date,
        ids=merged_ids,
        aggregated_status=status,
        aggregated_rating=avg_rating,
        sources=merged_sources,
        episodes=unique_episodes,
        history_logs=unique_logs,
    )


class DisjointSet:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: int, j: int):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_i] = root_j


def deduplicate_items(items: List[CanonicalMediaItem]) -> DeduplicationResult:
    if not items:
        return DeduplicationResult()

    n = len(items)
    ds = DisjointSet(n)
    flagged: List[Dict[str, Any]] = []
    flagged_pairs: Set[tuple] = set()

    # 1. Build candidate buckets to avoid O(N^2) comparison
    buckets: Dict[str, List[int]] = defaultdict(list)
    for idx, item in enumerate(items):
        t_norm = normalize_title(item.title)
        if t_norm:
            buckets[f"t:{t_norm}"].append(idx)
        
        ids = item.ids
        for field in ["imdb", "tmdb", "tvdb", "mal", "kitsu", "anidb", "simkl", "trakt", "nuvio"]:
            val = getattr(ids, field)
            if val is not None and str(val):
                buckets[f"{field}:{val}"].append(idx)

    # 2. Check candidate pairs in buckets
    candidate_pairs: Set[tuple] = set()
    for b_items in buckets.values():
        if len(b_items) > 1:
            for i_idx in range(len(b_items)):
                for j_idx in range(i_idx + 1, len(b_items)):
                    idx1, idx2 = b_items[i_idx], b_items[j_idx]
                    if idx1 != idx2:
                        candidate_pairs.add((min(idx1, idx2), max(idx1, idx2)))

    for idx1, idx2 in candidate_pairs:
        item1 = items[idx1]
        item2 = items[idx2]

        matching_ids = item1.ids.matching_id_count(item2.ids)
        is_multi_id_match = matching_ids >= 2
        is_title_date_match = _titles_match(item1, item2) and _dates_match(item1, item2)

        if is_multi_id_match or is_title_date_match:
            ds.union(idx1, idx2)
        else:
            pair_key = (min(item1.uuid, item2.uuid), max(item1.uuid, item2.uuid))
            if pair_key not in flagged_pairs:
                if matching_ids == 1 and (
                    _titles_conflict(item1, item2)
                    or _dates_conflict(item1, item2)
                    or _dates_missing(item1, item2)
                ):
                    flagged.append({
                        "reason": "1 matching external ID with conflicting dates/titles",
                        "item1": item1,
                        "item2": item2,
                        "item1_title": item1.title,
                        "item2_title": item2.title,
                        "matching_ids": 1,
                    })
                    flagged_pairs.add(pair_key)
                elif _titles_match(item1, item2) and (
                    _dates_conflict(item1, item2)
                    or _dates_missing(item1, item2)
                ):
                    flagged.append({
                        "reason": "Title match with missing or conflicting start/end dates",
                        "item1": item1,
                        "item2": item2,
                        "item1_title": item1.title,
                        "item2_title": item2.title,
                    })
                    flagged_pairs.add(pair_key)

    # 3. Merge components
    groups: Dict[int, List[CanonicalMediaItem]] = defaultdict(list)
    for idx, item in enumerate(items):
        root = ds.find(idx)
        groups[root].append(item)

    confirmed: List[CanonicalMediaItem] = []
    for grp in groups.values():
        merged = grp[0]
        for next_item in grp[1:]:
            merged = merge_items(merged, next_item)
        confirmed.append(merged)

    return DeduplicationResult(confirmed=confirmed, flagged=flagged)
