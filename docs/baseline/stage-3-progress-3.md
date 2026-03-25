# 阶段 3 进展记录（第三批）

## 本批目标

开始迁移文本生成层，优先拆出 `build_prompt()` 与 `api_chat()`，并让主脚本优先调用 `night_journal.generation`。

---

## 本批已完成内容

### 1. 新增 `generation/prompt_builder.py`
已迁出：
- `build_prompt()`

职责：
- 组合 world_state、override、recent memories、events、topic、memory/future blocks、重复风险、场景、意象、情绪与剧情弧线提示
- 输出正文生成 prompt

### 2. 新增 `generation/llm_client.py`
已迁出：
- `api_chat()`

职责：
- 统一构造模型请求 payload
- 统一发起 HTTP 请求
- 统一解析模型返回内容

### 3. 主脚本新增 generation 层导入

`generate_night_journal.py` 已新增可选导入：
- `generation_build_prompt`
- `generation_api_chat`

### 4. 主脚本已开始优先调用 generation 层

以下函数现已优先委托给 `night_journal.generation`：
- `build_prompt()`
- `api_chat()`

同时仍保留旧版 fallback，以维持可回滚性。

---

## 验证结果

已完成验证：
- `night_journal/generation/prompt_builder.py` 通过 `py_compile`
- `night_journal/generation/llm_client.py` 通过 `py_compile`
- `scripts/generate_night_journal.py` 通过 `py_compile`
- import 主脚本后，`build_prompt()` 可正常返回 prompt 文本
- `api_chat` 入口函数可调用

本次验证输出：
- `prompt_len = 856`
- `prompt_has_owner = True`
- `api_fn = True`

说明：
- prompt 构建链已开始走 generation 层
- prompt 内容结构正确，核心人物设定仍在
- LLM 客户端入口已接回主脚本

---

## 当前阶段判断

到这一步，阶段 3 已从叙事决策层进入文本生成层。

当前已完成：
- 叙事决策模块拆出并接回主脚本
- prompt builder 拆出并接回主脚本
- llm client 拆出并接回主脚本

这意味着生成链的前半段已经开始被新包接管。

---

## 下一步建议

阶段 3 下一批建议继续拆：
1. `refine_body()` → `generation/body_refiner.py`
2. `generate_title_and_description()` → `generation/title_desc.py`
3. 如有余力，再补 `output_cleaner.py`

拆完这批，文本生成层才算基本成型。
