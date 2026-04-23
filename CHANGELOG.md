# Changelog

本文件记录全真夜记各版本的主要变更。

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
