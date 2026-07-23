# AGENTS.md — Developer & AI Agent Guidelines

Welcome AI agents and human contributors! This document outlines architectural standards, workflow rules, and skill routing guidelines for contributing to **What I Watched Sync**.

---

## 1. Core Architecture Principles (DDD & On-Device First)

- **Domain-Driven Design (DDD)**: Code must strictly respect layer boundaries:
  - `domain/`: Pure business logic, canonical models (`CanonicalMediaItem`, `CanonicalIDs`), outbox states, and policies. **Zero external HTTP/I/O dependencies allowed in domain/**.
  - `application/`: Orchestrates use cases (`process_scrobble.py`, `flush_outbox.py`).
  - `infrastructure/`: External API adapters (Trakt, MAL, Simkl, Nuvio Supabase) and persistence stores (`local_storage.py`).
  - `ui/`: Nuvio Addon manifest (`manifest.json`), Hermes JS provider bundle (`providers/otaku_sync_plugin.js`), and toast notifier (`ui/toast_notifier.js`).
- **100% On-Device / Serverless**: No central backend servers. Everything executes on the client device.
- **Selective Enrichment**: `Fribb/anime-lists` and `Goldenfreddy0703/Otaku-Mappings` enrich missing IDs/offsets ONLY. Never overwrite valid existing IDs.
- **Zero Data Loss**: No payload or conflict item is ever discarded.

---

## 2. Skill Routing Guidelines

When performing tasks in this repository, agents should invoke the following skills:

- **Brainstorming / Features** ➔ `/brainstorming`
- **Architecture / Engineering Reviews** ➔ `/plan-eng-review`
- **Developer Experience Reviews** ➔ `/plan-devex-review`
- **Systematic Debugging** ➔ `/investigate`
- **QA Testing & Bug Fixes** ➔ `/qa`
- **Code Reviews** ➔ `/review`
- **Documentation Updates** ➔ `/document-release`

---

## 3. Testing & Verification Requirements

- **Domain Unit Tests**: Every domain entity or service must have a corresponding test in `tests/domain/` using Python's native `unittest` framework.
- **Infrastructure Unit Tests**: API adapters must be tested in `tests/infrastructure/`.
- **Hermes JS Bundle Validation**: Validate JavaScript syntax using `node tests/ui/test_plugin.js`.

To run all tests locally:
```bash
PYTHONPATH=. python3 -m unittest discover -s tests
node tests/ui/test_plugin.js
node tests/ui/test_toast.js
```
