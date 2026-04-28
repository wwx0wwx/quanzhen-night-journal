# Changelog

本文件记录全真夜记各版本的主要变更。

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
