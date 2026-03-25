# 阶段 5 收尾总结

## 阶段目标回顾

完成质检发布层与分析层迁移，补齐测试覆盖，主脚本最终瘦身。

---

## 已完成模块清单

### quality 层
| 模块 | 函数 | 职责 |
|---|---|---|
| `quality/checker.py` | `quality_check()` | 质量门禁：长度/禁词/模板/重复度 |
| `quality/checker.py` | `guard_publish()` | 发布守卫：暂停/manual-only/日限 |

### publishing 层
| 模块 | 函数 | 职责 |
|---|---|---|
| `publishing/writer.py` | `build_markdown()` | 组装 Hugo Markdown 内容 |
| `publishing/writer.py` | `route_output_dir()` | 模式路由（auto/draft/review-first）|
| `publishing/writer.py` | `write_post()` | 落盘写文件 |
| `publishing/hugo.py` | `build_hugo()` | 调用 hugo 构建 |
| `publishing/hugo.py` | `git_push()` | git add/commit/push |

### analysis 层
| 模块 | 函数 | 职责 |
|---|---|---|
| `analysis/report.py` | `analyze()` | 完整分析报告生成 |
| `analysis/report.py` | `print_report()` | 人类可读报告打印 |
| `analysis/report.py` | `title_shape()` | 标题句法分类 |
| `analysis/report.py` | `latest_post_files()` | 获取近期发布文件列表 |

---

## application.py 更新

- 已接入 `guard_publish()`（state + overrides 加载后立即执行）
- 已接入 `write_post()`（替代 inline Markdown 落盘）
- 已移除内联 `_quality_check()`，改为调用 `quality.checker.quality_check()`

---

## 主脚本状态说明

`scripts/generate_night_journal.py` 当前有 618 行，其中大量函数以 fallback 形式保留：

**已被包接管、主脚本保留 fallback 的函数：**
- `choose_topic()` → `narrative/topic_selector`
- `choose_world_material()` → `narrative/material_selector`
- `maybe_memory()` → `narrative/memory_selector`
- `maybe_future_fragment()` → `narrative/future_selector`
- `story_arc_triggers()` → `narrative/story_arcs`
- `build_prompt()` → `generation/prompt_builder`
- `api_chat()` → `generation/llm_client`
- `refine_body()` → `generation/body_refiner`
- `generate_title_and_description()` → `generation/title_desc`

**已被包接管、主脚本 main() 直接委托的：**
- `main()` → `application.run()` (当 app_run 可用时)

**仍为主脚本独有的工具函数（合理保留）：**
- `sh()`, `log_line()`, `save_json()`, `today_utc()`
- `get_env()`, `map_*()`, `collect_vps_events()`
- `summarize_for_state()`, `capture_recent_memory()`
- `update_story_arcs()`, `update_stats()`

保留原则：只要 `app_run` 可用，这些 fallback 不会被执行。远程节点迁移完成后可再做一次清理。

---

## 测试总覆盖

**102 tests，全部 PASSED，14.95s**

| 层 | 测试文件数 | tests 数 |
|---|---|---|
| generation | 3 | 19 |
| inputs | 1 | 8 |
| narrative | 5 | 32 |
| application | 1 | 4 |
| publishing | 1 | 11 |
| quality | 1 | 14 |
| analysis | 1 | 14 |
| **总计** | **13** | **102** |

---

## 完整路线回顾

| 阶段 | 状态 |
|---|---|
| 0 基线冻结 | 完成 |
| 1 搭包骨架 | 完成 |
| 2 迁输入层 | 完成 |
| 3 迁叙事与生成 | 完成 |
| 4 迁质检与发布（application 接管） | 完成 |
| 5 迁质检/发布/分析模块 + 测试补全 | 完成 |

---

## 后续建议

1. **远程节点同步**：将 `night_journal/` 包部署到远程 VPS，切换实际运行
2. **主脚本清理**：远程切换完成后，删除主脚本里的 fallback 函数
3. **CI/CD**：GitHub Actions 自动跑 `python3 -m pytest tests/ -q`
4. **end-to-end 冒烟测试**：真实 API 连通后跑一次完整生成链验证
