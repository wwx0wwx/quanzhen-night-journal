# Changelog

本文件记录全真夜记各版本的主要变更。

## [1.4.2] - 2026-07-10

### Fixed
- 生成链路回归：fake LLM 正文补足至默认 `qa.min_length=900` 以上，标题按 seed 区分；未显式降门槛的生成/webhook 用例补 `qa.min_length` 夹具，消除 `circuit_open` 误熔断。
- `doc/database_schema.sql` 的 `users` 表补齐 2FA 列（`totp_*` / `recovery_codes_hash`），与 `init_database` 迁移一致。
- `doc/database_migration.md` 迁移辅助函数名更正为 `_ensure_column`。
- 前端 ESLint：清理 unused 与可自动修复的格式 warning；`npm run lint` 启用 `--max-warnings=0`。

## [1.4.1] - 2026-07-10

### Added
- 闲笔小彩蛋：约每 10–14 篇强制/随机一篇「没事可做」夜记（胭脂水粉、糖水、缝袖、买花等），收束常带「王爷不派任务」的淡刺，声口仍克制。

## [1.4.0] - 2026-07-10

### Added
- 长线叙事规划器 `narrative_planner`：影中五阶段（0–10 年）、关系主音轮转、五类场景轮转、本篇任务卡。
- 配置项 `narrative.enabled`、`narrative.posts_per_world_year`（默认 15 篇≈1 世界年，约 3–5 个月真实发文对应 6–10 年影中年华）。
- QA：标题同名拒绝、开场 40 字指纹近复制检测（`qa.opening_similarity_threshold`）。
- 篇级记忆增强（关系主音/场景大类/禁用意象）与 L1 世界线状态记忆自动 upsert。

### Changed
- 默认 `qa.min_length` 提到 900，抑制姿态速写短文。
- 全真人格文案补「夜记写法硬约束」与「长线世界」；启动时对缺省文案的默认人格软升级。
- 生成上下文近篇扩展到 8 条并带开场指纹回避清单。

### Tests
- 新增 `test_narrative_planner`、`test_qa_opening_title`；调整生成去重用例开场，避免与新规则冲突。

## [1.3.0] - 2026-07-10

### Added
- 管理员 TOTP 两步验证：支持启用/确认/关闭、登录二阶段校验和一次性恢复码。
- 统一错误码目录与响应 `message_key`，前端错误描述优先按 i18n key 翻译。
- 自动数据库备份：支持设置页开关、Cron、保留份数、自动 `auto-` 快照与状态接口。
- 备份页展示自动备份状态、下次运行时间，并区分自动/手动数据库快照。

### Changed
- Login、Settings、Ghost、PersonaEdit、PostEdit 补全新增文案 i18n。
- 设置字段翻译支持带点号的配置键，避免 schema 字段在英文模式下回退中文。

### Tests
- 增加 2FA 登录/恢复码、错误 `message_key`、自动备份 prune 覆盖。
- 验证：后端全量 pytest、ruff、前端 vitest 与 production build。

## [1.2.0] - 2026-07-10

### Added
- 全局 Toast 与统一确认对话框（危险操作二次确认）。
- 设置页简单/全部模式、字段搜索；设置字段中英文翻译。
- 首页待签发队列（可直接签发）；预算接近提示。
- 路由懒加载；任务轨迹/发布决策/cron 文案 i18n。

### Changed
- 补全管理后台剩余中英文案与空状态引导。
- 删除未使用的旧 Navbar 组件。

## [1.1.1] - 2026-07-10

### Added
- 管理后台中英文切换（默认中文），侧栏/登录/首页等核心文案与状态标签支持双语。
- 语言偏好保存在本地 `localStorage`，刷新后保持。

### Notes
- 设置页字段级帮助文案仍以中文 schema 为主，分组标题已支持英文；后续可继续补全字段级翻译。

## [1.1.0] - 2026-07-10

### Changed
- 管理后台全面切换为浅色默认、左侧栏导航的干净 SaaS 风格界面。
- 导航与文案人话化：角色设定、长期记忆、发文任务、备份与迁移等。
- 首页改为「状态 + 下一步动作 + 待办」，高级健康/域名信息默认折叠。
- 旧版后台 UI 已本地备份，可按需回滚。

### Notes
- 正式入口仍为 `http://<IP>:5210/admin/`；域名站点不开放后台（设计如此）。

## [1.0.10] - 2026-07-09

### Fixed
- Hugo 发布完成判定改为按 build signal 精确匹配，避免接受上一轮构建的陈旧 `status=ok`。
- 重启恢复：保留 `waiting_human_signoff` 任务；仍处于 `queued` 的任务会在启动后按原事件重新投递。
- 中文记忆关键词降级检索改用字/双字与混合分词，不再依赖空格分词。

### Changed
- 记忆检索改为候选池裁剪（核心 + 最近 + 权重补齐），避免全表扫描。
- 感知采样显式标注容器/宿主机视角；支持 `SENSORY_HOST_ROOT` + `sensory.source_mode=host`。
- 新增 `/api/health/metrics` 进程与业务指标端点。
- 前端关键层（api/stores/utils）TypeScript 化；Dashboard/Memories/PersonaEdit 抽出共享模块降低单文件体积。
- 文档版本与工程实施说明同步到 1.0.10。

## [1.0.9] - 2026-04-28

