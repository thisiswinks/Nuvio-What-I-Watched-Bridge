# Knowledge-Centered Service (KCS) Knowledge Base

Welcome to the **What I Watched Sync** Knowledge Base! This repository adheres to Knowledge-Centered Service (KCS) principles: knowledge is created, enriched, reused, and maintained as a natural byproduct of development and user feedback.

---

## KCS Article 1: How Does On-Device 2-Way Sync Work?

**Environment**: Nuvio TV (Android TV, Mobile, Desktop)  
**Issue**: How can I sync my watch progress across Trakt, MyAnimeList (MAL), and Simkl without sending my data to a 3rd-party server?  
**Resolution**:
What I Watched Sync runs **100% locally on your device**. When you watch a movie or anime episode in Nuvio TV:
1. **Live Progress**: Trakt and Nuvio Supabase RPC receive real-time percentage progress updates.
2. **Watched Completion**: Once playback crosses **85% completion** (fully configurable in settings), MyAnimeList (MAL) and Simkl mark the item as `completed` / `watched`.
3. **Selective Otaku Enrichment**: Fribb and Otaku-Mappings automatically map TVDB / TMDB season numbers to MyAnimeList absolute episode numbers (e.g. Season 2 Episode 5 ➔ Episode 30).

---

## KCS Article 2: How Do I Authenticate on Smart TVs without Remote Typing?

**Environment**: Smart TVs (Android TV, Google TV, Fire TV)  
**Issue**: Typing long OAuth passwords with a TV remote is painful and frustrating.  
**Resolution**:
1. Open Nuvio TV ➔ Settings ➔ What I Watched Sync.
2. Click on the target service (Trakt or Simkl).
3. A large QR code and 6-digit PIN (e.g., `8F3-A1B`) will display on your TV screen.
4. Scan the QR code with your smartphone camera or visit [simkl.com/pin](https://simkl.com/pin) / [trakt.tv/activate](https://trakt.tv/activate).
5. Tap **Approve** on your phone. Your TV will automatically update to `Connected` within 3 seconds!

---

## KCS Article 3: How Does Unmatched Item Recovery Work?

**Environment**: Anime & Movies with missing or ambiguous database entries  
**Issue**: What happens if an anime episode cannot be found on MyAnimeList or Simkl?  
**Resolution**:
1. Nothing is ever deleted or discarded.
2. The item is safely stored in your local history file (`combined_full.json`) with the outbox status marked as `unmatched`.
3. An inline badge displays on the item card (`MAL: Unmatched`).
4. You can click `[Edit]`, `[Skip]`, or `[Search ID]` right from Nuvio settings to manually enter the correct ID or ignore the warning.
