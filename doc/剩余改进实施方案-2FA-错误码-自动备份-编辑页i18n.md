# 管理后台剩余四点 — 实施方案（给 Codex 执行）

> **状态**：待执行  
> **基准版本**：`main` @ `31ded1f` 之后（前端约 v1.2.0，后台 UI 已中英切换 + Toast/签发队列）  
> **目标读者**：Codex / 自动化 coding agent  
> **约束**：默认小步提交；可测；不破坏现有 5210 部署与 API 契约（除非本方案明确写「破坏性变更」）  
> **仓库路径**：`/projectdev/quanzhen-night-journal`  
> **线上后台**：`http://<IP>:5210/admin/`（域名站点不开放 `/admin`）

---

## 0. 总览

| # | 主题 | 优先级 | 建议工期 | 主要触达 |
|---|------|--------|----------|----------|
| A | 管理员 2FA（TOTP） | P1 安全 | 1.5–2 天 | `backend/security`, `backend/api/auth.py`, `frontend` 登录/设置 |
| B | 错误码统一（前后端共享词典） | P1 可维护 | 1–1.5 天 | `backend/utils/response.py` + 全 API；`frontend/src/utils/errors.ts` + i18n |
| C | 自动备份产品化 | P1 运维 | 1–1.5 天 | `backend/scheduler` + `ghost` API + 设置 + 备份页 |
| D | PersonaEdit / PostEdit 全量 i18n | P2 体验 | 0.5–1 天 | `frontend/src/views/PersonaEdit.vue`, `PostEdit.vue` + locales |

**推荐执行顺序：B → A → C → D**  
理由：B 为 A/C 的错误提示与审计铺路；A 独立安全能力；C 依赖调度与配置；D 纯前端可最后收口。

**完成定义（整体）**

- [ ] 四点均有单测/烟雾测试
- [ ] `frontend`：`npm test` + `npm run build` 通过
- [ ] `backend`：相关 pytest 通过
- [ ] `docker compose build caddy`（及需要时 `core`）后 5210 后台可用
- [ ] `CHANGELOG.md` 更新，`git commit` + `git push origin main`
- [ ] 文档内「回滚」步骤可执行

---

## 1. 公共约定（执行时遵守）

### 1.1 代码风格

- 后端：现有 FastAPI + SQLAlchemy async + `success()` / `error()` 封装（见 `backend/utils/response.py`）
- 前端：Vue 3 + Pinia + vue-i18n（`src/i18n/`），文案走 `t('key')`，默认 `zh-CN`
- 危险操作：用现有 `confirmAction` + Toast（`stores/toast.ts`）
- 不要引入过重 UI 框架

### 1.2 配置与密钥

- 新增配置优先走 `ConfigStore` / settings schema（可后台改的）或 env（部署级）
- 密钥类字段：`type: 'secret'`，遮罩 `******`
- 2FA secret 必须加密落库（复用 `backend/security/encryption.py` 能力）

### 1.3 测试与部署

```bash
# 后端
cd /projectdev/quanzhen-night-journal
# 使用项目既有 venv/uv 方式运行 pytest
.venv/bin/pytest backend/tests -q   # 或项目惯用命令

# 前端
cd frontend && npm test && npm run build

# 仅 UI 变更
docker compose build caddy && docker compose up -d caddy

# 含 core 变更
docker compose build core caddy && docker compose up -d core caddy
```

### 1.4 提交粒度

每个主题至少 1 个 commit（可拆多个），message 用完整句子说明 why。推送前本地验证通过。

---

## A. 管理员 2FA（TOTP）

### A.1 目标

为**唯一管理员账号**（当前 `admin`）提供可选 TOTP 二次验证：

- 设置页可「启用 / 禁用」2FA
- 启用流程：展示二维码 + 手动密钥 → 输入 6 位码确认绑定
- 登录：密码正确后若已启用 2FA，进入第二步输入 OTP
- 支持一次性**恢复码**（备用，单次使用）
- **默认关闭**；不强制已有部署立刻启用

非目标（本期不做）：多用户、WebAuthn、短信 OTP、邮件 OTP。

