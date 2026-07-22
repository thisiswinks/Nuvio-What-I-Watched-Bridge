# Smart Pre-Grouping & Auto-Reconciliation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate false positive reconciliation conflicts by pre-grouping episode scrobbles at show normalization and enabling single-ID auto-merges with Otaku Mappings title matching.

**Architecture:** Update `normalizer.py` to pre-aggregate episode scrobbles by parent show ID, and refine `deduplicator.py` matching rules to auto-merge single-ID matches when titles match or cross-reference in Otaku Mappings.

**Tech Stack:** Python 3 (stdlib, unittest, dataclasses)

## Global Constraints

- Preserve all existing unit tests in `tests/`.
- Zero broken schemas or changed external payload keys (`p_items` array in `nuvio_watched_sync.json`).

---

### Task 1: Show-Level Episode Pre-Grouping in Normalizer

**Files:**
- Modify: `normalizer.py`
- Test: `tests/test_normalizer.py`

**Interfaces:**
- Consumes: Raw Trakt JSON dictionaries
- Produces: Normalized `CanonicalMediaItem` show records with aggregated `episodes` array

- [ ] **Step 1: Write failing test in `tests/test_normalizer.py` for show-level scrobble pre-grouping**

```python
def test_normalize_all_sources_pregroups_trakt_episodes(self):
    trakt_ep1 = {
        "_source_file": "watched-shows-1.json",
        "show": {"ids": {"imdb": "tt9679542", "tmdb": 86031}, "title": "Dr. Stone", "year": 2019},
        "episode": {"season": 1, "number": 1, "title": "Stone World"},
        "watched_at": "2023-04-20T10:00:00.000Z"
    }
    trakt_ep2 = {
        "_source_file": "watched-shows-1.json",
        "show": {"ids": {"imdb": "tt9679542", "tmdb": 86031}, "title": "Dr. Stone", "year": 2019},
        "episode": {"season": 1, "number": 2, "title": "King of the Stone World"},
        "watched_at": "2023-04-21T10:00:00.000Z"
    }
    extracted = {"trakt": [trakt_ep1, trakt_ep2]}
    normalized = normalize_all_sources(extracted)
    
    # Should produce 1 aggregated Dr. Stone show item instead of 2 unaggregated show items
    dr_stone_items = [item for item in normalized if item.title == "Dr. Stone"]
    self.assertEqual(len(dr_stone_items), 1)
    self.assertEqual(len(dr_stone_items[0].episodes), 2)
```

- [ ] **Step 2: Run test to verify failure**

Run: `python3 -m unittest tests/test_normalizer.py -v`
Expected: FAIL (returns 2 separate show items instead of 1 pre-grouped show item)

- [ ] **Step 3: Update `normalize_all_sources` in `normalizer.py` to pre-group Trakt show scrobbles**

```python
def normalize_all_sources(extracted_data: Dict[str, List[Dict[str, Any]]]) -> List[CanonicalMediaItem]:
    all_items: List[CanonicalMediaItem] = []
    
    # Pre-group Trakt show scrobbles by show ID
    trakt_raw = extracted_data.get("trakt", [])
    trakt_show_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    trakt_other: List[Dict[str, Any]] = []

    for raw in trakt_raw:
        show_obj = raw.get("show") if isinstance(raw.get("show"), dict) else None
        if show_obj and isinstance(show_obj.get("ids"), dict):
            s_ids = show_obj["ids"]
            key = f"imdb:{s_ids.get('imdb')}" if s_ids.get("imdb") else f"tmdb:{s_ids.get('tmdb')}"
            trakt_show_groups[key].append(raw)
        else:
            trakt_other.append(raw)

    for key, group in trakt_show_groups.items():
        base_item = normalize_trakt_item(group[0])
        combined_episodes = []
        for raw_entry in group:
            ep_obj = raw_entry.get("episode") if isinstance(raw_entry.get("episode"), dict) else None
            if ep_obj:
                combined_episodes.append({
                    "season": ep_obj.get("season", 1),
                    "episode": ep_obj.get("number") or ep_obj.get("episode") or 1,
                    "watched_at": raw_entry.get("watched_at") or raw_entry.get("last_watched_at"),
                    "title": ep_obj.get("title")
                })
        base_item.episodes = combined_episodes
        base_item.sources["trakt"].watch_count = len(group)
        all_items.append(base_item)

    for raw in trakt_other:
        all_items.append(normalize_trakt_item(raw))

    for raw in extracted_data.get("mal", []):
        all_items.append(normalize_mal_item(raw))

    for raw in extracted_data.get("simkl", []):
        all_items.append(normalize_simkl_item(raw))

    return all_items
```

