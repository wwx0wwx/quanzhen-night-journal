# 管理后台 v2（预览）

浅色默认、左侧栏、干净 SaaS 风格的管理后台重构版。

- **预览地址**：`http://<服务器IP>:5211/admin/`
- **原版后台**：`http://<服务器IP>:5210/admin/`（保持不变，互不影响）
- **共用 API**：两套前端都走同一套后端 `/api`

## 本地开发

```bash
cd frontend-v2
npm ci
npm run dev
```

## 构建

```bash
npm run build
```

## 启动 5211 预览（Docker）

```bash
docker rm -f qz-admin-v2-preview 2>/dev/null || true
docker run -d \
  --name qz-admin-v2-preview \
  --network quanzhen-night-journal_default \
  -p 5211:5211 \
  -v "$(pwd)/dist:/srv/webui:ro" \
  -v "$(pwd)/../caddy/Caddyfile.preview:/etc/caddy/Caddyfile:ro" \
  caddy:2-alpine \
  caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
```

验收通过后再把正式部署从 `frontend/` 切到 `frontend-v2/`（需改 Caddy 构建与端口策略）。
