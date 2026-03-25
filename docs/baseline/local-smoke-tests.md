# 本地 Smoke Test（阶段 0 初版）

## 目的

用于在本地开发端快速验证夜札系统的最基本可运行性，为后续重构提供回归基线。

当前本地项目路径：
`/root/.openclaw/workspace/quanzhen-night-journal`

---

## 前置条件

1. 已存在 `.env`
2. 已执行：
   ```bash
   python3 scripts/bootstrap_runtime_state.py
   ```
3. 已确保目录存在：
   - `content/posts/`
   - `draft_review/`
   - `logs/`
   - 本地输出目录 `.tmp-output/`

---

## Smoke Test 1：运行时状态初始化

### 命令
```bash
python3 scripts/bootstrap_runtime_state.py
```

### 期望
- 若 runtime 文件不存在，则自动创建
- 若已存在，则输出 `SKIP exists`
- 不报错退出

---

## Smoke Test 2：基础分析脚本

### 命令
```bash
python3 scripts/analyze_journal.py
```

### 期望
- 能输出当前世界状态
- 能输出近期记忆层与统计信息
- 不因缺失 runtime JSON 而报错

当前已验证：**通过**

---

## Smoke Test 3：配置加载

### 检查项
- `.env` 存在
- `ENGINE_ROOT` 指向本地项目根目录
- `BLOG_OUTPUT_DIR` 指向本地临时输出目录，而非生产目录
- `LOG_DIR` 指向本地日志目录

当前本地 `.env` 约定：
- `ENGINE_ROOT=/root/.openclaw/workspace/quanzhen-night-journal`
- `BLOG_OUTPUT_DIR=/root/.openclaw/workspace/quanzhen-night-journal/.tmp-output`
- `LOG_DIR=/root/.openclaw/workspace/quanzhen-night-journal/logs`

---

## Smoke Test 4：目录安全性

### 检查项
- 本地默认输出目录不是线上目录
- 本地运行不应写入远程生产路径
- 本地重构前的测试输出应限制在项目根目录内

当前已处理：**通过**

---

## Smoke Test 5：后续待补

以下测试作为下一轮 smoke/integration 补充项：

1. `review-first` 模式下手动生成一篇草稿
2. `manual-only` 模式下确认自动发布被阻断
3. `pause_publishing=true` 时确认流程中止
4. `auto` 模式下确认本地仅写入本地测试目录
5. 首次本地全链路 run（生成 → 落盘 → Hugo/输出）

这些测试应在继续补齐本地内容目录与运行样本后执行。

---

## 当前结论

阶段 0 初版 smoke 已证明：
- 本地项目路径已固定
- `.env` 已建立
- runtime state 已 bootstrap
- `analyze_journal.py` 可运行
- 本地环境已具备继续进入阶段 1 的最低条件

但还未完成完整生成链路验证，后续仍需继续补齐本地集成测试。
