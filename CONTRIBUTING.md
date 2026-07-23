# Contributing to Nuvio Watched Importer

Thank you for your interest in improving the **Nuvio Watched Importer**! Whether you are an AI Agent, an open-source enthusiast, or a community member looking to report a bug, your help is appreciated.

## The Core Rule: Read `AGENTS.md`

We have a complete developer and AI agent guideline document located in [`AGENTS.md`](AGENTS.md). **This document is the absolute source of truth for our architecture and contribution workflow.**

Before you write any code, open a pull request, or submit an issue, please read `AGENTS.md` entirely. It covers:
1. Our strict adherence to **Domain-Driven Design (DDD)**.
2. The requirement for **100% on-device** execution.
3. How to write tests for the application (and our requirement for 100% test passing before commits).
4. Our approach to A11y (Accessibility) and ADHD/AuDHD-friendly design.

## How to Contribute

### 1. Reporting Bugs
- Please check the [KCS Knowledge Base](KCS_KNOWLEDGE_BASE.md) first to see if your issue is a known limitation or configuration issue.
- Provide detailed reproduction steps, logs from the Nuvio Addon console, and your current configuration (with secrets redacted!).

### 2. Requesting Features
- We strongly prefer features that align with our "Zero Data Loss" and "Selective Enrichment" policies.
- Open a discussion or an issue before writing large code changes to ensure alignment with the project's vision.

### 3. Submitting Code
1. Fork the repository (`thisiswinks/Nuvio-What-I-Watched-Bridge`).
2. Create a clean feature branch.
3. Write your tests *first* in `tests/domain/`, `tests/infrastructure/`, or `tests/application/`.
4. Ensure all layers respect the DDD boundaries (e.g., absolutely no `urllib` or external dependencies in the `domain/` layer).
5. Run the test suite:
   ```bash
   PYTHONPATH=. python3 -m unittest discover -s tests -t . -v
   node tests/ui/test_plugin.js
   node tests/ui/test_toast.js
   ```
6. Open a Pull Request!

## AI Agent Contributions
If you are an autonomous coding assistant (like Claude, Codex, or Gemini) operating in this repository, you must invoke the appropriate skill workflows for your tasks (e.g., `/gsd-code-review`, `/gstack-qa`) as detailed in `AGENTS.md` prior to concluding your work.

We look forward to building a reliable, private, and fast sync engine with you!
