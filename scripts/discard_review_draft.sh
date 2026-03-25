#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="${BLOG_BASE_DIR:-/opt/blog-src}"
DRAFT_DIR="$BASE_DIR/draft_review"
TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 <draft-file>"
  exit 1
fi

if [[ ! -f "$TARGET" ]]; then
  if [[ -f "$DRAFT_DIR/$TARGET" ]]; then
    TARGET="$DRAFT_DIR/$TARGET"
  else
    echo "Draft not found: $TARGET"
    exit 1
  fi
fi

rm -f "$TARGET"
echo "Discarded: $(basename "$TARGET")"
