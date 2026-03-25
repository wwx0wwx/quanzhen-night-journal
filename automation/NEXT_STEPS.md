# NEXT_STEPS.md — 全真夜札系统续接笔记

这份文件给未来的新会话看。用途只有一个：

**快速接上系统，知道最近做了什么、为什么这样改、接下来该优先看哪里。**

---

## 一、当前状态（一句话版）

全真夜札系统已经从“可运行原型”打磨到“可长期试运行版本”。

目前：
- 定时发布链路已打通
- GPT-5.4 已接入
- 状态机 / 记忆层 / 未来片段 / 剧情弧线 / 质量检查 / 审核模式 / 复盘脚本 都已落地
- 测试态已清理，系统已回到正式起跑态

---

## 二、重要入口文件

新会话接手时，优先读：

1. `/opt/blog-src/automation/README-system.md`
2. `/opt/blog-src/automation/world_state.json`
3. `/opt/blog-src/automation/manual_overrides.json`
4. `/opt/blog-src/automation/recent_memories.json`
5. `/opt/blog-src/automation/night_journal_stats.json`
6. `/opt/blog-src/scripts/generate_night_journal.py`
7. `/opt/blog-src/scripts/analyze_journal.py`

---

## 三、我们已经做过的修改历史（按阶段）

## 阶段 0：发现博客并开始接管

已确认博客结构：
- Hugo 源目录：`/opt/blog-src`
- 发布目录：`/var/www/shetop.ru`
- 主题：PaperMod
- 域名：`shetop.ru`

做过的事：
- 梳理博客目录
- 发布并改写前两篇文章，使其符合“全真”人设
- 修正首页文案，不再把博客局限为“记录技术与长夜见闻”

---

## 阶段 1：全真夜札引擎原型搭建

最初搭建了：
- `world_state.json`
- `memory_anchors.json`
- `topic_rules.json`
- `generate_night_journal.py`
- `run_night_journal.sh`
- systemd timer / service 模板

当时实现：
- 基础状态机
- 基础题材池
- 基础回忆触发
- Hugo 自动写入与发布
- 初版 VPS 事件接入

当时还是“占位稿 + prompt 输出”阶段。

---

## 阶段 2：接入真实模型 API

做过的关键改动：
- 将夜札引擎接到 `doongai/gpt-5.4`
- 放弃 Python `openai` 包依赖，改用原生 HTTP 请求
- 真正生成夜札正文，不再只是占位稿

这一阶段确认：
- 生成链路可用
- Hugo 发布链可用
- 状态推进可用

---

## 阶段 3：第一次文风修正

发现的问题：
- VPS 数据直灌，容易出现出戏的大数字
- 表达太直白，不像全真

因此加入：

### 1. 事件意象化压缩器
把系统数据翻译成：
- 飞蛾 / 草莽 / 鼠辈
- 堂上风雨 / 主人劳形 / 府内安稳
- 守了多少个日夜

不再把阿拉伯数字直接塞进正文。

### 2. 文风收束器
加入铁律：
- 禁止直白写“我嫉妒 / 我爱主人 / 我杀了他”
- 动作代替心理
- 句式极简
- 视角受限于门外、暗处、床榻边缘等位置

结果：
- 文字更冷
- 更像全真
- 少了现代说明味

---

## 阶段 4：去重器与摘要增强器

发现的问题：
- 文章开始互相像
- 上一篇摘要只是截正文开头，太蠢

因此加入：

### 1. 去重器
- 扫最近几篇正文
- 抽重复措辞
- 将“重复风险”喂回 prompt

### 2. 摘要增强器
- 文章生成后，再次调用模型生成 45-70 字连续性摘要
- 不再直接截正文开头

结果：
- 夜札连续性更自然
- 下一篇前情更稳定

---

## 阶段 5：系统结构升级

做过的事：
- 世界状态机升级为 v2
- 新增字段：
  - `attention_to_zhen`
  - `guilt`
  - `emptiness`
  - `vigilance`
  - `recent_scenes`
  - `recent_emotions`
  - `recent_imagery`
  - `story_arcs`

新增文件：
- `recent_memories.json`
- `future_fragments.json`
- `night_journal_stats.json`
- `manual_overrides.json`

结果：
- 系统不再只是写散篇
- 开始具备中期记忆、未来预感、剧情推进、人工导演能力

---

## 阶段 6：审核模式、初始化脚本、复盘脚本

新增：
- `draft_review/` 模式支持
- `review-first` / `auto` / `manual-only`
- `bootstrap_runtime_state.py`
- `publish_reviewed_post.sh`
- `discard_review_draft.sh`
- `analyze_journal.py`

