# 阶段 1 实施记录

## 目标

搭建 `night_journal/` 包骨架，并落下最基础的配置边界、数据模型、日志工具与应用编排入口，同时保持现有脚本入口兼容。

---

## 已完成内容

### 1. 包骨架已创建

已创建：
- `night_journal/__init__.py`
- `night_journal/config.py`
- `night_journal/models.py`
- `night_journal/application.py`
- `night_journal/logging_utils.py`
- `night_journal/inputs/__init__.py`
- `night_journal/narrative/__init__.py`
- `night_journal/generation/__init__.py`
- `night_journal/quality/__init__.py`
- `night_journal/publishing/__init__.py`
- `night_journal/analysis/__init__.py`

### 2. `config.py`

已新增统一配置加载入口 `load_settings()`，当前负责：
- 解析 `ENGINE_ROOT`
- 解析 `automation/content/draft_review/output/log` 等路径
- 读取 `OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL`

### 3. `models.py`

已新增初始数据模型：
- `GeneratedDraft`
- `QualityReport`
- `PublishResult`
- `RunResult`

这仍是轻量起步，但已开始替代“满地裸 dict”。

### 4. `logging_utils.py`

已新增统一 logger 工具，先提供最小文件日志能力。

### 5. `application.py`

已新增最小编排骨架 `run()`：
- 读取 settings
- 初始化 logger
- 返回 `RunResult`

目前它尚未接管真正主流程，但已作为未来迁移的稳定入口。

### 6. 脚本入口兼容性处理

已在 `scripts/generate_night_journal.py` 中加入对 `night_journal.application` 的可选导入。

当前仍不改变主流程逻辑，只是为后续接入新包预留入口。

---

## 当前阶段判断

阶段 1 的核心目标已经完成：
- 包结构已立住
- 配置边界已出现
- 数据结构已出现
- 编排入口已出现
- 旧脚本仍保留主逻辑，没有被粗暴替换

这说明后续阶段已具备“往包里迁逻辑”的骨架条件。

---

## 下一步

下一阶段应进入：
**阶段 2：迁移输入层与状态读写**

优先迁出的对象：
- JSON 读写
- override 解释
- VPS 信号采集
- 最近文章装载
- 规则/素材池装载

---

## 注意事项

当前仍未做的事：
- 未让 `generate_night_journal.py` 真正调用 `application.run()` 主导流程
- 未拆出任何业务模块实现
- 未补针对新包的自动化测试

这些都属于阶段 2 及之后的工作，不应在阶段 1 混入。
