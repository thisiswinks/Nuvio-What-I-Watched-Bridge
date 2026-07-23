# Simkl Anime Path A / Path B Payload Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the bridge's Simkl provider integration into full compliance with the [Simkl anime guide](https://api.simkl.org/guides/anime): route each anime item to either Path B (anime-native `anime[]` envelope with flat absolute episodes) or Path A (TVDB-hybrid `shows[]` envelope with `use_tvdb_anime_seasons: true` and TVDB season coordinates), with a configurable `anime_mode`, the correct `POST /sync/history` contract, structured `added`/`not_found` result handling, bounded `Retry-After`-aware retries, and quarantine (never guessing) for unresolved identity. Also delivers Phase 0 of [issue #1](https://github.com/thisiswinks/Nuvio-What-I-Watched-Bridge/issues/1): correct prototype claims and record the architecture decision.

**Architecture:** DDD. Routing decisions are pure domain logic (`domain/services/`); HTTP transport stays in the adapter (`exporters/simkl_sync.py`); orchestration in `application/use_cases/flush_outbox.py`. All new behavior is configured via `config.yaml`, nothing hidden.

**Why (from issue #1 provider requirements):**
- Current `SimklSyncAdapter` posts everything under a `shows[]` envelope to `/sync/add-to-history` with ID-only entries, no `use_tvdb_anime_seasons`, no `anime[]` envelope, no episode coordinates, boolean-only results. Anime writes therefore mis-route or silently drop split-cour titles.
- `flush_outbox` requires `item.ids.simkl` for Simkl sync, which tempts deriving a cour-specific Simkl ID from a shared TMDB/TVDB parent — explicitly forbidden. Path A/B payloads let Simkl resolve identity itself.

---

### Task 1: Domain — AnimeSyncMode + SimklPayloadRouter (TDD)

**Files:**
- Create: `domain/services/simkl_payload_router.py`
- Modify: `domain/models/canonical_ids.py` (add `anilist` field, keep merge additive)
- Test: `tests/domain/test_simkl_payload_router.py`

**Interfaces:**
- `AnimeSyncMode` enum: `AUTO_NATIVE_PREFERRED` (default), `TVDB_HYBRID_ONLY`, `NATIVE_ONLY`.
- `SimklPayloadRouter(mode).route(item) -> SimklRoute` where `SimklRoute` carries:
  - `path`: `"native" | "hybrid" | "standard" | "needs_identity"`
  - `envelope`: `"anime" | "shows" | "movies"` (None for `needs_identity`)
  - `entry`: the JSON-ready dict payload entry
  - `reason`: human-readable route explanation (transparency requirement)

**Routing rules (pure, no I/O):**
1. Non-anime movie → `movies[]` standard entry (title, year, ids, rating).
2. Non-anime show → `shows[]` standard entry with per-episode `seasons[]` structure when episodes exist. `use_tvdb_anime_seasons: true` is a safe no-op and is NOT added for non-anime.
3. Anime, native-capable (any of `mal`/`anilist`/`anidb`/`kitsu` present AND a flat/absolute episode number available or item-level status-only write): Path B → `anime[]` envelope, `ids` restricted to native + simkl ids, `episodes: [{"number": N}]` flat list, never a `season` key.
4. Anime, hybrid-capable (tmdb or tvdb present AND season+episode coordinates): Path A → `shows[]` envelope, `use_tvdb_anime_seasons: true`, `seasons: [{"number": S, "episodes": [{"number": E}]}]`. Send both tmdb and tvdb when both exist (boundary-disagreement guard). Title+year included as resolver fallback.
5. Mode gates: `NATIVE_ONLY` refuses hybrid fallback (ambiguous → `needs_identity`); `TVDB_HYBRID_ONLY` refuses native; `AUTO_NATIVE_PREFERRED` tries native → hybrid → `needs_identity`.
6. **Never derive or invent a Simkl ID.** A shared parent tmdb/tvdb never produces an ID-only anime entry; without coordinates or native IDs the item quarantines as `needs_identity` with a reason.

- [ ] Step 1: Write failing tests covering the routing matrix: native cour-split (mal-only, flat ep 4), native absolute long-runner (ep 403), hybrid split-cour (tmdb 1429 S3E13 with flag), both-IDs-sent case, needs_identity quarantine (anime with only shared tmdb parent and no coordinates), NATIVE_ONLY refusal, TVDB_HYBRID_ONLY refusal, non-anime passthrough without flag, no `season` key ever in native episodes.
- [ ] Step 2: Implement `simkl_payload_router.py` until tests pass. Stdlib only.

### Task 2: Infrastructure — Correct /sync/history adapter contract (TDD)

**Files:**
- Modify: `exporters/simkl_sync.py`
- Test: extend `tests/infrastructure/test_sync_adapters.py`

**Interfaces:**
- `SimklSyncAdapter.sync_history(routed: Dict[str, List[dict]]) -> SimklSyncResult`
  - POSTs to `https://api.simkl.com/sync/history` (correct endpoint; keep `add_to_history` as thin deprecated alias delegating to it).
  - Batches per envelope at `batch_size` (100), preserving `{"movies": [...], "shows": [...], "anime": [...]}` shape per chunk.
  - Parses response body: structured `added` counts and `not_found` echo entries; result exposes `added`, `not_found` (list of payload entries Simkl rejected), `errors`.
  - Retry policy: on HTTP 429 or 5xx, bounded retries (max 3) honoring `Retry-After` when present; injectable `sleep_fn` so tests don't sleep.
  - Diagnostics logging redacts the bearer token (log status + counts, never headers).

- [ ] Step 1: Write failing tests with mocked `urllib.request.urlopen`: endpoint URL, envelope preservation, chunking >100, added/not_found parsing, 429 Retry-After honored then success, bounded retry exhaustion → errors, token never in log output.
- [ ] Step 2: Implement until green.

### Task 3: Application — flush_outbox uses router + structured results (TDD)

**Files:**
- Modify: `application/use_cases/flush_outbox.py`
- Modify: `config.py` / `config.yaml` (add `providers.simkl.anime_mode`, default `auto_native_preferred`)
- Test: extend `tests/application/test_process_scrobble.py` sibling: create `tests/application/test_flush_outbox.py`

**Behavior:**
- Simkl branch routes every pending item via `SimklPayloadRouter` (mode from config).
- `needs_identity` routes → outbox status `unmatched` (quarantined, transparent reason logged), never sent.
- Sent items map back from `not_found` echoes → those items get `error` status with reason; the rest `synced`. Partial failure preserves failed items (no all-or-nothing bool).
- No behavior change for MAL/Nuvio branches.

- [ ] Step 1: Failing tests: pending anime with mal id syncs via anime envelope; anime with only parent tmdb and no coords → unmatched not sent; not_found echo marks only that item errored while others sync.
- [ ] Step 2: Implement until green.

### Task 4: Phase 0 — architecture decision + prototype claim correction

**Files:**
- Create: `docs/adr/0001-provider-runtime-in-nuviotv.md` — records issue #1 core decision: production event capture/credentials/queues belong in NuvioTV Kotlin; this repo remains the architecture reference, mapping/fixture, migration/backfill, and contract test-vector home. Links issue #1 and the Simkl guide paths.
- Modify: `README.md` — correct prototype claims accordingly and document the new `anime_mode` setting.
- Modify: `AGENTS.md` — add Simkl Path A/B routing rules to provider standards (rate limiting section already exists).

- [ ] Step 1: Write ADR + README/AGENTS updates.

### Task 5: Verification

- [ ] `PYTHONPATH=. python3 -m unittest discover -s tests -t . -v` — all pass (≥47 existing + new).
- [ ] `node tests/ui/test_plugin.js && node tests/ui/test_toast.js` — pass.
- [ ] Full pipeline smoke: `python3 main.py` completes without regression.
- [ ] Grep guard: no `sync/add-to-history` callers left outside the deprecated alias; no hardcoded secrets.

---

## GSTACK REVIEW REPORT (/autoplan, 2026-07-23)

Mode: autonomous (user directive). Codex unavailable (usage limit until Jul 28) → all phases `[subagent-only]`. Phase 2 (Design) skipped: no UI scope. Phase 3.5 (DX) skipped: re-evaluated as no developer-facing surface (API terms refer to outbound Simkl calls); DX-relevant items captured in Eng F1/F9.

### CEO DUAL VOICES — CONSENSUS TABLE
| Dimension | Claude | Codex | Consensus |
|---|---|---|---|
| Premises valid? | MOSTLY (guide-verified; live-API unverified) | N/A | flagged |
| Right problem? | PARTIALLY (portable contract > Python runtime) | N/A | flagged |
| Scope calibration? | MIXED (Task 2 overbuilt, vectors missing) | N/A | flagged |
| Alternatives explored? | NO (add to ADR) | N/A | flagged |
| Competitive risks? | LOW (substitution note → ADR) | N/A | flagged |
| 6-month trajectory? | SOUND with amendments | N/A | flagged |

### ENG DUAL VOICES — CONSENSUS TABLE
| Dimension | Claude | Codex | Consensus |
|---|---|---|---|
| Architecture sound? | CONDITIONAL (F1/F6/F12) | N/A | flagged |
| Test coverage sufficient? | NO (F14 list added below) | N/A | flagged |
| Performance risks? | OK (cap Retry-After) | N/A | flagged |
| Security covered? | LARGELY (F13 residuals) | N/A | flagged |
| Error paths handled? | NO (F2/F3/F4/F5 — now amended) | N/A | flagged |
| Deployment risk? | MANAGEABLE with amendments | N/A | flagged |

### Plan Amendments (accepted findings, binding for execution)

1. **Golden contract vectors (CEO-F1):** add `tests/fixtures/simkl_contract_vectors.json` — (canonical item, mode) → (route, envelope, entry) pairs — verified by a dedicated test; this is the portable spec the NuvioTV Kotlin port consumes. ADR records guide version/date.
2. **Absolute-episode provenance (CEO-F3):** native path requires a source-provided flat/absolute episode (`absolute_episode`, or legacy episode entries without season semantics). If a native-ID anime has only S/E coordinates, AUTO mode falls back to hybrid (Simkl does the mapping); NATIVE_ONLY quarantines. Never locally derive absolute numbers.
3. **No episode-less series writes (CEO-F4/Eng-F2, critical):** `/sync/history` entries for shows/anime series MUST carry episode coordinates; episode-less history entries are only legal for movies (incl. anime movies via `anime[]` with native ids, or `movies[]` otherwise). Episode-less series → quarantine `needs_identity`/`missing_coordinates`.
4. **Config plumbing (Eng-F1, critical):** implement a minimal strict stdlib YAML-subset loader in `config.py` (nested keys, scalars, comments only) reading `config.yaml`; `providers.simkl.anime_mode` default `auto_native_preferred`; unknown mode fails loud. Env var `SIMKL_ANIME_MODE` overrides for tests/ops.
5. **not_found correlation (Eng-F3):** router emits digit-only ids as ints (canonical wire form); flush keeps ordered (entry, item) correlation per chunk; echo matching via normalized id-set intersection + episode coords, fallback title+year; ambiguous → all candidates errored with reason; unmatched echo → logged, counted, no unrelated mutation.
6. **watched_at + retry idempotency (Eng-F4):** every entry carries `watched_at` (ISO-8601 from `watched_date`) when available. Bounded retries ONLY on 429 (request rejected ⇒ safe), honoring integer `Retry-After` capped at 60s (HTTP-date/absent → exponential backoff). 5xx/timeout = unknown outcome ⇒ NO in-call retry; chunk marked errored, next flush cycle retries via outbox `retry_count`. Non-retryable 4xx never retried; 401 yields distinct "Simkl token expired or invalid" message.
7. **Per-chunk error attribution (Eng-F5):** `SimklSyncResult.errors` carries the failed entries themselves so flush maps chunk→items; partial failure preserves exact failed set (test: 250 items, chunk 2 fails ⇒ those 100 errored, 150 synced).
8. **Legacy pipeline in scope (Eng-F6):** router accepts both the domain item (scalar coords) and legacy `models.CanonicalMediaItem` (episodes list) via duck-typed attribute access; `export_simkl_payload` routes anime through the router so `simkl_import.json` stops emitting forbidden ID-only anime entries. Legacy movies/shows keep current shape.
9. **anilist (Eng-F7):** add `anilist` to domain `CanonicalIDs` AND populate it in `otaku_enrichment` from Otaku-Mappings if the source carries `anilist_id`; if the mapping source lacks it, drop the field from scope.
10. **media_type vocabulary (Eng-F8):** series = {"show", "series"}; unknown media_type → quarantine with reason; explicit anime-movie routing rule + tests.
11. **Alias contract (Eng-F10):** `add_to_history(list) -> bool` preserved exactly (wraps `{"shows": chunk}`, collapses result to bool), pinned by test, removed only after flush_outbox migrates.
12. **Batching (Eng-F11):** empty routed payload ⇒ zero HTTP calls, success result. Chunking = per-request total ≤ batch_size across envelopes.
13. **Layering (Eng-F12):** adapter moves to `infrastructure/api_clients/simkl.py`; `exporters/simkl_sync.py` becomes a re-export shim; flush_outbox drops concrete type hints. ADR records the router-returns-wire-format tradeoff.
14. **Log hygiene (Eng-F13):** error bodies capped (500 chars) + control chars stripped before logging/persisting; grep guards exclude `.claude/worktrees` and `.worktrees`.
15. **Docs first (CEO-F8):** ADR + README correction execute as Task 0.
16. **Test additions (Eng-F14):** malformed/non-JSON bodies, missing envelope keys in response, both-ids native-wins + tvdb-excluded pinning, episode=0/season=0, empty-string id sentinels, retry_count/error_message on exception, unmatched items not re-sent, adapter=None untouched, mixed-envelope overflow, empty batch.

### NOT in scope (deferred to TODOS.md)
- Live-API validation spike against a real Simkl account (CEO-F2) — side effects on user's real tracking data; needs user-run token + consent. Instructions in TODOS.md.
- Scheduled contract-drift canary (CEO-F7) — new infra; ADR records guide date instead.
- Provider-generic router abstraction (CEO-F6c) — ADR paragraph only.

### User Challenges
- **Drop 3-mode config to AUTO-only (CEO-F5):** models recommend shipping one mode; issue #1 explicitly specifies the 3-mode `AnimeSyncMode`. **User direction stands: 3 modes kept.**

### What already exists
- `domain/services/otaku_enrichment.py` (id enrichment), `ProviderOutboxState` states, batching pattern in `flush_outbox`, `absolute_episode` field on domain item, Otaku-Mappings repository in `infrastructure/otaku_mappings/`.

### Decision Audit Trail
| # | Phase | Decision | Classification | Principle | Rationale | Rejected |
|---|-------|----------|----------------|-----------|-----------|----------|
| 1 | CEO | Premise gate auto-approved | gate (user pre-auth) | P6 | User declared full autonomy; premises guide-verified | blocking |
| 2 | CEO | Add golden contract vectors | mechanical | P1,P2 | Repo's decided role is contract home | Python-only spec |
| 3 | CEO | Defer live-API spike | mechanical | — | Real-account side effects need user consent | autonomous live writes |
| 4 | CEO | Keep 3 anime modes | USER CHALLENGE | — | Issue #1 specifies enum; user direction stands | AUTO-only |
| 5 | CEO | Native requires provenance | mechanical | P1 | Prevents silent wrong-episode corruption | derive offsets locally |
| 6 | Eng | Stdlib YAML-subset loader | taste→decided | P5 | AGENTS.md mandates config.yaml as source of truth; no new deps | pyyaml dep; env-only |
| 7 | Eng | Retry only on 429 | mechanical | P5,P1 | 429=rejected=safe; 5xx/timeout=unknown ⇒ outbox-cycle retry | blind 5xx retry |
| 8 | Eng | Errors carry failed entries | mechanical | P1 | Per-item attribution; fixes legacy all-or-nothing bug | string errors |
| 9 | Eng | Route legacy exporter via router | borderline scope→approved | P2 | In blast radius; stops forbidden payload shape | out-of-scope note |
| 10 | Eng | Move adapter to infrastructure/ | mechanical | P5 | AGENTS.md layer table; shim keeps compat | leave in exporters/ |
| 11 | Autoplan | DX phase skipped | mechanical | P3 | No developer-facing surface; DX items in Eng F1/F9 | full DX phase |