### A.2 数据模型

在用户表（或等价存储）增加字段（名称可按现有 entities 调整）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `totp_enabled` | bool | 是否启用 |
| `totp_secret_enc` | text/null | 加密后的 base32 secret |
| `totp_confirmed_at` | datetime/null | 确认绑定时间 |
| `recovery_codes_hash` | text/null | JSON 数组，存恢复码哈希（bcrypt/argon2 或 sha256+pepper） |

若当前 `users` 表字段少，用 Alembic/项目既有迁移方式；SQLite 可 `ALTER TABLE` 或文档中的 migration 流程。

**迁移注意**：已有生产库要可空默认 `totp_enabled=false`。

### A.3 API 设计

前缀建议：`/api/auth/...`（均需登录，除登录第二步）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/auth/2fa/status` | `{ enabled, confirmed }` 不回传 secret |
| POST | `/auth/2fa/setup` | 生成 secret，返回 `{ otpauth_url, secret, recovery_codes[] }`（恢复码仅此一次明文） |
| POST | `/auth/2fa/confirm` | body `{ code }` 验证后 `totp_enabled=true` |
| POST | `/auth/2fa/disable` | body `{ password, code? }` 关闭并清空 secret |
| POST | `/auth/login` | **扩展**：若密码对且 2FA 开，返回 `{ requires_2fa: true, pre_auth_token }` 而非完整 session |
| POST | `/auth/login/2fa` | body `{ pre_auth_token, code }` 或 `{ pre_auth_token, recovery_code }` 发正式 cookie/JWT |

`pre_auth_token`：短时（如 5 分钟）签名 token，只表示「密码已通过」，不可访问业务 API。

### A.4 后端实现要点

1. 依赖：`pyotp`（TOTP）、可选 `qrcode` 仅前端生成二维码则后端只返 `otpauth_url`
2. Issuer 名称：站点标题或固定 `Quanzhen Night Journal`
3. 验证窗口：`valid_window=1`
4. 恢复码：生成 8–10 个，展示一次；校验后删除该码
5. 审计：`auth.2fa.setup` / `confirm` / `disable` / `login_2fa_ok` / `login_2fa_fail`
6. 限流：复用 `middleware/rate_limit.py`，2FA 失败与登录同级限流

### A.5 前端实现要点

1. **登录页** `Login.vue`  
   - 两步 UI：密码 → OTP  
   - 状态机：`password | otp`  
   - 支持「使用恢复码」切换输入框  

2. **设置页**（安全区块，简单模式也要露出）  
   - 未启用：按钮「启用两步验证」→ 弹层展示 QR（可用 `otpauth_url` + 前端库或 `https://api.qrserver.com` **不推荐生产依赖外网**；优先本地 `qrcode` 包生成 data URL，或只展示 secret 手动添加）  
   - 输入验证码确认  
   - 已启用：显示状态 +「关闭 2FA」（需密码）  

3. i18n：`zh-CN` / `en` 增加 `twofa.*` 键  

4. 文案原则：面向小白——「手机验证器 App（如 Google Authenticator）」

### A.6 测试

- 后端：setup → 错误码拒绝 → 正确码 confirm → login 两步成功；错误 OTP 失败；恢复码一次性  
- 前端：登录两步表单渲染；设置页状态切换（可用 mock API）

### A.7 验收

- [ ] 未启用时登录行为与现在一致  
- [ ] 启用后仅密码不能进后台  
- [ ] 关闭 2FA 后恢复单因素登录  
- [ ] 恢复码可用且用后失效  
- [ ] 审计日志有记录  

### A.8 回滚

- Feature flag 或配置 `auth.totp_enabled_global=false` 强制忽略 2FA（紧急）  
- 数据库字段可保留；代码回退上一 commit  

---

## B. 错误码统一（前后端共享词典）

### B.1 目标

统一业务错误形态，使前端 i18n 与后端日志一致：

```json
{
  "code": 2001,
  "message": "not_authenticated",
  "message_key": "errors.raw.not_authenticated",
  "data": null
}
```