### Added
- 发布健康检查与测试站可达性验证：补充博客入口、控制台入口、核心 API 的 smoke test 流程。
- 质量策略新增 `qa.required_perspective=first_person`，后台设置页可配置叙事人称。
- 生成追踪记录 LLM `finish_reason` 与请求输出上限，便于排查模型截断。

### Fixed
- 修复 AI 正文被 `max_tokens=1000` 截断仍被发布的问题；截断会自动重写，重试耗尽则失败。
- 修复第二人称正文可被发布的问题；命中“你/您”等第二人称叙事会自动重写，重试耗尽则失败。
- Hugo sidecar 构建启用 `--cleanDestinationDir`，删除文章后旧静态页面不再残留。
- 修复无域名、Cloudflare 代理、博客入口探测和发布决策展示中的多处误导性状态。

### Changed
- 正文生成默认输出上限调整为 `llm.max_tokens=2400`。
- 版本号统一升至 1.0.9（pyproject.toml、package.json、package-lock.json、backend/__init__.py、backend/config.py）。

## [1.0.8] - 2026-04-24

### Added
- 关于页面（/admin/about）：项目介绍、快速上手、功能模块说明和常见问题
- API Key 显示按钮：密钥字段支持点击"显示"从后端解密展示真实值
- 可视化调度选择器：高级设置中的复查时间和维护时间改为频率下拉 + 时间选择器，无需手写 cron
- POST /api/config/reveal 接口：安全解密并返回指定密钥字段的明文值
- 审计日志 API 支持分页与筛选

### Fixed
- SQLite PRAGMA（foreign_keys、busy_timeout、WAL）改为 engine event listener，确保连接池每条连接都正确设置
- Ghost 导入添加字段白名单和 zip 炸弹防护（256 MB 压缩 / 2.5 GB 解压上限）
- 登出时 delete_cookie 补齐 httponly 和 samesite 参数
- 记忆衰减添加权重下限，防止权重衰减到 0
- 人格查询优先过滤 is_active，避免选中已停用人格
- 滑动窗口限流器添加定时清理，防止内存泄漏
- X-Forwarded-For/X-Real-IP 仅在对端为 Cloudflare IP 时信任
- Hugo 配置 TOML 字符串转义换行符，防止注入
- QA 禁用词检测改为大小写不敏感
- 感知引擎时间差判断修正为非负检查
- 重试生成不再累积原始 prompt
- PostEdit/PersonaEdit 表单脏标记延迟到数据加载后注册，修复 3 个前端测试
- StabilityGauge hint 改为 computed 保证响应性
- Setup 页密码提示从"至少 12 位"修正为"至少 8 位"
- 前端路由添加 404 兜底重定向
- Docker Compose caddy depends_on 改为 service_healthy 条件

### Changed
- 版本号统一升至 1.0.8（pyproject.toml、package.json、backend/__init__.py）
- .gitignore egg-info 条目改为通配符 `*.egg-info/`
- cron 字段类型从文本框改为 schedule 可视化选择器

## [1.0.7] - 2026-04-23

### Added
- 场景骰子（scene_pool）：从全局硬编码迁移到每个人格独立的 JSON 字段，支持自定义场景池
- 任务列表页（/admin/tasks）：新增任务管理界面，支持状态筛选和分页
- 前端表单离开保护：PostEdit、PersonaEdit、Settings 页面添加 `onBeforeRouteLeave` 未保存提醒
- Setup 页面表单验证：密码最低 8 位、域名格式校验
- 配置键白名单：`ConfigEntry` 添加前缀校验，防止写入未知配置
- GitHub Actions CI：后端 lint + 测试、前端构建 + 测试、Docker 构建验证
- Docker healthcheck：core 和 caddy 容器添加健康检查
- ESLint + Prettier：前端代码风格统一配置

### Fixed
- `folder_monitors.py`：`add_monitor` 从 raw dict 改为 Pydantic schema 验证
- `webhook.py`：`request.json()` 添加异常捕获和类型校验
- `ghost.py`：文件下载添加 `resolve().is_relative_to()` 防目录穿越
- `memory_engine.py`：embedding 失败时记录 warning 日志而非静默忽略
- `setup.py`：初始化流程包裹 try/except，失败时回滚数据库
- `auth.py`：cookie secure 标志改为从 `Settings.is_production` 读取
- `scheduler.py`：`_scheduler_timezone()` 未初始化时记录 warning

### Changed
- 版本号统一为 1.0.7（pyproject.toml、backend/config.py）
- ruff 行宽从 100 调整为 120，忽略 B008（FastAPI Depends 模式）
- 全量 lint 修复：527 条告警清零

## [1.0.6] - 2026-04-19

### Added
- 默认全真人格 v3：丰富的身份设定、世界观、语言风格、禁忌清单、感知词典
- 自动识别旧版全真人格并升级到 v3
- 审计日志页面（/admin/audit）
- Ghost 导入导出与数据库备份功能
- 发布决策引擎：QA + 人工签发 + 自动发布三级路径

## [1.0.0] - 2026-04-14

### Added
- 初始版本发布
- FastAPI 后端 + Vue 3 前端 + Hugo 静态站点生成
- 人格系统、记忆系统、感知引擎
- LLM 内容生成管线（Context → Prompt → Generate → QA → Publish）
- 定时写作调度
- Docker 三服务部署（core + caddy + hugo-builder）
