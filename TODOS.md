# TODOS

Deferred scope from the Simkl anime path-routing work (2026-07-23).
See `docs/superpowers/plans/2026-07-23-simkl-anime-path-routing.md` for the full
review and rationale.

## Live-API validation spike (deferred — needs user consent)

Freeze the golden vectors against the *live* Simkl API, not just the published
guide. This writes to a real Simkl account, so it is out of scope for automated
runs and must be user-initiated.

Steps:
1. Use a throwaway/test Simkl account and its `client_id` + `access_token`.
2. Perform one Path A write (`shows[]` + `use_tvdb_anime_seasons`, e.g. AoT
   S3E13 via tmdb `1429`) and one Path B write (`anime[]` flat episode, e.g.
   One Piece ep 403 via mal `21`) against `POST /sync/history`.
3. Capture the real request/response pairs, especially the exact `not_found`
   echo shape for the `anime[]` envelope, and reconcile against
   `tests/fixtures/simkl_contract_vectors.json` and the adapter's
   `_parse_body`.

## Contract-drift canary (deferred — new infra)

The Simkl anime guide is recent and may change. Consider a scheduled check
(guide content hash or a periodic recorded-request replay) so drift surfaces
instead of silently invalidating the vectors. Guide date recorded in ADR 0001.

## Provider-generic router (deferred — speculative)

Trakt has the same split-cour identity problem as Simkl. If a second consumer
appears, extract a shared routing abstraction. Kept Simkl-specific for now.
