#!/bin/sh

set -eu

mkdir -p /runtime

if [ ! -s /runtime/Caddyfile ]; then
  cp /etc/caddy/Caddyfile /runtime/Caddyfile
fi

exec caddy run --config /runtime/Caddyfile --adapter caddyfile