- `message`：稳定 **机器可读** snake_case（或保留兼容旧中文一段时间）  
- `message_key`：前端 `t(message_key)` 主键  
- 数字 `code`：沿用现有分段（1xxx 参数、2xxx 鉴权、3xxx 初始化、4xxx 发布…）

### B.2 现状问题

- `frontend/src/utils/errors.ts` 与后端各处硬编码中文/`error()` 调用不一致  
- 任务 `error_code` 字符串（如 `invalid_model_output`）与 HTTP API `code` 数字两套体系  
- 部分接口 `HTTPException(detail="snake")`，部分 `error(1002, "中文")`

### B.3 目标架构

```
backend/utils/error_catalog.py   # 单一事实来源：code + key + default_zh
frontend/src/i18n/...            # errors.* 与 catalog key 对齐
frontend/src/utils/errors.ts     # 优先 message_key → code → raw message map
```

**Catalog 示例结构：**

```python
ERRORS = {
    "not_authenticated": {"http": 401, "code": 2001, "key": "errors.raw.not_authenticated"},
    "not_found": {"http": 404, "code": 1002, "key": "errors.codes.1002"},
    "validation_error": {"http": 400, "code": 1001, "key": "errors.codes.1001"},
    # task-level
    "invalid_model_output": {"http": 400, "code": 4101, "key": "errors.labels.invalid_model_output"},
}
```

封装：

```python
def fail(error_id: str, *, data=None, status_code=None):
    meta = ERRORS[error_id]
    return error(
        meta["code"],
        error_id,  # message 机器可读
        status_code=status_code or meta["http"],
        data={**(data or {}), "message_key": meta["key"]},
    )
```

或扩展 `error()` 增加 `message_key=` 参数，**推荐扩展现有函数**减少大面积改签名。

### B.4 迁移策略（兼容）

1. **Phase B1**：扩展响应，增加 `message_key`（或放在 `data.message_key`），`message` 暂保持现状  
2. **Phase B2**：前端 `describeError` 优先 `message_key` / `data.message_key`  
3. **Phase B3**：新代码只用 catalog；旧中文 `message` 仍可被 `RAW_MESSAGE_MAP` 兜底  
4. **Phase B4**（可选）：`message` 全面改为 snake_case（需通告，可能影响外部脚本）

本期建议完成 **B1–B3**，B4 仅改新增/高频路径。

### B.5 任务级 error_code

`task.error_code` 已是 snake_case：在 catalog 中登记，前端已有 `errors.labels.*`，补全缺失项并对齐命名。

Dashboard attention `label` 若直接塞 `error_code`，保持不变，仅保证 i18n 有键。

### B.6 测试

- 单元测试：每个 catalog 条目有 `key`，前端 locale `zh-CN`/`en` 都存在该 key（可写脚本校验）  
- API 测试：故意触发 401/404，断言 body 含 `message_key`  
- `npm test` 中 `errors.test.js` 更新

### B.7 验收

- [ ] 登录失败、未初始化、发布失败等主路径前端显示翻译后的人话  
- [ ] 切换 EN 后错误提示为英文  
- [ ] 旧客户端仅读 `message` 仍不白屏（兼容）  

### B.8 回滚

仅回退 `error()` 与 `describeError` 相关 commit；catalog 文件可保留无害。

---

## C. 自动备份产品化

### C.1 目标

站长无需记手动操作，也能获得：

1. **按计划自动**数据库快照（复用现有 `GhostManager.backup_database`）  
2. **保留最近 N 份**，自动 prune  
3. 设置页可开关与配置  
4. 备份页展示「下次备份时间 / 最近自动备份」  
5. 失败写审计 + 可选通知 webhook（若 `notify.enabled`）

可选增强（时间够再做）：每周自动导出完整 `.ghost` 搬家包（体积大，默认关）。

### C.2 配置项（settings schema）

建议放入 **简单模式可见** 的「运行与安全」或新建 `backup` section：

