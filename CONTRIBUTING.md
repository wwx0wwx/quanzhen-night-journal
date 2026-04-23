# Contributing to 全真夜记

感谢你对全真夜记的关注。以下是参与贡献的基本指南。

## 开发环境

### 后端

```bash
# 依赖管理使用 uv
uv sync --extra dev

# 运行测试
uv run python -m pytest backend/tests/ -q

# 代码风格检查
uv run ruff check backend/

# 自动格式化
uv run ruff format backend/
```

### 前端

```bash
cd frontend
npm install
npm run dev      # 开发服务器
npm test         # 运行测试
npm run build    # 生产构建
```

### Docker 部署

```bash
cp .env.example .env
# 编辑 .env 填写必要配置
docker compose up -d --build
```

## 提交规范

提交信息使用中文或英文均可，格式参考：

```
<类型>: <简要描述>

<详细说明（可选）>
```

类型：
- `feat`: 新功能
- `fix`: 修复 bug
- `refactor`: 重构（不改变功能）
- `docs`: 文档变更
- `test`: 测试相关
- `chore`: 构建、依赖、配置变更

## Pull Request 流程

1. Fork 本仓库
2. 从 `main` 创建功能分支
3. 确保 `ruff check` 和 `pytest` 全部通过
4. 确保前端 `npm run build` 和 `npm test` 通过
5. 提交 PR 并描述你的改动

## 代码风格

- **后端**: Python 3.11+，遵循 ruff 配置（`pyproject.toml`），行宽 120
- **前端**: Vue 3 Composition API，ESLint + Prettier
- **命名**: 类用 PascalCase，函数/变量用 snake_case（后端）或 camelCase（前端），常量用 UPPER_CASE
- **注释**: 尽量不写注释，代码本身应该足够清晰。只在"为什么"不明显时写

## 报告问题

请在 GitHub Issues 中提交，包含：
- 复现步骤
- 期望行为 vs 实际行为
- 环境信息（操作系统、Docker 版本等）
