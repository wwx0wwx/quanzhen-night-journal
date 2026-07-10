#!/usr/bin/env bash
# 使用 qz-ink 主题构建博客预览站（不触碰生产 hugo_public）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${ROOT}/blog-preview/public"
CONTENT_VOL="${CONTENT_VOL:-quanzhen-night-journal_hugo_content}"
HUGO_IMAGE="${HUGO_IMAGE:-hugomods/hugo:exts-0.152.2}"

mkdir -p "${OUT_DIR}"

# 清理旧产物但保留目录
find "${OUT_DIR}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +

echo "[preview] building qz-ink → ${OUT_DIR}"
echo "[preview] content volume: ${CONTENT_VOL}"

docker run --rm \
  -v "${CONTENT_VOL}:/project/content:ro" \
  -v "${ROOT}/themes:/project/themes:ro" \
  -v "${ROOT}/hugo/config.preview.toml:/project/hugo.toml:ro" \
  -v "${ROOT}/hugo/static:/project/static:ro" \
  -v "${ROOT}/archetypes:/project/archetypes:ro" \
  -v "${OUT_DIR}:/project/public" \
  -w /project \
  "${HUGO_IMAGE}" \
  hugo --config /project/hugo.toml --destination /project/public --cleanDestinationDir

# 归档页 / 搜索页：若 content 里 layout 指向 PaperMod 专用 layout，主题已提供同名
echo "[preview] pages:" "$(find "${OUT_DIR}" -name index.html | wc -l)"
echo "[preview] done. Serve with Caddy on :5212 (see caddy/Caddyfile.blog-preview)."
