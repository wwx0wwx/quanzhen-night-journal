# 阶段 2 进展记录（第三批）

## 本批目标

继续迁移输入层预处理逻辑，把最近文章上下文构建与 VPS 信号采集正式接到 `night_journal.inputs`，进一步缩薄主脚本。

---

## 本批已完成内容

### 1. `inputs/recent_posts.py` 已增强

新增能力：
- `extract_repeated_phrases()`
- `build_recent_context()`

这意味着最近文章相关的预处理逻辑，不再只有“读文件”，还开始承接：
- 正文提取
- front matter 解析
- 标题/description 收集
- 重复措辞提取

### 2. `generate_night_journal.py` 已接入最近文章预处理模块

主脚本中的 `build_recent_context()` 现已：
- 优先调用 `night_journal.inputs.recent_posts.build_recent_context()`
- 保留旧逻辑 fallback

### 3. `generate_night_journal.py` 已接入 VPS 信号输入模块

主脚本中的 `collect_vps_events()` 现已：
- 优先调用 `night_journal.inputs.vps_signals.collect_vps_signals()`
- 由新输入层提供：
  - uptime_days
  - load1
  - mem_pct
  - ssh_bad
  - disk_pct
  - nginx_hits
  - service_restart_hits
  - cert_hits
- 然后仍在主脚本中完成“信号 → 江湖事件”的映射
- 同时保留旧版 shell 采集逻辑 fallback

---

## 验证结果

已完成验证：
- `scripts/generate_night_journal.py` 通过 `py_compile`
- `night_journal/inputs/recent_posts.py` 通过 `py_compile`
- `night_journal/inputs/vps_signals.py` 通过 `py_compile`
- 在本地 import 主脚本后：
  - `build_recent_context()` 可正常返回结果
  - `collect_vps_events()` 可正常返回事件列表与 uptime_days

本次验证输出：
- `recent_ctx_lengths = 0 0 0 0`
- `events_count = 5`
- `uptime_days = 110`

说明：
- 本地当前没有最近文章样本，因此 recent context 为空，这符合现状
- VPS 信号采集与事件映射链路已可执行

---

## 当前阶段判断

到这一步，阶段 2 的第三批核心目标已经完成：
- 最近文章预处理已开始从主脚本迁出
- VPS 底层信号采集已开始从主脚本迁出
- `generate_night_journal.py` 的输入层与预处理层进一步变薄

这表示阶段 2 已从“只是建立输入模块”进入“主脚本真实调用新模块”的阶段。

---

## 阶段 2 剩余工作

虽然第三批已完成，但阶段 2 还未彻底结束。剩余建议项包括：
1. 让主脚本不再保留旧版 fallback，改为明确依赖新输入层
2. 补输入层测试与 fixtures
3. 如有必要，把 `strip_front_matter()` / `parse_front_matter()` 的调用统一收口，避免主脚本与输入层重复定义

---

## 结论

阶段 2 目前已完成：
- 输入层模块落地
- 顶部状态/规则装载接管
- recent context 预处理接管
- VPS 信号采集接管

接下来，已可以开始考虑：
- 收尾阶段 2
- 或进入阶段 3：迁叙事决策与文本生成
