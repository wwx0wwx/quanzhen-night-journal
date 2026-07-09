#!/bin/sh

set -eu

echo "Hugo builder sidecar started."
mkdir -p /hugo/public /hugo/data
LAST_SIGNAL=""
CONFIG_FILE="/hugo/config.toml"

while true; do
  SIGNAL="$(cat /hugo/data/.build_signal 2>/dev/null || true)"
  if [ -n "$SIGNAL" ] && [ "$SIGNAL" != "$LAST_SIGNAL" ]; then
    echo "[$(date -Iseconds)] Build signal detected: $SIGNAL"
    if [ -f /hugo/data/hugo.toml ]; then
      CONFIG_FILE="/hugo/data/hugo.toml"
    fi
    # Mark as running for this exact signal so publishers do not accept stale ok status.
    printf '{"status":"running","built_at":"%s","signal":"%s"}\n' "$(date -Iseconds)" "$SIGNAL" > /hugo/data/build_status.json
    if hugo --source /hugo --destination /hugo/public --config "$CONFIG_FILE" --cleanDestinationDir; then
      printf '{"status":"ok","built_at":"%s","signal":"%s"}\n' "$(date -Iseconds)" "$SIGNAL" > /hugo/data/build_status.json
    else
      printf '{"status":"error","built_at":"%s","signal":"%s","error":"hugo_build_failed"}\n' "$(date -Iseconds)" "$SIGNAL" > /hugo/data/build_status.json
    fi
    LAST_SIGNAL="$SIGNAL"
  fi
  sleep 2
done
