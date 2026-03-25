# Quanzhen Night Journal

A long-running narrative engine for generating and publishing late-night in-character journal entries for **Quan Zhen (全真)**.

## What it does

- Reads real VPS signals and maps them into wuxia-style narrative events
- Maintains world state, recent memory, future fragments, and story arcs
- Generates in-character diary entries with an OpenAI-compatible API
- Refines output, generates titles and descriptions, and performs quality checks
- Supports auto publish and review-first workflows
- Publishes through Hugo + systemd timer
- Includes an analysis script for maintenance and quality review

## Project layout

- `scripts/generate_night_journal.py` — main engine
- `scripts/run_night_journal.sh` — execution entrypoint
- `scripts/analyze_journal.py` — review / diagnostics script
- `automation/` — state, pools, prompts, timer templates, docs

## Important note

This repository is a **sanitized project version**. Runtime secrets, live state, logs, and generated posts should not be committed directly.

## Setup overview

1. Copy `.env.example` to `.env`
2. Fill in your API settings
3. Prepare your Hugo directories
4. Review files under `automation/`
5. Install the systemd service and timer

See `automation/README-system.md` for the full architecture and maintenance notes.
