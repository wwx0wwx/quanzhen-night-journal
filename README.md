# Quanzhen Night Journal

A long-running narrative engine for generating and publishing late-night in-character journal entries for **Quan Zhen (全真)** — a cold, restrained, fiercely devoted wuxia heroine whose emotional continuity is maintained through world state, memory, future fragments, and system signals from a live VPS.

## Features

- OpenAI-compatible generation pipeline
- Hugo publishing workflow
- systemd timer support
- World state + story arc progression
- Core memories + recent memories + future fragments
- VPS signal mapping into narrative incidents
- Title / description generation
- Refinement pass + quality checks
- Auto mode and review-first mode
- Analysis / maintenance tooling

## Repository layout

```text
automation/
  *.example.json          # runtime templates
  *.json                  # reusable pools and rules
  README-system.md        # full internal system map
  README-overrides.md     # override reference
  night-journal.service   # systemd service template
  night-journal.timer     # systemd timer template
scripts/
  bootstrap_runtime_state.py
  generate_night_journal.py
  run_night_journal.sh
  analyze_journal.py
  publish_reviewed_post.sh
  discard_review_draft.sh
docs/
  architecture.md
  deployment.md
  review-workflow.md
```

## Quick start

### 1. Clone the repo
```bash
git clone https://github.com/wwx0wwx/quanzhen-night-journal.git
cd quanzhen-night-journal
```

### 2. Configure environment
```bash
cp .env.example .env
```

Fill in:
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `BLOG_BASE_DIR`
- `BLOG_OUTPUT_DIR`

### 3. Bootstrap runtime state
```bash
python3 scripts/bootstrap_runtime_state.py
```

This creates runtime JSON files from the provided templates.

### 4. Run once manually
```bash
bash scripts/run_night_journal.sh
```

### 5. Inspect the system
```bash
python3 scripts/analyze_journal.py
```

## Runtime modes

Controlled through `automation/manual_overrides.json`.

- `auto` — publish immediately
- `review-first` — generate to `draft_review/`
- `manual-only` — block timer-driven publishing

## Review workflow

### Approve a generated draft
```bash
bash scripts/publish_reviewed_post.sh <draft-file>
```

### Discard a generated draft
```bash
bash scripts/discard_review_draft.sh <draft-file>
```

## Deployment

See:
- `docs/deployment.md`
- `docs/architecture.md`
- `docs/review-workflow.md`
- `automation/README-system.md`

## Important note

This repository is a **sanitized project version**. Runtime secrets, live state, logs, generated posts, and instance-specific values should not be committed directly.
