# ADR 0001: Provider sync runtime lives in NuvioTV; this repo is the contract home

- Status: Accepted
- Date: 2026-07-23
- Context: [Issue #3](https://github.com/thisiswinks/Nuvio-What-I-Watched-Bridge/issues/3)

## Decision

The production tracking-provider runtime (event capture, credential storage,
durable queues, provider API calls) belongs in **NuvioTV** using its existing
Kotlin, Hilt, Retrofit, Moshi, DataStore, and Room patterns.

This repository remains the:

- architecture reference for the provider sync design,
- home of anime mapping fixtures and Otaku-Mappings integration,
- migration/backfill tooling,
- **contract test-vector home** — machine-readable payload vectors any
  implementation (Kotlin first) verifies against.

The current JavaScript bundle (`providers/otaku_sync_plugin.js`) is a catalog
surface, not a background tracking-provider API, and does not gate production
sync. The Python pipeline is spec-by-executable-example, not the production path.

## Simkl anime contract (the portable asset)

Routing decisions live in `domain/services/simkl_payload_router.py` (pure, no
I/O) and are frozen as golden vectors in
`tests/fixtures/simkl_contract_vectors.json`. Two paths, per the
[Simkl anime guide](https://api.simkl.org/guides/anime) (guide as published
2026-07):

- **Path A (hybrid):** [TMDB/TVDB primary](https://api.simkl.org/guides/anime#path-a-tmdb-or-tvdb-primary-integration).
  `shows[]` envelope, `use_tvdb_anime_seasons: true`, TVDB season/episode
  coordinates. Simkl resolves per-cour splits and absolute numbering.
- **Path B (native):** [anime-native](https://api.simkl.org/guides/anime#path-b-anime-native-integration).
  `anime[]` envelope, native ids (MAL/AniList/AniDB/Kitsu), flat absolute
  episode numbers, no season key.

Rules that protect user history:

- **Never derive a cour-specific Simkl identity from a shared parent id.** A bare
  TMDB/TVDB franchise id without coordinates quarantines as `needs_identity`.
- **Native path requires absolute-episode provenance** (source-provided or
  Otaku-Mappings offset). A native-id anime carrying only S/E coordinates falls
  back to Path A so Simkl does the mapping; it is never locally converted.
- **No episode-less series history writes** — they would mark an entire show
  watched. Only movies may post without episode coordinates.

## Alternatives considered

- **Implement directly in Kotlin, this repo holds only vectors.** Rejected for
  now: the Python pipeline already encodes normalization/enrichment logic worth
  exercising as an executable spec. Revisit once the Kotlin port begins.
- **Provider-generic router.** Trakt has the same split-cour identity problem;
  a shared abstraction is attractive but deferred to avoid speculative
  generality. The router is intentionally Simkl-specific until a second
  consumer exists.
- **Resolve identity via Simkl search before writing** instead of quarantining.
  Rejected: quarantine-over-guess is the safer default; a live resolution step
  is a future enhancement.

## Consequences

- Retry/transport specifics in the Python adapter are a behavioral reference,
  not the shipping implementation; the Kotlin port re-derives transport from
  the vectors and this ADR.
- The defensible asset is Nuvio event capture plus mapping correctness, not
  payload formatting; a first-party Simkl importer or a Kodi/Jellyfin scrobbler
  adopting the guide would erode everything except Nuvio-specific capture.
- Live-API validation against a real Simkl account is deliberately out of scope
  for automated runs (writes touch real user history). See `TODOS.md`.
