# What I Watched Sync

> A 100% on-device sync engine that bridges what you watch on Nuvio TV to Trakt, MyAnimeList (MAL), Simkl, and Nuvio Sync.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**What I Watched Sync** is a privacy-first, on-device sync engine. No middleman servers, no data harvesting. It normalizes your watch history, enriches anime titles using Otaku mappings, resolves identity conflicts locally, and exports your history to Trakt, MyAnimeList, Simkl, and Nuvio Sync.

> **Status: prototype / architecture reference.** This repository is the design
> reference, anime mapping fixtures, and Simkl contract test-vector home. The
> production sync runtime (live event capture, QR/PIN login, credentials,
> durable queues) targets NuvioTV in Kotlin. To wire it up, follow
> [docs/NUVIO_INTEGRATION.md](docs/NUVIO_INTEGRATION.md). See also
> [ADR 0001](docs/adr/0001-provider-runtime-in-nuviotv.md) and
> [issue #3](https://github.com/thisiswinks/Nuvio-What-I-Watched-Bridge/issues/3).

## Features

* **100% Serverless & Private**: All data processing, deduplication, and routing logic runs on-device.
* **Multi-Platform Sync**: API adapters for **Trakt**, **MyAnimeList (MAL)**, and **Simkl**. Simkl anime follows the official [Path A (TVDB hybrid) and Path B (anime-native)](https://api.simkl.org/guides/anime) contract.
* **Smart Anime Enrichment**: Uses the *Fribb* and *Otaku-Mappings* datasets to align Nuvio media IDs with anime tracking platforms. Unresolved identity is quarantined, never guessed.
* **Conflict Resolution Engine**: A transparent, customizable policy engine that lets you decide how to handle playback conflicts (e.g., prompt user vs. auto-merge).
* **Strict Batching & Rate Limiting**: Built to strictly adhere to API rate limits (like MAL's 600ms delay) and chunk sizes (Simkl's 100-item maximums).
* **ADHD & A11y Friendly UI**: Non-disruptive, polite toasts that conform to Nielsen Norman UX principles.

## Installation & Setup

For a step-by-step walkthrough of the installation process, please see our [User Installation Guide](USER_INSTALLATION_GUIDE.md).

**Quick Start for Power Users:**
1. Clone this repository.
2. Provide your API keys via a `.env` file (see `.env.example`).
3. Run the pipeline: `PYTHONPATH=. python3 main.py`.

### Simkl anime sync mode

`config.yaml` → `providers.simkl.anime_mode` (env override `SIMKL_ANIME_MODE`)
controls how anime is serialized to Simkl:

| Mode | Behavior |
|------|----------|
| `auto_native_preferred` (default) | Native ids with absolute episodes when available, else TVDB hybrid, else quarantine. |
| `tvdb_hybrid_only` | Always route via TMDB/TVDB coordinates and `use_tvdb_anime_seasons`. |
| `native_only` | Only anime-native ids; ambiguous events are quarantined. |

## Architecture

This project strictly follows **Domain-Driven Design (DDD)** to guarantee data integrity and maintainability:

* **Domain (`domain/`)**: Pure business logic (Canonical items, Policies). Zero I/O or HTTP calls.
* **Infrastructure (`infrastructure/`)**: External API adapters, persistence stores, and mapping logic.
* **Application (`application/`)**: Use cases that orchestrate the domain and infrastructure layers.
* **UI (`ui/`)**: Hermes JS bundles and toast notifications tailored for TV displays.

## Documentation & Support

If you encounter issues or want to learn more about how the sync engine handles specific scenarios (e.g., duplicate scrobbles, rate limits), check out our Knowledge-Centered Support base:

- **[KCS Knowledge Base](KCS_KNOWLEDGE_BASE.md)**

## Contributing

We welcome contributions! Whether you're an AI agent, a seasoned developer, or a community member reporting a bug, please read our contribution guidelines first.

- **[Read the Contributor Guidelines (AGENTS.md)](AGENTS.md)**
- **[CONTRIBUTING.md](CONTRIBUTING.md)**

---

*What I Watched Sync - your data, your device, your tracking.*
