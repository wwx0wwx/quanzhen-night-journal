# 阶段 2 进展记录（第二批）

## 本批目标

把 `generate_night_journal.py` 最外层的输入装载逻辑正式接入 `night_journal.inputs`，先迁出“读配置、读状态、读规则”这层职责。

---

## 本批已完成内容

### 1. 主脚本新增输入层依赖接入

`generate_night_journal.py` 已新增可选导入：
- `load_settings`
- `StateStore`
- `ContentCatalog`

### 2. 主脚本顶部加载逻辑已收口

原先主脚本直接使用：
- `json.loads((AUTO / 'world_state.json').read_text())`
- `json.loads((AUTO / 'memory_anchors.json').read_text())`
- `json.loads((AUTO / 'topic_rules.json').read_text())`
- ...

现在已改为：
- 优先通过 `load_settings()` + `StateStore()` + `ContentCatalog()` 装载
- 若新模块不可用，再回退到旧逻辑

### 3. 当前已接入到新输入层的对象

通过 `StateStore` / `ContentCatalog` 已接入：
- `world_state`
- `memory_anchors`
- `topic_rules`
- `imagery_pool`
- `scene_pool`
- `emotion_pool`
- `event_map_rules`
- `recent_memories`
- `manual_overrides`
- `future_fragments`
- `night_journal_stats`

### 4. 保持兼容策略

当前仍保留旧版 fallback 逻辑。

这意味着：
- 若新包导入失败，主脚本依旧可按旧方式工作
- 这一步属于“接管输入层”，不是“强制切断旧路”

---

## 验证结果

已完成验证：
- `scripts/generate_night_journal.py` 已通过 `py_compile`
- 在设置本地环境变量后，直接 import 主脚本成功
- 验证输出表明主脚本当前已使用本地项目路径：
  - `BASE=/root/.openclaw/workspace/quanzhen-night-journal`
  - `AUTO=/root/.openclaw/workspace/quanzhen-night-journal/automation`
  - `CONTENT=/root/.openclaw/workspace/quanzhen-night-journal/content/posts`
- `rules['categories']` 已正常读取
- `overrides['mode']` 已正常读取

---

## 当前阶段判断

到这一步，阶段 2 已完成最关键的一刀：
**主脚本最外层输入装载已经开始由新输入层接管。**

这使得后续继续迁移：
- front matter 解析
- 最近文章读取
- VPS 信号采集

都会更顺，不必再从一团大脚本里硬撕。

---

## 下一步

阶段 2 下一批建议继续迁移：
1. `recent_post_paths()` / `strip_front_matter()` / `parse_front_matter()` / `build_recent_context()`
2. `collect_vps_events()` 对底层信号采集的依赖，改为使用 `inputs.vps_signals`

等这两块也迁出后，输入层才算真正从“装载”扩展到“预处理”。
