# Web dashboard design notes

Notes on the browser dashboard (`index.html`, `styles.css`, `app.js`) used to
inspect and import media lists. This is a reference tool, not the NuvioTV addon UI.

## Layout and type

- Dark base `#0a0c10` with `#7c3aed` primary and `#10b981` accent.
- Headings use `Outfit`; body uses `Plus Jakarta Sans` (loaded from Google Fonts).
- Content is capped at 1280px. Cards use CSS grid with
  `repeat(auto-fit, minmax(240px, 1fr))` for stats and `minmax(280px, 1fr)` for
  media items, so the layout reflows from desktop down to mobile.

## Components

- Translucent cards with `backdrop-filter: blur(16px)`.
- Media cards carry per-source badges.
- The Nuvio Sync modal streams import progress and parses a bearer token and API
  key from a pasted cURL command (`parseNuvioAuth` in `app.js`).

## Known gaps

- Fonts load from a CDN, so the dashboard needs network access to render its
  intended typography; it falls back to system fonts offline.
- The dashboard is a local inspection tool. Account pairing and live sync are
  designed for NuvioTV, not implemented here.
