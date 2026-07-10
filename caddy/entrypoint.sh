#!/bin/sh

set -eu

mkdir -p /runtime

IMAGE_CADDYFILE=/etc/caddy/Caddyfile
RUNTIME_CADDYFILE=/runtime/Caddyfile
STAMP_FILE=/runtime/.caddyfile_image_stamp

# Refresh runtime Caddyfile when the image copy changes (content hash),
# while still allowing operators to pin a custom file via
# CADDYFILE_PIN=1 (never overwrite runtime).
if [ "${CADDYFILE_PIN:-0}" = "1" ]; then
  if [ ! -s "$RUNTIME_CADDYFILE" ]; then
    cp "$IMAGE_CADDYFILE" "$RUNTIME_CADDYFILE"
  fi
else
  image_hash="$(cksum "$IMAGE_CADDYFILE" | awk '{print $1" "$2}')"
  prev_hash=""
  if [ -f "$STAMP_FILE" ]; then
    prev_hash="$(cat "$STAMP_FILE")"
  fi
  if [ ! -s "$RUNTIME_CADDYFILE" ] || [ "$image_hash" != "$prev_hash" ]; then
    cp "$IMAGE_CADDYFILE" "$RUNTIME_CADDYFILE"
    printf '%s\n' "$image_hash" > "$STAMP_FILE"
  fi
fi

exec caddy run --config "$RUNTIME_CADDYFILE" --adapter caddyfile
