#!/bin/sh

set -eu

mkdir -p /runtime

cp /etc/caddy/Caddyfile /runtime/Caddyfile

exec caddy run --config /runtime/Caddyfile --adapter caddyfile
