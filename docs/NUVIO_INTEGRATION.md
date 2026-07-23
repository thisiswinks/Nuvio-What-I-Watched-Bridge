# Making What I Watched Sync work on Nuvio

This is the checklist for wiring the sync engine into NuvioTV, grounded in the
actual NuvioTV source. Read [ADR 0001](adr/0001-provider-runtime-in-nuviotv.md)
first: the sync runtime lives in NuvioTV (Kotlin), not in this repo's JS bundle.

## Why the sync engine cannot be a Nuvio JS plugin

NuvioTV's JS plugin runtime (`core/plugin/PluginRuntime.kt`) compiles a bundle
with QuickJS and calls exactly one function:

```js
getStreams(tmdbId, mediaType, season, episode)  // returns playable streams
```

That is a stream-scraper contract. It never calls `getManifest`/`getCatalog`,
never receives playback progress, and cannot hold credentials or a durable
queue. Scrobbling and account sync are native Kotlin services
(`data/repository/TraktScrobbleService.kt`, `core/sync/PluginSyncService.kt`),
invoked from the player (`ui/screens/player/PlayerRuntimeControllerPlaybackEvents.kt`).

So `providers/otaku_sync_plugin.js` in this repo is a reference stub, not the
sync path. To make sync work on Nuvio you add Kotlin services that mirror the
existing Trakt ones. NuvioTV already ships the complete Trakt blueprint to copy.

## What NuvioTV already provides (the Trakt blueprint)

| Concern | Trakt reference in NuvioTV | Mirror for Simkl / MAL |
|---|---|---|
| Device-code (QR) auth | `data/repository/TraktAuthService.kt` (`startDeviceAuth()`, poll loop) | `SimklAuthService`, `MalAuthService` |
| Auth API | `data/remote/api/TraktApi.kt` (`oauth/device/code`, `oauth/device/token`, `oauth/token`) | `SimklApi`, `MalApi` |
| Auth DTOs | `data/remote/dto/trakt/TraktAuthDtos.kt` | `dto/simkl/*`, `dto/mal/*` |
| Token persistence | `data/local/TraktAuthDataStore.kt` | `SimklAuthDataStore`, `MalAuthDataStore` |
| QR login UI | `ui/screens/settings/TraktScreen.kt` + `TraktViewModel.kt` (renders the QR + PIN) | `SimklScreen`/`SimklViewModel`, `MalScreen`/`MalViewModel` |
| Scrobble/write | `data/repository/TraktScrobbleService.kt` (`scrobbleStart/Stop/Pause`, `buildRequestBody`, `shouldSkip` dedup) | `SimklScrobbleService`, `MalSyncService` |
| Player hook | `ui/screens/player/PlayerRuntimeControllerPlaybackEvents.kt` calls `traktScrobbleService.scrobbleStart/Stop` | add Simkl/MAL calls alongside |

## Step 1 — QR login (device auth) for each service

Mirror `TraktAuthService.startDeviceAuth()` and its poll loop.

- **Simkl** uses the PIN device flow. `GET /oauth/pin?client_id=…` returns a
  `user_code` + `verification_url` (`https://simkl.com/pin`); poll
  `GET /oauth/pin/{user_code}?client_id=…` until it returns an `access_token`.
  Render the `verification_url` as the QR and show `user_code` as the PIN,
  exactly like `TraktScreen.kt`. Simkl tokens do not expire, so no refresh loop.
- **MyAnimeList** uses OAuth2 + PKCE (no device-code endpoint). On a TV, show a
  QR to the authorize URL (`https://myanimelist.net/v1/oauth2/authorize` with
  `code_challenge`); the user approves on their phone and you complete the
  exchange at `/v1/oauth2/token`. Persist the refresh token and refresh on 401,
  the same lifecycle `TraktAuthService` runs for Trakt.
- **Trakt** and **Nuvio Sync** already work; leave them.

Store each service's tokens in its own DataStore, scoped per Nuvio profile
(issue #3: accounts, cursors, and queues are profile-scoped).

## Step 2 — Retrofit APIs

Add `SimklApi.kt` with `@POST("sync/history")` (and `scrobble/start` where
supported) and `MalApi.kt` for the MAL list-update endpoints. The Trakt
`scrobble/start` / `scrobble/stop` / `sync/history` signatures in `TraktApi.kt`
are the shape to follow.

## Step 3 — Port the Path A/B routing (this repo is the spec)

The Simkl payload shape is fully specified and tested here. Port it directly:

- **Rules**: `domain/services/simkl_payload_router.py` — Path B (anime-native
  ids, flat absolute episodes, `anime[]`, no `season`) vs Path A (TMDB/TVDB +
  `use_tvdb_anime_seasons` + TVDB `seasons[]`); quarantine a shared parent id
  rather than guessing a cour.
- **Golden vectors**: `tests/fixtures/simkl_contract_vectors.json` — load these
  verbatim as Kotlin test fixtures so `SimklScrobbleService.buildRequestBody`
  produces byte-identical payloads. This is the contract handshake between the
  two repos.
- **Adapter behavior**: `infrastructure/api_clients/simkl.py` — `/sync/history`,
  `added`/`not_found` handling, 429-only bounded `Retry-After` retry. Reproduce
  in the Kotlin service; the durable retry queue is NuvioTV's Room outbox.

`buildRequestBody` in `SimklScrobbleService` is where the routing lives: switch
on media kind and anime mode exactly as the Python router does.

## Step 4 — Wire into the player

In `PlayerRuntimeControllerPlaybackEvents.kt`, alongside the existing
`traktScrobbleService.scrobbleStart(...)` / `scrobbleStop(...)` calls, dispatch
to the enabled outbound targets for the active profile (Simkl live scrobble
where supported; MAL as a completion/state update at the configured threshold).
Reuse the existing `shouldSkip` dedup so one stop event is one write.

## Step 5 — Profile routing and durable outbox

Follow issue #3: a `ProfileTrackingPolicy` (authoritative source + outbound
targets + accepted media types + anime mode), a Room `TrackingOutbox` with the
idempotency key `profileId + provider + sourceEventId + operation`, and origin
tags to prevent import loops. This repo's `application/use_cases/flush_outbox.py`
and `ProviderOutboxState` show the state machine to mirror.

## What works today (in this repo) vs. what to build (in NuvioTV)

Ready to port:
- Simkl Path A/B routing rules + golden contract vectors.
- `/sync/history` adapter contract (endpoint, added/not_found, 429 retry).
- Outbox state machine and quarantine semantics.
- Dry-run preview: `python3 main.py --simkl-dry-run` shows exact routing per item.
- Import/normalize/dedup pipeline and provider re-import payloads.

Must be built in NuvioTV (not possible in this repo):
- QR/device-code login for Simkl and MAL (Kotlin auth services + screens).
- Live playback capture and scrobble dispatch from the player.
- Credential storage and the durable Room outbox, profile-scoped.
- The Kotlin `SimklScrobbleService` / `MalSyncService` and their Retrofit APIs.

## Definition of "working on Nuvio"

1. User opens Nuvio TV settings, connects Simkl and MAL by scanning a QR / PIN.
2. They finish an episode; at the completion threshold NuvioTV scrobbles it to
   the enabled targets for that profile.
3. Anime routes by the Path A/B rules verified against the golden vectors.
4. Unresolved identity is quarantined and visible, never guessed.
5. Writes survive process death and token expiry via the Room outbox.

Steps 1-2 and 5 are NuvioTV Kotlin work; steps 3-4 are the contract this repo
already provides and tests.