| key | 类型 | 默认 | 说明 |
|-----|------|------|------|
| `backup.auto_enabled` | boolean | `false` | 是否启用自动 DB 备份 |
| `backup.auto_cron` | schedule | `0 3 * * *` | 每天 03:00（与现有 cron 组件一致） |
| `backup.keep_count` | number | `7` | 保留份数（1–30） |
| `backup.include_ghost_weekly` | boolean | `false` | 是否每周额外打完整包 |
| `backup.ghost_weekly_cron` | schedule | `0 4 * * 0` | 仅当上一开关为 true |

`settingsSchema.js` + i18n `settingsFields.*` + `settingsSchema.sections.backup`。

### C.3 后端

1. **调度**  
   - 在 `backend/scheduler/jobs.py` / `scheduler.py` 注册 job  
   - 配置变更时 reschedule（参考现有 review/decay cron 热更新模式）  

2. **Job 逻辑** `run_auto_database_backup()`  
   - 调用现有 backup  
   - prune keep_count  
   - `log_audit(..., "backup.auto", ...)`  
   - 失败：`notify` 若开启则推送  

3. **API**（可挂在 ghost 路由）  
   - `GET /api/ghost/backup-policy` 或并入 `/api/config` 即可  
   - `GET /api/ghost/backup-status` → `{ last_auto_at, last_auto_ok, next_run_at, recent: [...] }`  

4. **与手动备份共存**：同一目录 `data/backups/`，文件名带 `auto-` 前缀便于识别

### C.4 前端

1. **设置页**：backup section（简单模式显示开关 + 时间 + 保留份数）  
2. **备份与迁移页 `Ghost.vue`**  
   - 顶部卡片：「自动备份：开/关 · 下次：… · 最近：…」  
   - 列表标记 `自动` / `手动`  
3. Toast：手动备份成功已有；自动失败仅审计/通知  

### C.5 测试

- 单元：job 调用 backup + prune（mock filesystem）  
- 配置关闭时 job no-op  
- keep_count=2 时只留 2 个 `auto-` 文件  

### C.6 验收

- [ ] 打开开关并设 cron 后，调度器 job 列表可见（或日志可见注册）  
- [ ] 手动触发 job 函数可生成 `auto-*.db` 并 prune  
- [ ] 关闭开关后不再新增 auto 备份  
- [ ] 设置项中英切换正常  

### C.7 回滚

`backup.auto_enabled=false` 或回退 scheduler 注册；已有备份文件保留。

### C.8 磁盘与安全注意

- 备份目录在 volume 内，文档说明磁盘占用 ≈ `keep_count * db_size`  
- 下载接口已有路径穿越防护，保持  
- 不要把备份目录暴露到公网域名

---

## D. PersonaEdit / PostEdit 全量 i18n

### D.1 目标

`PersonaEdit.vue`、`PostEdit.vue` 中所有用户可见字符串进入 vue-i18n，**无硬编码中文/英文**（调试 log 除外）。

含：

- 页头标题/说明  
- Tab 名、表单 label、placeholder、help  
- 按钮、空状态、确认框、Toast  
- 结构篇幅选项、场景/禁忌/词典相关提示  
- 预览区辅助文案  

### D.2 方法（避免漏网）

1. 扫描：

```bash
cd frontend
rg -n "[\u4e00-\u9fff]" src/views/PersonaEdit.vue src/views/PostEdit.vue
```

2. 在 `src/i18n/locales/zh-CN.ts` / `en.ts` 增加命名空间：

```
personaEdit.*
postEdit.*
```

建议结构：

```
personaEdit.tabs.basic | personality | scenes | advanced
personaEdit.fields.name | description | system_prompt | ...
personaEdit.actions.save | setDefault | delete
postEdit.fields.title | slug | summary | body
postEdit.actions.save | publish | unpublish | ...
```

3. 模板全部 `t('...')`；`script` 中 `message.value = '...'` 改为 `t(...)`  
4. `confirmAction` / `toast` 文案走 i18n  
5. 与设置字段相同：若有 options 数组，用 `t` 生成 computed options

### D.3 关联文件

- `src/utils/personaTemplates.ts`：模板名/描述若展示给用户，一并 i18n  
- 测试：`MemoriesPersonaEdit.test.js`、`PostEdit.test.js` 中断言改为 `i18n` 默认中文文案或改用 key 不敏感匹配  

