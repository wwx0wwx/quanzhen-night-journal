# 全真夜记

> **Night Journal** — an AI persona blogging engine.
>
> [English Documentation](README.en.md) · [Live Demo](https://iuaa.de)
>
> Define a persona (identity, worldview, language style, scene pool, memory seeds),
> plug in any OpenAI-compatible LLM, and let the system automatically generate,
> QA-check, and publish blog posts via Hugo. Ships with one preset (“全真”),
> but any worldview — cyberpunk, slice-of-life, workplace — can be loaded as a
> JSON preset pack under `presets/`.
>
> **Stack:** FastAPI · SQLite · Vue 3 · Hugo · Caddy · Docker Compose

全真夜记是一个围绕”人格、记忆、感知、事件、生成、发布”组织起来的 AI 人格博客引擎。

## 文档入口

- [项目总纲](doc/项目总纲.md)
- [工程实施文档](doc/工程实施文档.md)
- [数据库 Schema](doc/database_schema.sql)
- [数据库升级与备份](doc/database_migration.md)
- [贡献指南](CONTRIBUTING.md)
- [更新日志](CHANGELOG.md)

## 架构

```text
                  ┌──────────────────────────────────────────────────┐
                  │                  Docker Compose                  │
                  │                                                  │
 Browser ────────▶│  ┌────────────────────────────────────────────┐  │
 (读者)    :80/443│  │              Caddy (Gateway)               │  │
                  │  │                                            │  │
 Browser ────────▶│  │  :5210/admin/* ──▶ Vue 3 SPA (静态文件)    │  │
 (管理员)   :5210 │  │  :5210/api/*   ──┐                        │  │
                  │  │  :80/:443      ──│── Hugo 静态博客         │  │
                  │  └──────────────────│─────────────────────────┘  │
                  │                     │                            │
                  │                     ▼                            │
                  │  ┌────────────────────────────────────────────┐  │
                  │  │          FastAPI Core (:8000)              │  │
                  │  │                                            │  │
                  │  │  ┌──────────────┐  ┌───────────────────┐  │  │
                  │  │  │ Persona Eng. │  │ Generation Orch.  │  │  │
                  │  │  │ Memory Eng.  │  │ Prompt Builder    │  │  │
                  │  │  │ Sensory Eng. │  │ QA Engine         │  │  │
                  │  │  │ Event Engine │  │ Cost Monitor      │  │  │
                  │  │  └──────────────┘  └───────────────────┘  │  │
                  │  │           │                │               │  │
                  │  │     SQLite DB     LLM / Embedding API     │  │
                  │  └────────────────────────────────────────────┘  │
                  │                     │ build signal               │
                  │                     ▼                            │
                  │  ┌────────────────────────────────────────────┐  │
                  │  │        Hugo Builder (Sidecar)              │  │
                  │  │  监听信号 → 重新生成静态站点 → /srv/hugo   │  │
                  │  └────────────────────────────────────────────┘  │
                  └──────────────────────────────────────────────────┘
```

## 当前结构

- `backend/`：FastAPI Core、任务状态机、记忆/人格/感知/成本/审计/迁移
- `frontend/`：Vue 3 + Vite 管理后台（含关于页、可视化调度选择器）
- `presets/`：人格预设包（JSON 定义 + 种子记忆 + 种子博文）
- `content/`：Hugo 站点内容（运行时生成）
- `hugo/`：Hugo 配置
- `hugo-builder/`：Hugo Sidecar 入口脚本
- `caddy/`：Caddy 站点与后台网关
- `doc/`：项目总纲、工程实施文档、数据库 Schema
- `scripts/`：初始化、加密密钥、烟雾测试等辅助脚本

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
cd frontend && npm test
cd frontend && npm run build
```

如需做部署后烟雾验证，可运行：

```bash
QZ_PASSWORD='<admin-password>' python3 scripts/smoke_test.py
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
- `SITE_BASE_URL`：未接域名时填 `http://<服务器IP>:5210`（此时仅后台可用，博客需配置域名后才公开）
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
- HTTP：`80`
- HTTPS：`443`

> **域名与博客公开访问**：未配置域名时，`:5210` 端口仅提供后台管理和 API；博客公开入口需要配置域名后才会启用。文章仍可正常生成、预览和写入 Hugo 内容目录，但不承诺通过 IP 直接访问博客首页。

## 生产部署提示

- 系统会在运行时生成 Hugo 配置与 Caddy 配置，并在站点信息变更后自动刷新。
- 域名入口只服务博客静态页；管理后台与 API 明确保留在 `http://<服务器IP>:5210/admin/` 与 `http://<服务器IP>:5210/api/*`。
- 域名默认要求 **DNS 直接解析到 `PUBLIC_SERVER_IP`**；如果域名走 Cloudflare 代理，请同时设置 `ALLOW_CLOUDFLARE_PROXY_DOMAIN=true`。
- Cloudflare 代理模式下，系统会按代理域名生成 HTTPS 站点；但证书签发成功不等于公网一定可用，Cloudflare 仍需要能够回源访问服务器的 `80/443`。
- 目录监控更适合监听宿主机投喂到挂载目录的文件；做自动化投喂时，建议等待服务健康检查通过后再写入文件。
- Ghost 只导出“数字生命数据”，不包含容器镜像、主题目录和 Caddy 证书数据。
- 数据库快照是原始 SQLite 备份，适合快速回滚运行态，不替代 `.ghost` 逻辑导出。

## 仓库清理约定

- 仓库只跟踪源码、正式文档、必要脚本和正式站点内容。
- `__pycache__/`、`.pytest_cache/`、`frontend/dist/`、`node_modules/`、数据库、Ghost 导出包、数据库快照、运行时 Hugo/Caddy 配置都应留在本地或服务器，不进入 Git。
- 当前后端与前端测试源码属于有效回归资产，不按“临时测试文件”处理。

## 默认初始化流程

1. 打开 `/admin/setup`
2. 设置管理员密码、站点信息和模型配置
3. 登录后台
4. 在“人格 / 记忆 / 设置”页补齐运行参数
5. 在总览页点击“立即发文”或等待定时任务

## 运行校验

- 后端：`pytest backend/tests`
- 前端测试：`cd frontend && npm test`
- 前端：`cd frontend && npm run build`
- 烟雾验证：`QZ_PASSWORD='<admin-password>' python3 scripts/smoke_test.py`
- 容器：`docker compose up -d --build`