结果：
- 系统可用于正式维护
- 不再只能盲发
- 有了检查与复盘能力

---

## 阶段 7：标题与 description 改造

发现的问题：
- 标题过于模板化：`夜札：陪伴` 这类太程序
- description 也像“引擎输出标签”

做过的事：
- 标题生成器单独跑
- description 生成器单独跑
- 要求标题像随笔、半句、意象、时间切片
- 要求 description 像页边轻注

测试后观察到：
- 标题明显变活
- description 不再出戏

---

## 阶段 8：剧情弧线减速

发现的问题：
- 连续测试几篇后，剧情推进过快
- 姐姐线 / 旧伤线推进太急

做过的事：
- 弧线推进不再只看 `post_count`
- 增加阈值条件：
  - 嫉妒值
  - 主人注意值
  - 愧意 + 空寂
- 拉大下一次触发间隔

结果：
- 剧情不再乱冲
- 节奏明显稳住

---

## 阶段 9：意象管理从“补丁式”升级为“母题簇总控”

这是很关键的一轮。

发现的问题：
- 先是“灯”过热
- 压掉灯以后，又担心出现“雨修雨、风修风、雪修雪”的循环救火

最终改成：

### 母题簇管理
- 灯簇
- 雨簇
- 风簇
- 雪簇
- 茶簇
- 剑簇
- 窗簇
- 门簇
- 夜簇

只要某个母题在最近几篇明显过热，就整簇降温，而不是只压一个字。

并且加入：
- 场景受热区约束
- 场景与意象做联动抽样

测试后观察：
- “灯”过热问题被压住
- 后续没有出现“雨修雨、风修风”的失控

这说明意象管理层已基本成型。

---

## 阶段 10：测试态清理

因为我们在 `review-first` 下跑了很多测试稿，如果不处理，系统会把这些未公开夜晚也算进自己的过去。

因此做了：
- 回拨 `world_state.json`
- 清空 `recent_memories.json`
- 重置 `night_journal_stats.json`
- 清空 `draft_review/`

结果：
- 代码层改进保留
- 测试痕迹清理
- 系统回到正式起跑态

这是当前运行态的起点。

---

## 阶段 11：GitHub 仓库整理与发布

已建立私有仓库：
- `https://github.com/wwx0wwx/quanzhen-night-journal.git`

做过的整理：
- 结构清理
- 补 README
- 补 docs
- 抽环境变量
- 保留 example 文件
- 新增 bootstrap / review workflow 工具
- 推送近期重要改动

当前仓库已同步到较新版本。

---

## 四、当前系统状态（维护判断）

### 已稳定的部分
- 生成链路
- review-first 模式
- Hugo 发布
- 标题 / description 生成
- 剧情弧线减速
- 意象簇总控
- 复盘脚本
- 运行态 / 示例态分离

### 目前不用急着再动的
- 主体结构
- systemd timer
- 中期记忆层
- 未来片段库
- override 总体设计

### 需要长期观察的
- 哪个母题下一步开始升温（目前“茶”略有抬头，但不严重）
- 标题句法是否又逐渐收缩
- 剧情弧线是否推进过慢或过快
- recent memories 是否越来越像真实生活，而非流水摘要

---

## 五、接下来最推荐的动作

### 现在最推荐
先别再继续大改。

让它：
- 按正式节奏跑几篇
- 再执行复盘：

```bash
python3 /opt/blog-src/scripts/analyze_journal.py
```

### 之后再根据真实产物决定下一刀
可能的方向：
- 若“茶”持续升温，则把茶簇纳入更严格冷却
- 若标题句法失衡，则给标题生成器加更硬的句法轮换
- 若剧情推进太慢，则轻调 story_arcs 触发门槛
- 若 recent memories 太像摘要，则单独增强“近期记忆抽取器”

---

## 六、特别提醒

### 1. 新会话接手时
先读：
1. `README-system.md`
2. `NEXT_STEPS.md`
3. `world_state.json`
4. `manual_overrides.json`
5. `recent_memories.json`
6. `night_journal_stats.json`
7. `generate_night_journal.py`
8. `analyze_journal.py`

### 2. 现在系统已经是“正式起跑态”
不要把早前 `review-first` 测试稿再算进正式前情。

### 3. 当前这版可以先跑
不要为了追求完美，再把它改得太敏感。

---

## 七、简短结论

这套系统现在已经从“实验性脚本”变成“可长期试运行的叙事系统”。

下一阶段的工作重点，不再是继续搭骨架，而是：

**让它真实运行一段，再根据复盘结果做精修。**
