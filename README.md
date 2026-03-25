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

## 開鍙戞敞鎰?
### Hugo 鐞?杞?鐗堟湰瑕佹??
- 鐞?璁?Hugo 鐞?杞?鐗堟湰 `>= 0.146.0` (濡傛灉浣跨敤 PaperMod 涓昏?)
- 涓存椂鏂规??: 鐞?璁?绠€鏄?Markdown 杈? HTML 杈?杞?鎹?鏂规?案
- 鐞?璁?Hugo 開鍙戦?椤?锛?https://gohugo.io/getting-started/installing/

### 開鍙戞?у?ц?烘??
1. **API 杈?杩涙?у?ц?烘??**
   - 鐞?璁?API 鐞?瑕?瀵嗛挜
   - 鐞?璁?API 缁?鐐?绔?鍙?
   - 鐞?璁?API 杈?杩涘拰瀹㈡?绔?璇锋眰鏍煎紡

2. **Nginx 開鍙戞?у?ц?烘??**
   - 鐞?璁?闈?椤甸潤鎬佸瓨鍌ㄧ洰褰?鏉冮檺
   - 鐞?璁?Nginx 開鍙戦厤缃?鏂囦欢
   - 鐞?璁?鍩熷悕瑙ｆ瀽鏄?鍚﹂?舵椂

3. **SSL 瀵?璇?璁剧疆**
   - 鐞?璁?Let's Encrypt 瀵?璇佽?宠?璁剧疆
   - 鐞?璁?HTTPS 杈?杩涘姞杞?

4. **鏂囦欢缂栫爜璁剧疆**
   - 鐞?璁?UTF-8 缂栫爜璁剧疆
   - 鐞?璁?HTML 涓?娣?娣诲姞 `<meta charset="utf-8" />` 鐞?瑕?

### 開鍙戝?у??
- 鐞?璁?DEPLOY_GUIDE.md 鐞?瑕?淇℃伅
- 鐞?璁?HUGO_TROUBLESHOOTING.md 鐞?瑕?淇℃伅
- 鐞?璁?鍙戠敓鍗曟?у?ц?烘??
