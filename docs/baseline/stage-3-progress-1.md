# 阶段 3 进展记录（第一批）

## 本批目标

正式进入叙事决策层迁移，优先把“决定写什么”的部分从大脚本中拆出来。

---

## 本批已完成内容

### 1. 新增 `narrative/topic_selector.py`
已迁出：
- `choose_topic()`

职责：
- 结合 `topic_rules`、`world_state.continuity.recent_topics`、`manual_overrides.forbid_topics` 与 `force_topic`
- 选出当前主题与提示语

### 2. 新增 `narrative/material_selector.py`
已迁出：
- `choose_world_material()`

职责：
- 选择意象、场景、主情绪、辅情绪
- 处理高频意象抑制与部分场景偏置逻辑
- 处理 `force_scene / force_primary_emotion / force_secondary_emotion`

### 3. 新增 `narrative/memory_selector.py`
已迁出：
- `maybe_memory()`

职责：
- 处理 `force_memory_id`
- 控制近期记忆与长期记忆锚点的触发

### 4. 新增 `narrative/future_selector.py`
已迁出：
- `maybe_future_fragment()`

职责：
- 处理 `force_future_id`
- 根据剧情弧线阶段选择未来片段

### 5. 新增 `narrative/story_arcs.py`
已迁出：
- `story_arc_triggers()`

职责：
- 根据 post_count、情绪阈值与 override，产出剧情推进提示语

---

## 验证结果

已完成验证：
- 五个 narrative 模块全部通过 `py_compile`
- 在本地真实 state / rules / overrides / 素材池下执行成功

验证输出示例：
- `topic_ok = 陪伴 True`
- `material_ok = 6 搁铜盆的小几旁 幽怨 慌`
- `memory_type = str`
- `future_type = str`
- `arc_lines = 1`

这说明：
- 主题选择正常
- 材料选择正常
- 记忆块与未来块生成正常
- 剧情弧线提示生成正常

---

## 当前阶段判断

阶段 3 已起步成功。

现在“叙事决策层”已经不再只是计划，而是开始拥有真实可调用实现。

但当前仍然只是：
- 模块已拆出
- 已做独立验证
- 还**没有正式接回主脚本**

因此本批完成后，下一步应当是：
1. 让 `generate_night_journal.py` 优先调用这些 narrative 模块
2. 再开始迁 `build_prompt()` 与生成链

---

## 下一步建议

阶段 3 第二批建议按顺序继续做：
1. 把主脚本中的 `choose_topic()` / `choose_world_material()` / `maybe_memory()` / `maybe_future_fragment()` / `story_arc_triggers()` 接入 `night_journal.narrative`
2. 保留 fallback
3. 验证主脚本在本地仍可 import 与执行到相应阶段

这一步做完，叙事决策层才算从“模块存在”进入“主流程接管”。
