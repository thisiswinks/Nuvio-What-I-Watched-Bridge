# Nuvio Watched Importer 📺✨

> A powerful, 100% on-device synchronization engine that tracks what you watch on Nuvio TV and bridges it to Trakt, MyAnimeList (MAL), and Simkl.

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-green.svg)](https://thisiswinks.github.io/nuvio-watched-importer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Nuvio Watched Importer** is a privacy-first, on-device syncing addon. No middleman servers, no data harvesting. It observes your playback on Nuvio, enriches anime titles using Otaku mappings, resolves identity conflicts locally, and safely exports your history to the tracking platforms you love.

## 🌟 Features

* **100% Serverless & Private**: All data processing, deduplication, and synchronization logic runs directly on your Nuvio device.
* **Multi-Platform Support**: Built-in, fully compliant API adapters for **Trakt**, **MyAnimeList (MAL)**, and **Simkl**.
* **Smart Anime Enrichment**: Uses the *Fribb* and *Otaku-Mappings* datasets to precisely align Nuvio media IDs with Anime tracking platforms. Never lose a scrobble due to mismatched IDs.
* **Conflict Resolution Engine**: A transparent, customizable policy engine that lets you decide how to handle playback conflicts (e.g., prompt user vs. auto-merge).
* **Strict Batching & Rate Limiting**: Built to strictly adhere to API rate limits (like MAL's 600ms delay) and chunk sizes (Simkl's 100-item maximums).
* **ADHD & A11y Friendly UI**: Non-disruptive, polite toasts that conform to Nielsen Norman UX principles.

## 🚀 Installation & Setup

We've made installing the Nuvio Watched Importer incredibly simple. For a step-by-step, ELI5 walkthrough of the installation process, please see our [User Installation Guide](USER_INSTALLATION_GUIDE.md).

**Quick Start for Power Users:**
1. Clone this repository to your Nuvio Addon directory.
2. Provide your API keys via a `.env` file (see `.env.example`).
3. Load the manifest via your Nuvio Developer Portal.
4. Scan the on-screen QR Code to authenticate your Trakt/MAL/Simkl accounts.

## 🏗️ Architecture

This project strictly follows **Domain-Driven Design (DDD)** to guarantee data integrity and maintainability:

* **Domain (`domain/`)**: Pure business logic (Canonical items, Policies). Zero I/O or HTTP calls.
* **Infrastructure (`infrastructure/`)**: External API adapters, persistence stores, and mapping logic.
* **Application (`application/`)**: Use cases that orchestrate the domain and infrastructure layers.
* **UI (`ui/`)**: Hermes JS bundles and toast notifications tailored for TV displays.

## 📖 Documentation & Support

If you encounter issues or want to learn more about how the sync engine handles specific scenarios (e.g., duplicate scrobbles, rate limits), check out our Knowledge-Centered Support base:

- 📚 **[KCS Knowledge Base](KCS_KNOWLEDGE_BASE.md)**

## 🤝 Contributing

We welcome contributions! Whether you're an AI agent, a seasoned developer, or a community member reporting a bug, please read our contribution guidelines first.

- 🛠 **[Read the Contributor Guidelines (AGENTS.md)](AGENTS.md)**
- 📝 **[CONTRIBUTING.md](CONTRIBUTING.md)**

---

*Nuvio Watched Importer - Your data, your device, your tracking.*
