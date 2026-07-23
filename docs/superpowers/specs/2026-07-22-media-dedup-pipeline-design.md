# Media List Extraction, Collation, Deduplication & Export Pipeline Design

**Date**: 2026-07-22  
**Target Services**: Simkl (API), Trakt (Local JSON export), MyAnimeList (Local XML export), Nuvio (Local JSON custom collection / sync bridge export)  
**Output Target**: Master JSON files (`movies.json`, `shows.json`, `anime.json`, `combined_full.json`), Reconciliation Reports, and Service-Native Re-import Payloads (Simkl, Trakt, MAL XML, Nuvio Custom Collection JSON).

---

## 1. Overview & Objective

Build a modular, easy-to-read Python pipeline to extract, unify, collate, deduplicate, and export media watch history, ratings, collections, and watchlists across four services:
1. **Simkl**: Fetched via API using OAuth PIN flow and cached locally.
2. **Trakt**: Read from local JSON export files (`data/import/trakt`).
3. **MyAnimeList (MAL)**: Read from local XML export (`data/import/mal_animelist.xml`).
4. **Nuvio**: Read from local JSON custom collection export (`data/import/nuvio_collection.json`).

The pipeline must:
- Preserve all external metadata identifiers (`imdb_id`, `tmdb_id`, `tvdb_id`, `mal_id`, `kitsu_id`, `anidb_id`, `simkl_id`, `trakt_id`, `nuvio_id`).
- Apply strict deduplication (requiring at least TWO matching IDs, or matching Title + Start/End Dates).
- Flag ambiguous/single-ID/date-mismatched records for manual reconciliation in `reconciliation_flagged.json` and `reconciliation.md`.
- Generate master combined JSON datasets and service-native import payloads (Simkl JSON, Trakt JSON, MAL XML, Nuvio Custom Collection JSON).
- Be modular, Gist-ready, and free of hardcoded sensitive credentials.

---

## 2. Directory & Module Architecture

```text
media_sync_pipeline/
├── .env.example              # Credentials & path config template (Gist safe)
├── .env                      # Local environment variables & secrets (gitignored)
├── config.py                 # Configuration loader & Simkl OAuth PIN auth helper
├── main.py                   # Main CLI execution entrypoint
├── models.py                 # Canonical Media Item data structures
├── extractors/
│   ├── base.py               # Abstract base extractor interface & local raw cacher
│   ├── simkl_api.py          # Simkl API client & raw file fetcher/cacher
│   ├── trakt_json.py         # Trakt export directory parser
│   ├── mal_xml.py            # MyAnimeList XML file parser
│   └── nuvio_json.py         # Nuvio collection/history JSON parser
├── normalizer.py             # Maps raw source objects to Canonical Media Items
├── deduplicator.py           # Multi-tier ID/Title/Date matching & merger logic
└── exporters/
    ├── master_exporter.py    # Master outputs: movies.json, shows.json, anime.json, combined_full.json
    ├── reconciliation.py     # Outputs reconciliation_flagged.json & reconciliation.md
    ├── simkl_exporter.py     # Formats Simkl API sync import payloads
    ├── trakt_exporter.py     # Formats Trakt API sync import payloads
    ├── mal_exporter.py       # Formats MyAnimeList XML import export
    └── nuvio_exporter.py     # Formats Nuvio custom collection JSON import payload
```

---

## 3. Data Flow & Processing Pipeline

1. **Configuration & Auth**:
   - `config.py` loads `SIMKL_CLIENT_ID`, `SIMKL_CLIENT_SECRET`, and local file paths from `.env`.
   - If `SIMKL_ACCESS_TOKEN` is missing, `config.py` launches an interactive terminal PIN flow (`https://simkl.com/oauth/authorize?response_type=code&client_id=...&redirect_uri=urn:ietf:wg:oauth:2.0:oob`), prompts user for PIN, exchanges PIN for access token, and saves it to `.env`.
2. **Extraction & Raw Caching**:
   - Downloads/fetches Simkl data via API (`/sync/all-items/`) and caches raw JSON in `data/raw/simkl/`. If raw cached files exist and `--refresh-api` is not set, reads from local disk.
   - Reads local Trakt JSON files from directory.
   - Reads local MAL XML file.
   - Reads local Nuvio custom collection JSON file.
3. **Normalization**:
   - Converts raw records to `CanonicalMediaItem` objects.
   - Preserves all external IDs (`imdb`, `tmdb`, `tvdb`, `mal`, `kitsu`, `anidb`, `simkl`, `trakt`, `nuvio`).
   - Normalizes ratings to 10-point scale and statuses to standard enum (`completed`, `watching`, `on_hold`, `plan_to_watch`, `dropped`).
4. **Strict Deduplication & Reconciliation**:
   - Groups items based on:
     - **Confirmed Duplicate**: Matches on >= 2 external IDs **OR** Title (normalized) + Start/End Dates match.
     - **Flagged for Reconciliation**: Matches on only 1 external ID with date/title conflicts, or Title matches with missing/conflicting Start/End dates.
     - **Unique Item**: No matching IDs or titles across other services.
   - Losslessly merges confirmed duplicates into single records containing all IDs, merged watch logs, ratings per service, and raw source payloads.
5. **Exporting**:
   - Exports master JSON datasets + markdown summary report.
   - Exports `reconciliation_flagged.json` and `reconciliation.md`.
   - Exports service-native import payloads (`exports/simkl_import.json`, `exports/trakt_import.json`, `exports/mal_import.xml`, `exports/nuvio_custom_collection.json`).

---

## 4. Canonical Data Model

```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "media_type": "movie | show | anime",
  "title": "Steins;Gate",
  "title_original": "シュタインズ・ゲート",
  "year": 2011,
  "start_date": "2011-04-06",
  "end_date": "2011-09-14",
  
  "ids": {
    "imdb": "tt1910272",
    "tmdb": "42206",
    "tvdb": "203491",
    "mal": "9253",
    "kitsu": "5953",
    "anidb": "7702",
    "simkl": 41530,
    "trakt": 33166,
    "nuvio": "collection-UGED6TEZ"
  },
  
  "aggregated_status": "completed",
  "aggregated_rating": 10.0,
  
  "sources": {
    "trakt": { "present": true, "status": "completed", "rating": 10, "watch_count": 1, "raw": {} },
    "simkl": { "present": true, "status": "completed", "rating": 10, "watch_count": 1, "raw": {} },
    "mal": { "present": true, "status": "Completed", "score": 10, "watched_episodes": 24, "raw": {} },
    "nuvio": { "present": true, "status": "watching", "catalog": "trakt.upnext", "raw": {} }
  },

  "episodes": [],
  "history_logs": []
}
```

---

## 5. Security & Public Gist Guidelines

1. **No Sensitive Data**: `.env` and `data/raw/` are included in `.gitignore`.
2. **Environment Variable Fallback**: All credentials load via `os.getenv()`.
3. **Public Template**: `.env.example` provided with placeholder values for `SIMKL_CLIENT_ID`, `SIMKL_CLIENT_SECRET`, and file paths.

---

## 6. Verification & Testing

- Unit/integration tests using standard `unittest` to verify:
  - Multi-ID matching logic (>=2 IDs match vs 1 ID match flagged).
  - Title + Start/End Date matching and date conflict flagging.
  - Trakt JSON parser, MAL XML parser, Nuvio JSON parser, and Simkl normalizers.
  - Export payload formatting validity (valid JSON/XML structure).
