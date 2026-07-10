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
- [全面审阅报告（2026-07-10）](doc/全面审阅报告-2026-07-10.md)
- [待修复问题清单 P1/P2](doc/待修复问题清单-P1-P2.md)
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
cd frontend && npm run typecheck
cd frontend && npm run lint
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
- `ENCRYPTION_KEY`：推荐设置 Fernet 主密钥（见 `.env.example`）；未设时使用数据库旁 `.encryption_key` 文件
- `ALLOW_FAKE_LLM`：生产必须为 `false`（`ENVIRONMENT=production` 时若为 true 会拒绝启动）

**关于 `:5210` 与博客：** 控制台端口（`Caddyfile` 的 `qz_console`）在 `/admin` 与 `/api` 之外会 fallthrough 到 Hugo 静态目录。若 volume 中已有构建产物，**同一主机上可能读到博客 HTML**。对外公开博客请使用域名站点片段（域名路径对 `/admin`/`/api` 返回 404）。预览主题 qz-ink / `:5211` / `:5212` **不在**默认 compose 中，见 `doc/博客展示页优化方案-预览站.md`（已决定生产保留 PaperMod）。
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
- 目录投喂：仓库内 `./inbox` 默认挂载到后端容器 `/app/inbox`，可在后台“目录监控”页直接监听该路径。

> **域名与博客公开访问**：正式对外博客请配置域名（域名站点不暴露 `/admin`/`/api`）。`:5210` 是管理台网关；其路径 fallthrough 到 Hugo 时，若本机已有静态构建产物，**可能**直接看到博客页，但这不是推荐的公开方式。文章仍会写入 Hugo 内容目录并按信号构建。

## 生产部署提示

- 系统会在运行时生成 Hugo 配置与 Caddy 配置，并在站点信息变更后自动刷新。
- 域名入口只服务博客静态页；管理后台与 API 明确保留在 `http://<服务器IP>:5210/admin/` 与 `http://<服务器IP>:5210/api/*`。
- Docker 部署下后台端口由 `docker-compose.yml` 端口映射控制，生产环境不支持在后台直接改动 `panel.port`。
- 健康检查的外部探测会访问 OpenAI-compatible `/models` 端点；401、403、404 不会被视为可用，只会让系统进入 degraded 状态。
- 默认质量策略会检查目标语言。`qa.required_language=zh` 时，英文漂移内容会进入人工签发。
- 默认质量策略要求第一人称正文。`qa.required_perspective=first_person` 时，命中“你/您”等第二人称叙事会自动重写；重试耗尽时不会发布。
- 正文生成默认 `llm.max_tokens=2400`。如果模型返回 `finish_reason=length/max_tokens`，系统会自动重写；重试耗尽时会失败，不会发布半截文章。
- Caddy admin reload 端口 `2019` 只在 Docker 内部网络开放，`docker-compose.yml` 不发布到宿主机；不要额外映射该端口到公网。
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
- 前端类型与风格：`cd frontend && npm run typecheck && npm run lint`
- 前端构建：`cd frontend && npm run build`
- 烟雾验证：`QZ_PASSWORD='<admin-password>' python3 scripts/smoke_test.py`
- 容器：`docker compose up -d --build`
