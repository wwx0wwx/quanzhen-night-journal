# 阶段 3 进展记录（第二批）

## 本批目标

把已拆出的叙事决策模块正式接回 `generate_night_journal.py`，让主流程开始优先调用 `night_journal.narrative`。

---

## 本批已完成内容

### 1. 主脚本新增 narrative 模块导入

`generate_night_journal.py` 已新增可选导入：
- `narrative_choose_topic`
- `narrative_choose_world_material`
- `narrative_maybe_memory`
- `narrative_maybe_future_fragment`
- `narrative_story_arc_triggers`

### 2. 主脚本已开始优先调用 narrative 层

以下函数现在都已优先委托给 `night_journal.narrative`：
- `choose_topic()`
- `choose_world_material()`
- `maybe_memory()`
- `maybe_future_fragment()`
- `story_arc_triggers()`

### 3. 兼容策略仍保留

和前面阶段一样：
- 新 narrative 模块可用时，优先走新路径
- 若不可用，仍回退到旧版实现

这保证了：
- 迁移过程中可回滚
- 不会因为一次接入就把旧主流程完全掐断

---

## 验证结果

已完成验证：
- `scripts/generate_night_journal.py` 通过 `py_compile`
- import 主脚本后，叙事决策函数调用成功

本次验证输出：
- `topic_ok = 江湖 True`
- `scene_ok = 落雨未歇时的檐下 幽怨 狠后的空 6`
- `memory_len = 0`
- `future_len = 0`
- `arcs_len = 1`

说明：
- 主脚本已能通过 narrative 层正常选题
- 能正常选择场景、意象、主辅情绪
- 记忆与未来片段函数可运行
- 剧情弧线提示可运行

---

## 当前阶段判断

到这一步，阶段 3 已从“模块存在”进入“主脚本优先调用 narrative 层”的状态。

这意味着叙事决策层迁移已经真正开始接管主流程。

---

## 下一步建议

阶段 3 第三批建议继续迁移文本生成层，优先顺序如下：
1. `build_prompt()` → `generation/prompt_builder.py`
2. `api_chat()` → `generation/llm_client.py`
3. `refine_body()` → `generation/body_refiner.py`
4. `generate_title_and_description()` → `generation/title_desc.py`

先把“生成链”拆出来，再动质量门禁层。
