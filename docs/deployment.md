# Deployment Notes

## Required environment variables

Copy `.env.example` to `.env` and fill:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `BLOG_BASE_DIR`
- `BLOG_OUTPUT_DIR`

## Runtime state files

The engine expects these runtime files to exist under `automation/`:

- `world_state.json`
- `recent_memories.json`
- `night_journal_stats.json`
- `manual_overrides.json`

Initialize them from the provided `*.example.json` files.

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
