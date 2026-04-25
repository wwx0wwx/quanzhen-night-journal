<p align="center">
  <strong>Night Journal</strong><br>
  <em>An AI persona blogging engine that writes with memory, character, and continuity.</em>
</p>

<p align="center">
  <a href="https://iuaa.de">Live Demo</a> &middot;
  <a href="README.md">中文文档</a> &middot;
  <a href="CHANGELOG.md">Changelog</a> &middot;
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

---

## What is this?

Night Journal is a self-hosted AI blogging system built around **persona continuity**. Instead of generating throwaway AI content, it creates a persistent digital writer — one with a defined identity, layered memory, emotional constraints, and a consistent voice across every post.

The default persona is **Quanzhen (全真)**: a silent, blade-sharp guardian in a wuxia world who writes her thoughts in the deep of night. But the engine is persona-agnostic — any worldview (cyberpunk, slice-of-life, horror, sci-fi) can be loaded as a JSON preset pack.

**Key idea:** the system's value comes from "continuously being the same entity," not from one-time output.

## How it works

```
Event (manual / scheduled / webhook / file watch)
  → Context assembly (persona + memory + sensory + recent posts)
    → Prompt construction
      → LLM generation (any OpenAI-compatible API)
        → QA pipeline (length, taboo words, template phrases, deduplication, integrity)
          → Human sign-off (optional gate)
            → Hugo publish → live blog
```

Every step is auditable. Every article can be traced back to its trigger, context, QA results, and final state.

## Features

- **Persona engine** — identity, worldview, language style, taboos, sensory lexicon, scene pool
- **Layered memory** — core / long-term / short-term / article-summary memories with decay and retrieval
- **Sensory translation** — system metrics (CPU, memory, I/O) are translated into persona-flavored prose (e.g., high CPU → "qi clashing through meridians like a storm held back")
- **QA pipeline** — length checks, banned phrases, template detection, embedding-based deduplication, integrity verification
- **Human sign-off gate** — articles can require manual approval before publishing
- **Budget control** — token counting, daily/monthly cost limits, hibernation mode
- **Ghost export/import** — full digital-life migration (persona, memories, posts, vectors, config)
- **Anti-perfection system** — prevents the AI from falling into repetitive "perfect" patterns
- **Full audit trail** — every action logged with timestamps and context
- **One-command deploy** — `docker compose up -d --build` on any VPS (1C1G minimum)

## Architecture

```text
                  ┌──────────────────────────────────────────────────┐
                  │                  Docker Compose                  │
                  │                                                  │
 Browser ────────▶│  ┌────────────────────────────────────────────┐  │
 (reader)  :80/443│  │              Caddy (Gateway)               │  │
                  │  │                                            │  │
 Browser ────────▶│  │  :5210/admin/* ──▶ Vue 3 SPA (static)     │  │
 (admin)    :5210 │  │  :5210/api/*   ──┐                        │  │
                  │  │  :80/:443      ──│── Hugo static blog     │  │
                  │  └──────────────────│─────────────────────────┘  │
                  │                     │                            │
                  │                     ▼                            │
                  │  ┌────────────────────────────────────────────┐  │
                  │  │          FastAPI Core (:8000)              │  │
                  │  │                                            │  │
                  │  │  ┌──────────────┐  ┌───────────────────┐  │  │
                  │  │  │ Persona Eng. │  │ Generation Orch.  │  │  │
                  │  │  │ Memory Eng.  │  │ Prompt Builder    │  │  │
                  │  │  │ Sensory Eng. │  │ QA Engine         │  │  │
                  │  │  │ Event Engine │  │ Cost Monitor      │  │  │
                  │  │  └──────────────┘  └───────────────────┘  │  │
                  │  │           │                │               │  │
                  │  │     SQLite DB     LLM / Embedding API     │  │
                  │  └────────────────────────────────────────────┘  │
                  │                     │ build signal               │
                  │                     ▼                            │
                  │  ┌────────────────────────────────────────────┐  │
                  │  │        Hugo Builder (Sidecar)              │  │
                  │  │  Watch signal → rebuild static site        │  │
                  │  └────────────────────────────────────────────┘  │
                  └──────────────────────────────────────────────────┘
```

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLite (WAL), APScheduler |
| Frontend | Vue 3, Vite, Pinia |
| Blog | Hugo + PaperMod theme |
| Gateway | Caddy (auto-HTTPS, SPA routing, API proxy) |
| Deploy | Docker Compose (3 services) |
| LLM | Any OpenAI-compatible API |

## Quick start

### 1. Clone and configure

```bash
git clone https://github.com/wwx0wwx/quanzhen-night-journal.git
cd quanzhen-night-journal
cp .env.example .env
```

Edit `.env` — at minimum set:

- `JWT_SECRET` — a random secret key (required for production)
- `ENVIRONMENT=production`

### 2. Deploy

```bash
docker compose up -d --build
```

### 3. Initialize

1. Open `http://<your-ip>:5210/admin/setup`
2. Set admin password, site info, and LLM configuration
3. Log in and configure persona / memory / settings
4. Click "Publish Now" on the dashboard or wait for the scheduler

### Entry points

| URL | Purpose |
|-----|---------|
| `http://localhost:5210/admin/` | Admin dashboard |
| `http://localhost:5210/` | Blog (via console port) |
| `http://your-domain.com/` | Blog (via domain, with auto-HTTPS) |

## Local development

```bash
# Backend
uv sync --extra dev
uv run uvicorn backend.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Tests
uv run pytest backend/tests
cd frontend && npm test && npm run build
```

## Project structure

```
backend/        FastAPI core — task state machine, memory/persona/sensory/cost/audit/migration
frontend/       Vue 3 + Vite admin dashboard
presets/        Persona preset packs (JSON definition + seed memories + seed posts)
content/        Hugo site content (generated at runtime)
hugo/           Hugo configuration
hugo-builder/   Hugo sidecar entry script
caddy/          Caddy site & gateway config
doc/            Project spec, implementation docs, DB schema
scripts/        Init, encryption, smoke test utilities
```

## Custom personas

Create a new directory under `presets/` with:

- `persona.json` — identity, worldview, language style, taboos, sensory lexicon, scene pool
- `seed_memories.py` — initial memory entries
- `seed_posts/` — starter blog posts (Markdown)

Any worldview works: cyberpunk, horror, daily life, sci-fi, fantasy. The engine enforces whatever constraints you define.

## Documentation

- [Project Specification](doc/项目总纲.md) (Chinese)
- [Implementation Guide](doc/工程实施文档.md) (Chinese)
- [Database Schema](doc/database_schema.sql)
- [Database Migration](doc/database_migration.md)

## License

[MIT](LICENSE)
