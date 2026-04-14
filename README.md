# 全真夜记

全真夜记是一个围绕“人格、记忆、感知、事件、生成、发布”组织起来的数字生命博客系统。

## 当前结构

- `backend/`：FastAPI Core、任务状态机、记忆/人格/感知/成本/审计/迁移
- `frontend/`：Vue 3 + Vite 管理后台
- `hugo/`：Hugo 配置
- `hugo-builder/`：Hugo Sidecar 入口脚本
- `caddy/`：Caddy 站点与后台网关
- `doc/`：项目总纲、工程实施文档、数据库 Schema

## 本地开发

### 后端

```bash
uv sync --extra dev
uv run uvicorn backend.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 测试

```bash
uv run pytest backend/tests
cd frontend && npm run build
```

## 容器化部署

1. 复制环境变量模板并按生产环境填写：

```bash
cp .env.example .env
```

至少要确认这些键：

- `ENVIRONMENT=production`：生产部署默认按生产模式启动
- `JWT_SECRET`：必须替换成随机长密钥；生产环境下如果仍是默认值，`core` 会拒绝启动
- `DATABASE_URL`：默认 SQLite 即可，生产建议保留到 `/app/data/quanzhen.db`
- `SITE_BASE_URL`：未接域名时填 `http://<服务器IP>:5210`
- `PUBLIC_SERVER_IP`：服务器公网 IP，用于域名诊断与 HTTPS 启用判断
- `ACME_EMAIL`：可选，启用 HTTPS 时建议填写
- `CADDY_RELOAD_ENABLED=true`：允许 Core 在域名配置变更后热重载 Caddy
- `ALLOW_CLOUDFLARE_PROXY_DOMAIN=true`：如果域名走 Cloudflare 代理且使用“完全(严格)”模式，需要显式打开
- `IMPORT_LEGACY_ASSETS=false`：默认禁用旧 MVP 资产自动迁移，避免脏数据污染新人格
- `ALLOW_FAKE_LLM=false`：生产环境不要开假模型

2. 启动容器：

```bash
docker compose up -d --build
```

如果 `JWT_SECRET` 未设置，生产用 `docker compose` 会直接报错并拒绝启动。

默认入口与端口：

- 后台：`http://localhost:5210/admin/`
- 站点：`http://localhost:5210/`
- HTTP：`80`
- HTTPS：`443`

## 生产部署提示

- 系统会在运行时生成 Hugo 配置与 Caddy 配置，并在站点信息变更后自动刷新。
- 域名入口只服务博客静态页；管理后台与 API 明确保留在 `http://<服务器IP>:5210/admin/` 与 `http://<服务器IP>:5210/api/*`。
- 域名默认要求 **DNS 直接解析到 `PUBLIC_SERVER_IP`**；如果域名走 Cloudflare 代理，请同时设置 `ALLOW_CLOUDFLARE_PROXY_DOMAIN=true`。
- Cloudflare 代理模式下，系统会按代理域名生成 HTTPS 站点；但证书签发成功不等于公网一定可用，Cloudflare 仍需要能够回源访问服务器的 `80/443`。
- 目录监控更适合监听宿主机投喂到挂载目录的文件；做自动化投喂时，建议等待服务健康检查通过后再写入文件。
- Ghost 只导出“数字生命数据”，不包含容器镜像、主题目录和 Caddy 证书数据。

## 默认初始化流程

1. 打开 `/admin/setup`
2. 设置管理员密码、站点信息和模型配置
3. 登录后台
4. 在“人格 / 记忆 / 设置”页补齐运行参数
5. 在总览页点击“立即发文”或等待定时任务

## 运行校验

- 后端：`pytest backend/tests`
- 前端：`cd frontend && npm run build`
- 容器：`docker compose up -d --build`
