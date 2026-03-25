# 阶段 2 进展记录（第一批）

## 目标

开始迁移输入层与状态读写，把大脚本中负责“装材料”的部分抽离到 `night_journal.inputs`。

---

## 本批已完成模块

### 1. `inputs/state_store.py`
已落地 `StateStore`，当前支持：
- 读取 `world_state.json`
- 读取 `recent_memories.json`
- 读取 `night_journal_stats.json`
- 读取 `manual_overrides.json`
- 读取 `future_fragments.json`
- 读取 `memory_anchors.json`
- 写回 `world_state.json`
- 写回 `recent_memories.json`
- 写回 `night_journal_stats.json`

### 2. `inputs/content_catalog.py`
已落地 `ContentCatalog`，当前支持：
- 读取 `topic_rules.json`
- 读取 `imagery_pool.json`
- 读取 `scene_pool.json`
- 读取 `emotion_pool.json`
- 读取 `event_map_rules.json`

### 3. `inputs/overrides.py`
已落地 `OverrideState` 与 `parse_overrides()`，当前提供：
- `mode`
- `pause_publishing`
- `is_manual_only`
- `is_review_first`
- `is_auto`

### 4. `inputs/vps_signals.py`
已落地 `VpsSignals` 与 `collect_vps_signals()`，当前支持采集：
- uptime_days
- load1
- mem_pct
- ssh_bad
- disk_pct
- nginx_hits
- service_restart_hits
- cert_hits

### 5. `inputs/recent_posts.py`
已落地：
- `RecentPost`
- `strip_front_matter()`
- `parse_front_matter()`
- `recent_posts()`

当前已能统一装载最近文章正文、标题、description。

---

## 验证结果

已完成最小验证：
- `StateStore` 可正常读取 world/stats/overrides
- `ContentCatalog` 可正常读取 topic rules
- `parse_overrides()` 正常返回模式状态
- `collect_vps_signals()` 可在本机返回结构化信号
- `recent_posts()` 可正常执行
- 输入层新增模块已通过 `py_compile`

验证输出示例：
- `world_meta_version = 2`
- `stats_post_count = 0`
- `override_mode = auto`
- `topic_categories = 5`
- `signals_uptime_days = 110`

---

## 当前阶段判断

阶段 2 已经起步成功。

这意味着：
- 后续可以逐步把 `generate_night_journal.py` 中直接 `json.loads(...)`、front matter 解析、系统信号采集等逻辑迁出
- 输入层已不再只是纸面目录，而是开始承接真实实现

---

## 下一步

下一批阶段 2 工作应继续做两件事：
1. 在主脚本中接入这些输入模块，先替换最外层装载逻辑
2. 继续补输入层测试与 fixture 样例

在这一步之前，不建议贸然开始迁叙事决策层。
