# Using What I Watched Sync

This repository is the sync engine and design reference. The consumer TV addon
(live playback capture, on-device account pairing) targets NuvioTV; see
[ADR 0001](docs/adr/0001-provider-runtime-in-nuviotv.md). This guide covers what
you can run today and what the finished NuvioTV experience is designed to do.

## What it does

When you watch movies, TV shows, or anime, What I Watched Sync updates your watch
history on MyAnimeList, Trakt, Simkl, and Nuvio Sync so your progress stays in one
place. Anime is mapped to the correct provider records using Otaku-Mappings.

## Run the pipeline today

You need Python 3.

1. Clone this repository.
2. Copy `.env.example` to `.env` and add your provider keys.
3. Point the importers at your export files (or set the paths in `.env`):
   `TRAKT_EXPORT_DIR`, `MAL_EXPORT_FILE`, `NUVIO_EXPORT_FILE`.
4. Run it:

   ```bash
   PYTHONPATH=. python3 main.py
   ```

The pipeline normalizes your history, deduplicates it, and writes provider-ready
payloads plus a reconciliation report to `data/export/`.

## Connecting accounts on NuvioTV (designed)

The finished NuvioTV addon pairs accounts without remote typing: open
**Nuvio TV Settings → What I Watched Sync**, pick a service, and a QR code and PIN
appear on screen. You approve on your phone, and the TV shows the account as
connected. This flow lives in NuvioTV, not in this pipeline.

## FAQ

**Does it cost anything?**
No. It is free and open source (MIT).

**Is my data private?**
Yes. Processing runs on your device and the pipeline writes only to local files. No
credentials are stored in this repository. Keep your `.env` out of version control
(it is already in `.gitignore`), and never commit the contents of `data/export/`,
which hold your real watch history.

**What if an episode is not found on MyAnimeList or Simkl?**
It is kept in your local history with an `unmatched` status and a recorded reason, so
you can correct the ID later rather than losing the entry.
