#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <domain>"
  exit 1
fi

DOMAIN="$1"
SITE_ROOT="/var/www/${DOMAIN}"
ENGINE_ROOT="/opt/blog-src"
HUGO_VER="0.147.0"

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y git nginx python3 python3-venv python3-pip certbot python3-certbot-nginx rsync curl jq unzip

if ! command -v hugo >/dev/null 2>&1; then
  curl -L "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VER}/hugo_extended_${HUGO_VER}_linux-amd64.tar.gz" -o /tmp/hugo.tgz
  tar -xzf /tmp/hugo.tgz -C /tmp
  install -m 0755 /tmp/hugo /usr/local/bin/hugo
fi

mkdir -p "${SITE_ROOT}" "${ENGINE_ROOT}/logs" "${ENGINE_ROOT}/draft_review" "${ENGINE_ROOT}/automation/backups"

if [[ ! -f "${ENGINE_ROOT}/.env" ]]; then
  echo "[!] ${ENGINE_ROOT}/.env not found"
  echo "    Copy .env.example to .env and fill real values first."
  exit 1
fi

cp "${ENGINE_ROOT}/automation/night-journal.service" /etc/systemd/system/night-journal.service
cp "${ENGINE_ROOT}/automation/night-journal.timer" /etc/systemd/system/night-journal.timer
systemctl daemon-reload
systemctl enable --now night-journal.timer

cat > "/etc/nginx/sites-available/${DOMAIN}" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};
    root ${SITE_ROOT};
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

ln -sf "/etc/nginx/sites-available/${DOMAIN}" "/etc/nginx/sites-enabled/${DOMAIN}"
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable --now nginx
systemctl reload nginx

cd "${ENGINE_ROOT}"
hugo --destination "${SITE_ROOT}"

echo
printf '%s\n' "[ok] Bootstrap complete for ${DOMAIN}"
printf '%s\n' "[next] If DNS is ready, enable HTTPS with:"
printf 'certbot --nginx -d %s -d www.%s --non-interactive --agree-tos -m admin@%s --redirect\n' "${DOMAIN}" "${DOMAIN}" "${DOMAIN}"