### D.4 验收

- [ ] 上述 `rg` 中文扫描仅命中注释或测试数据（理想为 0）  
- [ ] 中/EN 切换后两页无中文残留（EN 下）  
- [ ] `npm test` 通过  

### D.5 回滚

纯前端，回退 commit 即可。

---

## 2. 跨任务依赖与风险

| 风险 | 缓解 |
|------|------|
| 2FA 启用后用户丢 OTP 无法登录 | 恢复码 + 文档紧急关 2FA SQL/脚本（见下） |
| 错误码改 message 破坏脚本 | B 期保持兼容；机器码放 `message` 时先双写 |
| 自动备份撑满磁盘 | keep_count 上限 30；状态页显示体积 |
| i18n 漏翻 | rg 扫描 + CI 可选 |

### 紧急关闭 2FA（运维脚本思路）

```sql
-- 表名/字段以实际 migration 为准
UPDATE users SET totp_enabled=0, totp_secret_enc=NULL, recovery_codes_hash=NULL WHERE username='admin';
```

或提供 `python -m backend.tools.disable_2fa` 管理命令。

---

## 3. 建议的 PR / Commit 切分

| Commit | 内容 |
|--------|------|
| 1 | `error_catalog` + `error()` 扩展 + 前端 describeError |
| 2 | 高频 API 接入 catalog + 测试 |
| 3 | 2FA 数据模型 + API + 测试 |
| 4 | 2FA 前端登录/设置 + i18n |
| 5 | 自动备份 job + config + API |
| 6 | 备份页/设置 UI |
| 7 | PersonaEdit/PostEdit 全量 i18n |
| 8 | CHANGELOG + 版本号 + 部署验证 |

版本号建议：功能合入后 `1.3.0`（含 2FA/备份）或分 `1.2.x` 小版本。

---

## 4. Codex 执行清单（复制即用）

```text
你在 /projectdev/quanzhen-night-journal 工作。
按 doc/剩余改进实施方案-2FA-错误码-自动备份-编辑页i18n.md 执行，顺序 B → A → C → D。

要求：
1. 每个主题可测、可回滚；优先扩展现有 error()/ConfigStore/scheduler/ghost，勿重造轮子。
2. 前端文案走 vue-i18n，默认 zh-CN。
3. 每完成一主题：跑相关测试；需要时 docker compose build/up 对应服务。
4. 全部完成后更新 CHANGELOG，commit 并 git push origin main（SSH deploy key 已配置）。
5. 不要把 .env 或密钥写进仓库。
6. 2FA 必须支持恢复码与紧急关闭路径。
7. 错误码迁移保持 API 兼容（增加 message_key，不随意删字段）。
```

---

## 5. 验收总表（交付时勾选）

| 项 | 验收标准 | 完成 |
|----|----------|------|
| B 错误码 | 主路径响应含可翻译 key；中英切换正确 | ☐ |
| A 2FA | 可选启用；登录两步；恢复码；审计 | ☐ |
| C 自动备份 | 开关+cron+保留 N；状态可见；prune | ☐ |
| D 编辑页 i18n | PersonaEdit/PostEdit 无用户可见硬编码中文 | ☐ |
| 质量 | 前后端测试绿；5210 可登录 | ☐ |
| 发布 | CHANGELOG + push GitHub | ☐ |

---

## 6. 参考文件地图

```
backend/api/auth.py
backend/api/ghost.py
backend/security/auth.py
backend/security/encryption.py
backend/scheduler/jobs.py
backend/scheduler/scheduler.py
backend/utils/response.py
backend/models/entities.py
frontend/src/utils/errors.ts
frontend/src/i18n/locales/{zh-CN,en}.ts
frontend/src/views/{Login,Settings,Ghost,PersonaEdit,PostEdit}.vue
frontend/src/config/settingsSchema.js
frontend/src/composables/useConfirm.ts
frontend/src/stores/toast.ts
```

---

**文档结束。** 执行时若与现网 schema 字段名冲突，以代码为准微调命名，但勿缩小本方案的验收范围。
