# Agent / Codex Collaboration Rules

This file defines persistent repository-level instructions for agents working on this project.

## Git Commit Policy

- Every time you change the repository, create a Git commit before finishing the task, unless the user explicitly says not to commit.
- Keep every codebase change rollbackable.
- Do not push commits unless the user explicitly asks for a push.
- Do not rewrite history, reset branches, or discard user changes unless the user explicitly requests that operation.
- If tests cannot be run or fail, still commit the requested change when appropriate, and mention the verification result clearly in the final response.

## Product Invariants

1. **Single worker**: Core assumes one uvicorn/process. `TASK_GATE`, rate limits, and publish locks are in-process. Do not scale horizontally without redesign.
2. **Production blog theme is PaperMod**. `themes/qz-ink` and ports 5211/5212 are preview-only; do not cut production over to qz-ink without an explicit product decision.
3. **Do not serve experimental preview as truth**: keep `blog-preview/` and ad-hoc Caddy preview configs out of the default `docker-compose.yml` path unless documenting them as optional.
4. **Secrets**: Prefer `ENCRYPTION_KEY` env; never re-introduce plaintext master keys into `system_config` for new installs. Never commit `.env` or `.encryption_key`.
5. **Fake LLM**: Forbidden when `ENVIRONMENT=production`.
6. **Generation QA**: length / title uniqueness / opening fingerprint / integrity are hard paths — do not weaken without product sign-off.
7. **Admin UI i18n**: new user-visible strings need `zh-CN` + `en` keys; avoid new hard-coded Chinese in views.
8. **Orchestrator wiring**: use `backend.engine.runtime_factory.build_generation_runtime` for API/scheduler/folder_monitor so narrative `config_store` cannot drift again.

## Verification (before claiming done)

```bash
uv run ruff check backend/
uv run pytest backend/tests -q
cd frontend && npm run lint && npm run typecheck && npm test
```
