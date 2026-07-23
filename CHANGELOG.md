# Changelog

All notable changes to What I Watched Sync are recorded here.

## [1.1.0] - 2026-07-23

### Added
- Simkl anime Path A/Path B payload routing per the
  [official anime guide](https://api.simkl.org/guides/anime): a pure domain
  router (`domain/services/simkl_payload_router.py`) chooses Path B
  (anime-native ids, flat absolute episodes) or Path A (TMDB/TVDB coordinates
  with `use_tvdb_anime_seasons`) by configurable `anime_mode`.
- `POST /sync/history` adapter (`infrastructure/api_clients/simkl.py`) with
  structured `added`/`not_found` parsing, per-entry error attribution, and
  429-only bounded `Retry-After` retries.
- Golden contract vectors (`tests/fixtures/simkl_contract_vectors.json`) as the
  portable spec for the NuvioTV Kotlin port; ADR 0001 records the runtime split.
- `main.py --simkl-dry-run`: routes items and writes `simkl_routing_preview.json`
  with a per-item route explanation, no network calls (issue #3 dry-run surface).
- `providers.simkl.anime_mode` in `config.yaml` (`SIMKL_ANIME_MODE` override).
- `anilist` external id, populated from Otaku-Mappings.

### Changed
- Anime library exports carry only native + simkl ids, so a shared TMDB/TVDB
  parent can never identify a specific cour.
- Corrected prototype claims across README, AGENTS, KCS, and the install guide;
  removed AI-slop patterns and emoji from documentation surfaces.

### Fixed
- Simkl history writes go to `/sync/history` (was the wrong `/sync/add-to-history`).
- `not_found` items quarantine as `unmatched` instead of being retried forever.
- Error attribution matches failed entries by value, not object identity, so a
  failed write can never be recorded as synced.

### Security
- Removed personal data (a secondary account handle, home-directory export
  paths) from tracked files; gitignored exported watch history (`data/export/`).
