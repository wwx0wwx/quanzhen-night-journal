# 阶段 3 进展记录（第四批）

## 本批目标

完成文本生成层后半段迁移：`refine_body()` 与 `generate_title_and_description()` 接入 generation 模块。

---

## 本批已完成内容

### 1. 新增 `generation/body_refiner.py`

- `refine_body(base_url, api_key, model, body)`
- 职责：对正文做冷处理式润色，削薄、去除模板感、增强克制质感

### 2. 新增 `generation/title_desc.py`

- `generate_title_and_description(base_url, api_key, model, body, recent_titles, recent_descs)`
- 职责：根据正文生成标题与 description，JSON 输出，含 fallback 容错

### 3. 主脚本 import 补入

- `generation_refine_body`
- `generation_title_desc`

### 4. 主脚本函数体正式切换

- `refine_body()` 已优先调用 `generation_refine_body`，保留旧版 fallback
- `generate_title_and_description()` 已优先调用 `generation_title_desc`，保留旧版 fallback

---

## 验证结果

- `scripts/generate_night_journal.py`：`py_compile` 通过
- `title_has_generation_check: True`
- `refine_has_generation_check: True`
- `generation_title_desc callable: True`
- `generation_refine_body callable: True`

---

## 当前 generation 层模块清单

| 文件 | 函数 | 状态 |
|---|---|---|
| `generation/llm_client.py` | `api_chat()` | 已接入主脚本 |
| `generation/prompt_builder.py` | `build_prompt()` | 已接入主脚本 |
| `generation/body_refiner.py` | `refine_body()` | 已接入主脚本 |
| `generation/title_desc.py` | `generate_title_and_description()` | 已接入主脚本 |

---

## 下一步建议

文本生成层已基本成型。阶段 3 后续可考虑：

1. 补 `generation/__init__.py`，统一对外导出接口
2. 补单元测试（`tests/test_generation/`）
3. 开始阶段 4：`application.py` 完整接管主流程，主脚本退化为纯入口
