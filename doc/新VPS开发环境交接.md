# 新 VPS 开发环境交接

> 生成日期：2026-05-04  
> 机器：64.83.41.12  
> 项目路径：`/projectdev/quanzhen-night-journal`

## 1. 当前环境

- 系统：Debian GNU/Linux 13 (trixie)
- Python：3.13.5
- uv：0.11.8，路径 `/root/.local/bin/uv`
- Node.js：v20.19.2
- npm：9.2.0
- Docker：29.4.2
- Docker Compose：v5.1.3
- Git：2.47.3
- GitHub CLI：2.46.0
- ripgrep：14.1.1

本次已安装：`ripgrep`、`nodejs`、`npm`、`gh`、`uv`，并完成项目级依赖安装：

```bash
uv sync --extra dev
cd frontend && npm install
```

## 2. Git 与 GitHub

- 当前分支：`main`
- 当前提交：`3d03892 fix embedding health and markdown QA`
- remote：`https://github.com/wwx0wwx/quanzhen-night-journal`
- Git 身份：
  - `user.name=wwx0wwx`
  - `user.email=3180102784@zju.edu.cn`
- GitHub CLI 状态：尚未登录。
- SSH key 状态：`~/.ssh` 下未发现常见 `id_*` key 文件。

当前可以读取远端：

```bash
git ls-remote --heads origin main
```

后续要启用 push，二选一：

```bash
# 方案 A：使用 GitHub CLI 登录 HTTPS
gh auth login --hostname github.com
gh auth setup-git

# 方案 B：生成 SSH key 并切换 remote
ssh-keygen -t ed25519 -C "3180102784@zju.edu.cn"
cat ~/.ssh/id_ed25519.pub
git remote set-url origin git@github.com:wwx0wwx/quanzhen-night-journal.git
ssh -T git@github.com
```

不要在终端或文档中记录 token、私钥或密码明文。

## 3. 容器与运行态数据

当前 Docker Compose 服务：

- `qz-core`：healthy
- `qz-caddy`：healthy
- `qz-hugo`：running

当前 volumes：

- `quanzhen-night-journal_app_data`
- `quanzhen-night-journal_hugo_content`
- `quanzhen-night-journal_hugo_public`
- `quanzhen-night-journal_caddy_data`
- `quanzhen-night-journal_caddy_config`

生产容器内已复核：

- `ENVIRONMENT=production`
- `SITE_BASE_URL=https://iuaa.de`
- `PUBLIC_SERVER_IP=64.83.41.12`
- `ALLOW_CLOUDFLARE_PROXY_DOMAIN=true`
- SQLite `integrity_check=ok`
- `posts=3`、`personas=1`、`memories=1`、`events=7`

不要删除 Docker volumes。不要覆盖 `.env`。不要暴露 Caddy admin `2019` 到公网。

## 4. 项目架构

全真夜记是一个 AI 人格博客引擎，核心链路是：

```text
事件触发 -> 上下文组装 -> Prompt 构造 -> LLM 生成
-> QA/去重/完整性检查 -> 可选人工签发 -> Hugo 发布 -> Caddy 对外服务
```

主要组件：

- `backend/`：FastAPI Core，负责认证、配置、人格、记忆、感知、事件、任务状态机、生成编排、QA、成本、审计、Ghost 迁移。
- `frontend/`：Vue 3 + Vite 管理后台，入口 `/admin/`。
- `hugo/`、`layouts/`、`themes/`、`archetypes/`：Hugo 静态博客构建输入。
- `hugo-builder/`：sidecar，监听 `/hugo/data/.build_signal`，有信号时运行 Hugo 构建。
- `caddy/`：网关，负责 `80/443` 静态博客、`:5210/admin/` 后台和 `:5210/api/*` API 代理。
- `presets/`：人格预设包。
- `scripts/`：初始化、密钥生成、烟雾测试等辅助脚本。
- `doc/`：项目文档与数据库 schema。

Docker Compose 中：

- `core` 挂载 `app_data`、`hugo_content`、`hugo_public`，并只读挂载 `presets/`、`draft_review/`、`automation/`。
- `hugo-builder` 读取 `hugo_content`，写入 `hugo_public`，读取 `app_data` 中的构建信号和运行时 Hugo 配置。
- `caddy` 只读服务 `hugo_public`，读取 `app_data` 中运行时 Caddyfile，持久化证书和配置到 Caddy volumes。

## 5. 源码、运行态与禁止误删内容

源码和应提交内容：

- `backend/`
- `frontend/src/`、`frontend/*.json`、配置文件
- `caddy/`、`hugo-builder/`
- `hugo/`、`layouts/`、`themes/`、`archetypes/`
- `presets/`、`automation/`
- `content/` 中正式 Hugo 内容
- `doc/`、`scripts/`、`docker-compose.yml`、`.env.example`、`pyproject.toml`、`uv.lock`

本地或运行态内容，不应提交：

- `.env`
- `.venv/`
- `frontend/node_modules/`
- `frontend/dist/`
- `.pytest_cache/`、`__pycache__/`
- 数据库文件、SQLite WAL/SHM、Ghost 导出包、数据库快照
- 运行时生成的 Hugo/Caddy 配置

生产关键数据在 Docker volumes 中，尤其是：

- `app_data`：SQLite 数据库、备份、Ghost 包、运行时 Caddy/Hugo 配置、构建信号。
- `hugo_content`：运行时生成的 Hugo 内容。
- `hugo_public`：Hugo 构建后的静态站点。
- `caddy_data` / `caddy_config`：证书与 Caddy 状态。

## 6. 开发命令

后端：

```bash
uv sync --extra dev
uv run uvicorn backend.main:app --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

容器部署：

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f core
```

烟雾验证：

```bash
QZ_PASSWORD='<admin-password>' python3 scripts/smoke_test.py
```

## 7. 测试结果

本次验证结果：

- `cd frontend && npm run typecheck`：通过。
- `cd frontend && npm run lint`：通过。
- `cd frontend && npm test`：通过，9 个文件、23 个测试。
- `cd frontend && npm run build`：通过。
- `uv run pytest backend/tests`：75 通过，1 失败。

后端失败测试：

```text
backend/tests/test_post_processing.py::test_generation_skips_generic_site_title_heading
IndexError: list index out of range
```

失败现象：测试触发生成后，`/api/posts` 返回的 `items` 为空，测试读取第 0 项时报错。本次按“不修改业务代码”约束未修复。

## 8. 风险点

- 生产站点正在本机容器中运行，开发操作不要随意 `docker compose down -v`、删除 volumes 或覆盖 `.env`。
- `core` 启动会执行数据库初始化、自检、缺失列补齐、异常任务恢复、默认人格修复和运行时站点配置应用。
- SQLite 使用 WAL，备份和恢复前要注意写入一致性；生产恢复通常需要先停 `core`，但执行前应明确确认。
- `SITE_BASE_URL` 当前为 `https://iuaa.de`，域名走 Cloudflare 代理时依赖 `ALLOW_CLOUDFLARE_PROXY_DOMAIN=true`。
- Caddy `2019` admin reload 只应在 Docker 内网使用，不要映射到公网。
- `.ghost` 是逻辑导出，不包含镜像、主题目录、Caddy 证书数据；SQLite 快照才是原始数据库备份。
- 远端 push 尚未配置认证；提交或推送前先完成 `gh auth login` 或 SSH key 配置。
