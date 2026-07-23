# AGENTS.md - Developer & AI Agent Guidelines

Welcome AI agents and human contributors! This document outlines architectural standards, workflow rules, and skill routing guidelines for contributing to **What I Watched Sync**.

---

## 1. Core Architecture Principles (DDD & On-Device First)

- **Domain-Driven Design (DDD)**: Code must strictly respect layer boundaries:
  - `domain/`: Pure business logic, canonical models (`CanonicalMediaItem`, `CanonicalIDs`), outbox states, and policies. **Zero external HTTP/I/O dependencies allowed in domain/**.
  - `application/`: Orchestrates use cases (`process_scrobble.py`, `flush_outbox.py`).
  - `infrastructure/`: External API adapters (Trakt, MAL, Simkl, Nuvio Supabase) and persistence stores (`local_storage.py`).
  - `ui/`: Nuvio Addon manifest (`manifest.json`), Hermes JS provider bundle (`providers/otaku_sync_plugin.js`), and toast notifier (`ui/toast_notifier.js`).
- **Runtime split**: the sync engine, routing, and contract vectors live here; the production runtime (live capture, QR/PIN login, credentials, durable queues) is NuvioTV Kotlin. Nuvio's JS plugin runtime is a `getStreams` stream scraper and cannot run sync. See [docs/NUVIO_INTEGRATION.md](docs/NUVIO_INTEGRATION.md) and [ADR 0001](docs/adr/0001-provider-runtime-in-nuviotv.md).
- **100% On-Device / Serverless**: No central backend servers. Everything executes on the client device.
- **Selective Enrichment**: `Fribb/anime-lists` and `Goldenfreddy0703/Otaku-Mappings` enrich missing IDs/offsets ONLY. Never overwrite valid existing IDs. All enrichment data is additive and also carries into our canonical store.
- **Zero Data Loss**: No payload or conflict item is ever discarded. Everything is transparent.

---

## 2. Configuration & Settings

All behavioral settings are centralized in `config.yaml`. Every function that makes a decision must read from this configuration rather than hardcoding behavior. Changes to behavior are tracked in the repo via the config file.

Key settings include:
- `sync_cadence` : how often and when syncing occurs
- `conflict_policy` : how duplicates and conflicts are handled (always prompt by default)
- `enrichment_policy` : Otaku-Mappings selective enrichment controls
- `providers` : per-provider rate limits and batch sizes
- `ui` : toast density, duration, and accessibility preferences

---

## 3. Skill Routing Guidelines

When performing tasks in this repository, agents should invoke the following skills:

- **Brainstorming / Features** → `/brainstorming`
- **Architecture / Engineering Reviews** → `/plan-eng-review`
- **Developer Experience Reviews** → `/plan-devex-review`
- **Systematic Debugging** → `/investigate`
- **QA Testing & Bug Fixes** → `/qa`
- **Code Reviews** → `/review`
- **Documentation Updates** → `/document-release`

---

## 4. Testing & Verification Requirements

- **Domain Unit Tests**: Every domain entity or service must have a corresponding test in `tests/domain/` using Python's native `unittest` framework.
- **Application Use Case Tests**: Use case orchestrators must be tested in `tests/application/`.
- **Infrastructure Unit Tests**: API adapters and persistence must be tested in `tests/infrastructure/`.
- **Hermes JS Bundle Validation**: Validate JavaScript syntax using `node tests/ui/test_plugin.js`.

To run all tests locally:
```bash
PYTHONPATH=. python3 -m unittest discover -s tests -t . -v
node tests/ui/test_plugin.js
node tests/ui/test_toast.js
```

Test count should be ≥100 Python tests + 2 JS tests. All must pass before any commit.

---

## 5. Code Quality Standards

- **No Mocked Functionality**: Every function must be real and operational. No `TODO`, `FIXME`, or stub implementations.
- **No Hardcoded Secrets**: All credentials come from environment variables or `.env` files. See `.env.example`.
- **Atomic Persistence**: All file writes use `os.replace()` (temp-then-rename) to prevent data corruption.
- **Error Handling**: Every external API call must have try/except with logging. Never silently swallow errors.
- **Rate Limiting**: MAL requires 600ms delay between calls. Simkl batches at 100 items. These are enforced in the adapter layer.

### Simkl Anime Routing (Path A / Path B)

Anime is serialized to Simkl per the [official anime guide](https://api.simkl.org/guides/anime). Routing is pure domain logic in `domain/services/simkl_payload_router.py`; the contract is frozen in `tests/fixtures/simkl_contract_vectors.json` (the portable spec for the NuvioTV Kotlin port). See [ADR 0001](docs/adr/0001-provider-runtime-in-nuviotv.md).

- **Path B (native)**: native id (MAL/AniList/AniDB/Kitsu) + absolute episode → `anime[]` envelope, flat `episodes: [{number}]`, never a `season` key, ids restricted to native + simkl.
- **Path A (hybrid)**: TMDB/TVDB + season coordinates → `shows[]` envelope, `use_tvdb_anime_seasons: true`, TVDB `seasons[]`. Send both tmdb and tvdb when both exist.
- **Never derive a cour-specific Simkl id from a shared TMDB/TVDB parent.** Unresolved identity quarantines as `needs_identity` (outbox status `unmatched`), never guessed.
- **Native path needs absolute-episode provenance.** A native-id anime with only S/E coordinates falls back to Path A; it is never locally converted to an absolute number.
- **No episode-less series history writes** (they mark the whole show watched). Only movies post without episode coordinates.
- **Endpoint**: `POST /sync/history`. Retry only on 429 (honor `Retry-After`, capped 60s). 5xx/timeout have an unknown outcome, so the adapter never retries them in-call; the item is left `error` for the caller to retry on a later run. Durable queueing and automatic re-drain are NuvioTV's responsibility (ADR 0001), not this reference adapter. `not_found` echoes are permanent identity mismatches and are quarantined as `unmatched`, not retried. Mode is `providers.simkl.anime_mode` in `config.yaml`.

---

## 6. DDD Layer Boundaries (Strict)

| Layer | Allowed Imports | Forbidden |
|-------|----------------|-----------|
| `domain/` | Python stdlib only | `urllib`, `requests`, `json.load(file)`, any I/O |
| `application/` | `domain/`, infrastructure interfaces | Direct HTTP calls |
| `infrastructure/` | `domain/` models, `urllib`, file I/O | Business logic |
| `ui/` | Browser APIs, Node.js `fs`/`path` | Python imports |

If a domain service needs data from an external source, it must receive it as a parameter (dependency inversion).

---

## 7. Contribution Workflow

1. **Read this file first.**
2. **Check existing tests pass** before starting work.
3. **Write tests first** for any new domain logic.
4. **Respect layer boundaries.** If your change touches `domain/`, it must not import from `infrastructure/`.
5. **Run the full test suite** before committing.
6. **Update `config.yaml`** if adding any new configurable behavior.
7. **Update this AGENTS.md** if adding new architectural patterns.

---

## 8. Project Structure

```
├── domain/                    # Pure business logic (no I/O)
│   ├── models/               # CanonicalMediaItem, CanonicalIDs, OutboxState, ConflictPolicy
│   └── services/             # ConflictResolver, OtakuEnrichment
├── application/              # Use case orchestrators
│   └── use_cases/            # process_scrobble, flush_outbox
├── infrastructure/           # External integrations
│   ├── api_clients/          # Simkl (/sync/history) + NuvioSupabase adapters
│   ├── otaku_mappings/       # Fribb/Otaku-Mappings mapper repository
│   └── persistence/          # LocalStorage (atomic JSON)
├── extractors/               # Data extractors (MAL XML, Trakt JSON, Simkl API, Nuvio JSON)
├── exporters/                # Data exporters (master files, service payloads, sync adapters)
├── providers/                # Hermes JS plugin bundle for Nuvio TV
├── ui/                       # Toast notifier (A11y, Nielsen UX)
├── tests/                    # All tests (mirrors source structure)
├── config.py                 # Environment-based configuration loader
├── config.yaml               # Central settings (all behaviors recorded here)
├── manifest.json             # Nuvio addon manifest
├── main.py                   # CLI entry point
├── AGENTS.md                 # This file
├── USER_INSTALLATION_GUIDE.md # End-user setup (ELI5 / MOM test)
└── KCS_KNOWLEDGE_BASE.md     # Knowledge-centered support articles
```

---

## 9. Accessibility & ADHD/AuDHD Guidelines

- **Toasts**: Non-disruptive, high-contrast, `aria-live="polite"`, auto-dismiss after configurable duration.
- **No decision fatigue**: Conflict resolution defaults to "prompt" - user always chooses.
- **Clear status indicators**: Every sync operation reports status via toast.
- **Configurable density**: Users can set toast density to `all`, `warnings_errors`, or `silent`.
- **D-pad navigation**: All interactive elements support TV remote D-pad focus.
