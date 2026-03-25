# 阶段 0 基线说明（本地开发端）

## 1. 本地项目位置

当前确认的本地开发端项目目录为：

`/root/.openclaw/workspace/quanzhen-night-journal`

该目录为一个独立 git 仓库，当前 `git status` 干净。

---

## 2. 当前本地项目现状

本地仓库当前属于**可迁移模板 / 项目化版本**，并非远程长期运行节点的实时完整副本。

已确认特点：
- 存在完整的 `scripts/` 入口脚本
- 存在 `automation/` 下的规则与说明文档
- 运行时状态文件多数以 `*.example.json` 形式存在
- 缺少直接可运行所需的 runtime JSON：
  - `world_state.json`
  - `recent_memories.json`
  - `night_journal_stats.json`
  - `manual_overrides.json`
  - `memory_anchors.json`
  - `future_fragments.json`
  - `topic_rules.json`
- 项目提供了 `scripts/bootstrap_runtime_state.py` 用于从模板初始化运行时状态

这说明：
- 本地项目适合作为开发端
- 但在正式重构前，必须先补足本地 runtime 基线

---

## 3. 当前关键入口

### 脚本入口
- `scripts/run_night_journal.sh`
- `scripts/generate_night_journal.py`
- `scripts/analyze_journal.py`

### 配置入口
- `.env.example`
- 未来运行使用 `.env`

### 文档入口
- `automation/README-system.md`
- `docs/architecture.md`
- `docs/deployment.md`
- `docs/review-workflow.md`
- `MIGRATION.md`

---

## 4. 当前发现的本地基线差异

### 4.1 与远程运行端相比的差异
本地仓库与远程长期运行节点相比，至少存在以下差异：

1. **运行时状态未落地**
   - 本地缺少 runtime JSON，仅有 example 模板

2. **默认输出路径仍偏旧**
   - `scripts/generate_night_journal.py` 默认输出目录仍是 `/var/www/shetop.ru`
   - `scripts/run_night_journal.sh` 默认输出目录也仍是 `/var/www/shetop.ru`
   - 说明本地模板仍保留旧域名迁移痕迹

3. **README-system.md 里的静态发布目录仍写旧值**
   - 文档中仍是 `/var/www/shetop.ru`
   - 与当前远程长期节点 `iuaa.de` 不一致

4. **脚本依赖 `.env` 与 bootstrap 初始化**
   - 本地未初始化前，不能直接拿来完整回归

### 4.2 这意味着什么
阶段 0 的核心，不只是“记一份清单”，还包括：
- 承认本地是**开发模板基线**，不是生产镜像基线
- 先建立一个**可运行的本地开发基线**，后续重构才能有参照物

---

## 5. 阶段 0 的固定结论

在本地开发端重构时，以下事实作为基线固定下来：

1. 本地项目目录：`/root/.openclaw/workspace/quanzhen-night-journal`
2. 本地项目当前是模板化、可迁移化版本
3. 本地项目需要先通过 bootstrap 建立 runtime 状态
4. 当前本地仍保留旧域名/旧输出目录默认值，需要在后续阶段统一收口到配置层
5. 在阶段 0 结束前，不做结构性代码重构，只做：
   - 基线文档
   - fixture 目录
   - 本地回归前置准备

---

## 6. 已建立的本地基线目录

已创建：
- `docs/baseline/`
- `tests/fixtures/automation/`
- `tests/fixtures/content_posts/`
- `tests/fixtures/draft_review/`
- `tests/fixtures/signals/`

这些目录将用于后续固化本地回归样本与模拟输入。

---

## 7. 阶段 0 下一步要补的东西

在进入阶段 1 前，还应继续完成以下基线工作：

1. 生成本地 `.env`
2. 运行 `scripts/bootstrap_runtime_state.py`
3. 将 bootstrap 后的 runtime 文件与 example 模板差异记录下来
4. 形成一版可重复执行的本地 smoke test
5. 固定首轮 fixture 样本

---

## 8. 当前阶段结论

阶段 0 已确认：
- 本地开发端在哪里
- 当前本地仓库属于什么状态
- 本地与远程的关键差异有哪些
- 后续重构前必须先补哪些基线能力

这为后续搭包骨架与迁移逻辑提供了可信起点。
