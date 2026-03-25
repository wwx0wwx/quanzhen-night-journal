# Deployment Notes

## Required environment variables

Copy `.env.example` to `.env` and fill:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `BLOG_BASE_DIR`
- `BLOG_OUTPUT_DIR`

## Runtime state files

Initialize runtime files from templates:

```bash
python3 scripts/bootstrap_runtime_state.py
```

This creates:
- `automation/world_state.json`
- `automation/recent_memories.json`
- `automation/night_journal_stats.json`
- `automation/manual_overrides.json`
- `automation/memory_anchors.json`
- `automation/future_fragments.json`
- `automation/topic_rules.json`

## Manual run

```bash
bash scripts/run_night_journal.sh
```

## Analyze output

```bash
python3 scripts/analyze_journal.py
```

## Systemd

Install templates:

```bash
install -m 0644 automation/night-journal.service /etc/systemd/system/night-journal.service
install -m 0644 automation/night-journal.timer /etc/systemd/system/night-journal.timer
systemctl daemon-reload
systemctl enable --now night-journal.timer
```

## Review mode

Switch `automation/manual_overrides.json` to `review-first` if you want drafts written to `draft_review/` instead of immediate publishing.
