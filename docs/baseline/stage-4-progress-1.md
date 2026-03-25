# 阶段 4 进展记录（第一批）

## 本批目标

让 `application.py` 完整接管主流程，主脚本退化为薄入口层。

---

## 本批已完成内容

### 1. `night_journal/application.py` 完整重写

完整接管了原 `main()` 里的全部主流程逻辑，包括：

- 配置加载（`load_settings`）
- 状态读取（`StateStore`、`ContentCatalog`）
- VPS 信号采集（`collect_vps_signals`）
- 近期文章上下文（`build_recent_context`）
- 叙事决策（`choose_topic` / `choose_world_material` / `maybe_memory` / `maybe_future_fragment` / `story_arc_triggers`）
- 文本生成（`build_prompt` / `api_chat` / `refine_body` / `generate_title_and_description`）
- 质检与修复（`_quality_check`）
- 文件输出（写入 Hugo Markdown）
- 状态漂移与弧线推进（`_drift_state` / `_update_story_arcs`）
- 状态持久化（`store.save_*`）

返回 `RunResult`，包含标题、slug、模式、是否修复等信息。

### 2. 所有子模块接口对齐

逐一核对并修正了以下调用签名：
- `choose_topic(rules, state, overrides)`
- `choose_world_material(imagery, scenes, emotions, state, overrides, repeated_phrases)`
- `maybe_memory(primary, overrides, anchors, recent_memories, rules)`
- `maybe_future_fragment(overrides, future_fragments, story_arcs)`
- `story_arc_triggers(state, overrides)`
- `build_recent_context(settings)`
- `recent_posts(settings, limit)` 替代 `recent_post_paths`

### 3. 主脚本 `main()` 退化为薄入口

`main()` 现在优先调用 `app_run(BASE)`，只在 `app_run` 不可用时回退到旧版 inline 流程。

---

## 验证结果

- `night_journal/application.py`：`py_compile` 通过
- `scripts/generate_night_journal.py`：`py_compile` 通过
- `app_run` import 成功，`run` 函数签名正确
- `main()` 已优先委托 `app_run`
- fallback 仍在，可回滚

验证输出：
- `import OK`
- `run signature: (base_path: Path | None = None) -> RunResult`
- `main_delegates_to_app_run: True`
- `app_run_available: True`
- `fallback_still_present: True`

---

## 当前阶段判断

**阶段 4 第一批：已完成。**

`application.py` 已成为完整的主流程层。主脚本已成功退化为薄入口。

---

## 下一步建议

1. 补 inputs / narrative 层单元测试
2. 补 `application.py` 的集成测试（mock LLM）
3. 考虑 CI/CD 集成（GitHub Actions）
4. 清理临时修复脚本（`fix_*.py`）