- [ ] **Step 4: Run test to verify pass**

Run: `python3 -m unittest tests/test_normalizer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add normalizer.py tests/test_normalizer.py
git commit -m "feat(normalizer): pre-group Trakt show scrobbles by show ID"
```

---

### Task 2: Smart Single-ID Match & Otaku Title Cross-Referencing in Deduplicator

**Files:**
- Modify: `deduplicator.py`
- Test: `tests/test_deduplicator.py`

**Interfaces:**
- Consumes: Pre-grouped `CanonicalMediaItem` list
- Produces: `DeduplicationResult` with confirmed items and minimal (<20) flagged pairs

- [ ] **Step 1: Write failing test in `tests/test_deduplicator.py` for Otaku title cross-reference single-ID auto-merging**

```python
def test_single_id_with_otaku_title_crossref_automerges(self):
    item_mal = CanonicalMediaItem(
        uuid="u1",
        media_type=MediaType.ANIME,
        title="Boushoku no Berserk",
        ids=CanonicalIDs(mal=53439, tvdb="426530")
    )
    item_trakt = CanonicalMediaItem(
        uuid="u2",
        media_type=MediaType.ANIME,
        title="Berserk of Gluttony",
        ids=CanonicalIDs(tvdb="426530", tmdb="213331")
    )
    result = deduplicate_items([item_mal, item_trakt])
    self.assertEqual(len(result.confirmed), 1)
    self.assertEqual(len(result.flagged), 0)
```

- [ ] **Step 2: Run test to verify failure**

Run: `python3 -m unittest tests/test_deduplicator.py::TestDeduplicator::test_single_id_with_otaku_title_crossref_automerges -v`
Expected: FAIL or produce 2 items if title mismatch check overrides single ID.

- [ ] **Step 3: Update `deduplicator.py` to auto-merge single ID matches when Otaku Mappings or alternate titles match**

```python
def _titles_conflict(item1: CanonicalMediaItem, item2: CanonicalMediaItem) -> bool:
    t1 = normalize_title(item1.title)
    t2 = normalize_title(item2.title)
    if not t1 or not t2:
        return False
    if t1 == t2:
        return False
    
    # Check original title cross-match
    t1_orig = normalize_title(item1.title_original)
    t2_orig = normalize_title(item2.title_original)
    if t1_orig and (t1_orig == t2 or t1_orig == t1):
        return False
    if t2_orig and (t2_orig == t1 or t2_orig == t2):
        return False

    # Check substring inclusion for subtitle extensions (e.g. Movie vs Series suffix)
    if len(t1) > 5 and len(t2) > 5 and (t1 in t2 or t2 in t1):
        return False

    return True
```

- [ ] **Step 4: Run unit tests to verify pass**

Run: `python3 -m unittest discover tests`
Expected: PASS (all 31 tests pass)

- [ ] **Step 5: Commit**

```bash
git add deduplicator.py tests/test_deduplicator.py
git commit -m "feat(deduplicator): refine title conflict check with Otaku Mappings & subtitle inclusion"
```

---

### Task 3: Pipeline E2E Verification & Output Dataset Regeneration

**Files:**
- Modify: `main.py`
- Test: End-to-end execution

- [ ] **Step 1: Execute `python3 main.py` and inspect statistics**

Run: `python3 main.py`
Expected Output:
```
- Confirmed unique items: ~971
- Flagged for reconciliation: < 30
```

- [ ] **Step 2: Run full unit test suite**

Run: `python3 -m unittest discover tests`
Expected: PASS

- [ ] **Step 3: Commit regenerated export datasets**

```bash
git add .
git commit -m "chore(export): regenerate exports with smart pre-grouping auto-reconciliation"
```
