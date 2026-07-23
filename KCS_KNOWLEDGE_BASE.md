# Knowledge Base

Knowledge-Centered Service articles for What I Watched Sync. This repository is a
prototype and design reference; the production TV runtime targets NuvioTV (see
[ADR 0001](docs/adr/0001-provider-runtime-in-nuviotv.md)). Articles below mark
what runs today versus what is designed for NuvioTV.

---

## Article 1: How watch history syncs to providers

**Status**: pipeline implemented in this repo; live playback capture is designed for NuvioTV.

The engine normalizes watch history into canonical records, enriches anime IDs
from Otaku-Mappings, and routes each item to the correct provider payload:

1. **Completion threshold**: an item counts as watched once playback crosses the
   configured threshold (default 85%, `config.yaml` → `sync_cadence.scrobble_threshold_percent`).
2. **Provider routing**: Trakt, MyAnimeList, Simkl, and Nuvio Sync each receive a
   payload shaped for their API. Simkl anime follows the Path A/Path B contract in
   [AGENTS.md](AGENTS.md#simkl-anime-routing-path-a--path-b).
3. **Otaku enrichment**: Fribb and Otaku-Mappings supply missing native IDs and
   episode offsets so TVDB/TMDB season coordinates resolve to anime records. Existing
   valid IDs are never overwritten.

Readback is limited to account validation, baseline establishment, and reconciliation;
provider state does not overwrite local history.

---

## Article 2: Device authentication (designed for NuvioTV)

**Status**: design target, not implemented in this repo.

Typing OAuth credentials with a TV remote is slow. The intended NuvioTV flow shows a
QR code and short PIN on screen; the user approves on their phone at the provider's
activation page (for example [simkl.com/pin](https://simkl.com/pin) or
[trakt.tv/activate](https://trakt.tv/activate)), and the TV updates to connected.
The token exchange and credential storage belong in NuvioTV, not in this pipeline.

---

## Article 3: Unmatched item recovery

**Status**: quarantine behavior implemented; the settings UI is designed for NuvioTV.

Nothing is deleted or discarded. When an item cannot be resolved to a provider record:

1. It stays in the local history file (`combined_full.json`) with the outbox status
   set to `unmatched` (or `needs_identity` for anime that cannot be routed without
   guessing identity from a shared parent ID).
2. The reason is recorded so the item can be inspected rather than silently dropped.
3. In NuvioTV, an inline badge (`MAL: Unmatched`) and edit/skip/search-ID actions let
   the user correct the ID or dismiss the item.
