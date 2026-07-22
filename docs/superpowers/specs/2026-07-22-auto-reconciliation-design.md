# Smart Pre-Grouping & Multi-ID Auto-Reconciliation Design

## Goal
Drastically reduce manual reconciliation items (from 4,129 down to < 20 genuine collisions) by pre-grouping episode-level scrobbles at show normalization time and enabling smart single-ID auto-merging across Otaku Mappings.

---

## Proposed Changes

### 1. Show-Level Episode Pre-Grouping (`normalizer.py`)
- During Trakt JSON normalization (`normalize_all_sources`), group episode scrobbles sharing parent show IDs (`imdb`, `tmdb`, `tvdb`, `trakt`, `slug`) prior to canonical list generation.
- Aggregates episode lists (`episodes`), `watch_count`, and `last_watched_at` into a single canonical `MediaType.SHOW` item per show.

### 2. Single-ID Auto-Merging (`deduplicator.py`)
- If two media records share **any 1 valid external ID** (`imdb`, `tmdb`, `tvdb`, `mal`, `kitsu`, `anidb`, `simkl`, `trakt`), auto-merge them as long as titles don't hard-collide.
- Title normalization utilizes `OtakuMapper` cross-references to treat Japanese titles and English titles (e.g. *Boushoku no Berserk* vs *Berserk of Gluttony*) as matching.

### 3. Strict Collision Flagging (`deduplicator.py`)
- Flag items into `reconciliation_flagged.json` ONLY for:
  1. Shared ID with completely unrelated titles (e.g. *The Umbrella Academy* vs *Moby Dick*).
  2. Matching titles with conflicting release years (e.g. *Star Trek* 1966 vs *Star Trek* 2009).

---

## Verification Plan
1. Run `python3 main.py` and verify confirmed items = ~971 and flagged reconciliation items < 30.
2. Run `python3 -m unittest discover tests` to ensure 100% test suite pass.
