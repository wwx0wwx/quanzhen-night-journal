# 全真夜札系统 — 需求规格文档

> 整理自主人 2026-03-25 口述，属下存档备忘。

---

## 一、核心目标

搭建一个具有**连续性、生命感和剧情推进能力**的角色叙事引擎，作为持续运转的日志系统，而非简单的定时发文脚本。

---

## 二、角色与文风

- 核心角色：**全真** — 常年立于暗处守护主人的暗卫
- 特质：隐忍、痴忠、清冷，带有对「姐姐」宿命般的嫉妒
- 文风：极简、古风，动作代替心理，场景白描传递情绪
- 严禁：直白的现代网络化情感宣泄

---

## 三、发布策略

- 目标博客：Hugo 静态博客，Markdown 格式输出
- 域名：shetop.ru
- 发布频率：每周三篇（周二/四/六），UTC 16:00 触发
- 触发方式：systemd timer（不依赖大模型会话记忆）
- 运行模式：
  - `auto` — 自动直发到 content/posts（**开发测试阶段常开**）
  - `review-first` — 落入 draft_review 待审（关键剧情节点使用）
  - `manual-only` / `pause_publishing` — 紧急暂停

---

## 四、技术架构

### 三层宏观架构

| 层 | 职责 | 实现 |
|---|---|---|
| 站点层 | 静态展示 | Hugo + Nginx + Let's Encrypt，输出到 /var/www/shetop.ru |
| 引擎层 | 叙事决策 + 生成 + 质检 + 发布 | Python 包 night_journal/ |
| 调度层 | 定时触发 | systemd timer（night-journal.timer） |

### 引擎层模块划分（night_journal/）

```
night_journal/
├── inputs/          输入层：状态读取、素材加载、VPS信号、近期文章
├── narrative/       叙事层：选题、选素材、选记忆、未来预感、剧情弧线
├── generation/      生成层：prompt构建、LLM调用、正文润色、标题description
├── quality/         质检层：质量门禁、发布守卫
└── publishing/      发布层：Markdown构建、模式路由、Hugo构建、git推送
```

### 状态机与记忆系统

| 文件 | 职责 |
|---|---|
| world_state.json | 世界状态机：主人疲惫/姐姐压力/全真嫉妒值/剧情弧线进度 |
| memory_anchors.json | 不可变核心记忆锚点库 |
| recent_memories.json | 滚动积累的近期小事（中期记忆） |
| future_fragments.json | 预示命运走向的未来片段 |
| topic_rules.json | 题材库与约束规则 |
| imagery_pool.json | 意象素材库（视觉/声音/气味/触感） |
| scene_pool.json | 场景库 |
| emotion_pool.json | 情绪库（主情绪/辅情绪/配对提示） |
| event_map_rules.json | VPS运维数据→江湖意象映射规则 |
| manual_overrides.json | 人工干预开关 |
| night_journal_stats.json | 运行统计 |

### 现实事件映射（Reality Mapping Engine）

VPS 真实运维数据 → 全真视角江湖意象：
- SSH 拦截次数 → 宵小夜闯
- 系统负载 → 堂上风雨
- Uptime → 守夜天数
- Let's Encrypt 续签 → 江湖凭信

---

## 五、质量控制

1. **数据意象化**：Python层拦截服务器数值，压缩为模糊古风意象，禁止直接输出冰冷数字
2. **意象簇总控降温**：动态监控近期文章，某类意象过热则抑制整组关联词汇
3. **二段式编辑链**：正文生成 → 冷处理润色 → 单独生成标题+description
4. **质量门禁**：长度/禁词/模板化/重复度四项检查，失败最多修3次

---

## 六、运维与复盘

- `analyze_journal.py`：一键统计发文成功率、高频意象、情绪分布、剧情进度
- 三种运行模式赋予导演级干预能力
- 日志：/opt/blog-src/logs/night-journal.log

---

## 七、开发环境说明

- **本机 VPS**：既是生产环境，也是开发测试环境
- **生产站点根目录**：`/opt/blog-src`
- **开发工作区**：`/root/.openclaw/workspace/quanzhen-night-journal`
- **部署策略**：开发版本直接部署到 /opt/blog-src，本机即生产
- **测试策略**：auto 模式常开，直观看效果；关键节点切 review-first

---

## 八、已知问题待修复

1. SyntaxWarning: invalid escape sequence 第148行
2. config.py 默认 BLOG_OUTPUT_DIR 仍为旧域名 /var/www/iuaa.de
3. 开发版本（night_journal/ 包）尚未部署到 /opt/blog-src
4. draft_review/ 有积压草稿待处理
