# 全真夜札引擎

一个具有连续性、生命感和剧情推进能力的角色叙事引擎，作为持续运转的博客系统。

## 功能特性

- **角色驱动**：核心角色「全真」，常年立于暗处守护主人的暗卫
- **情感层次**：隐忍、痴忠、清冷，对「姐姐」宿命般的嫉妒
- **文风控制**：极简、古风，动作代替心理，场景白描传递情绪
- **状态管理**：世界状态机驱动长期关系弧线（主人疲惫度、姐姐归期、全真嫉妒值等）
- **记忆系统**：多维记忆库（核心锚点/滚动记忆/未来预感）
- **现实映射**：VPS运维数据→江湖意象（SSH拦截→宵小夜闯，负载→堂上风雨）
- **智能生成**：调用 OpenAI 兼容接口生成文本
- **质量控制**：长度/禁词/模板化/重复度四重检查
- **发布管理**：支持 auto/review/manual-only 三种模式

## 技术架构

### 三层架构

| 层 | 职责 | 实现 |
|---|---|---|
| 站点层 | 静态展示 | Hugo + Nginx，输出到 /var/www/shetop.ru |
| 引擎层 | 核心逻辑 | Python 包 night_journal/ |
| 调度层 | 定时触发 | systemd timer（night-journal.timer） |

### 引擎模块划分

```
night_journal/
├── inputs/          # 输入层：状态读取、素材加载、VPS信号、近期文章
├── narrative/       # 叙事层：选题、选素材、选记忆、未来预感、剧情弧线
├── generation/      # 生成层：prompt构建、LLM调用、正文润色、标题description
├── quality/         # 质检层：质量门禁、发布守卫
├── publishing/      # 发布层：Markdown构建、模式路由、Hugo构建、git推送
└── analysis/        # 分析层：复盘统计、报告生成
```

## 部署与运行

### 环境要求

- Python 3.10+
- Hugo
- systemd（用于定时任务）

### 配置

1. 复制 `.env.example` 为 `.env`，填入 API 密钥和基础配置
2. 修改 `automation/manual_overrides.json` 设置运行模式
3. 确保 `automation/` 目录下的各配置文件正确

### 运行模式

- `auto`：自动生成并发布到 content/posts
- `review`：生成后存入 draft_review 待审
- `manual-only`：禁止自动发布

### 手动运行

```bash
# 自动模式（直接发布）
python scripts/run.py

# 审稿模式（存草稿）
python scripts/run.py --mode review

# 指定项目根目录
python scripts/run.py --root /path/to/blog

# 强制指定主题
python scripts/run.py --force-topic "守夜"

# 试运行（不写文件）
python scripts/run.py --dry-run
```

### 定时任务

通过 systemd timer 实现定时触发：

```bash
# 启用定时器
systemctl enable --now night-journal.timer

# 查看定时器状态
systemctl status night-journal.timer
systemctl list-timers | grep night-journal
```

## 文件结构

```
/opt/blog-src/                    # 主站根目录
├── scripts/
│   ├── run.py                    # 主入口脚本
│   ├── generate_night_journal.py # 旧版入口（兼容用）
│   └── health_check.py           # 健康检查脚本
├── automation/                   # 状态数据文件
│   ├── world_state.json          # 世界状态机
│   ├── manual_overrides.json     # 人工干预开关
│   ├── *.json                    # 各种素材库
│   └── night-journal.timer/service # systemd配置
├── content/posts/                # 正式发布文章
├── draft_review/                 # 审核草稿
├── logs/                         # 运行日志
├── hugo.toml                     # Hugo配置
└── .env                          # API key / 路径配置
```

## 状态文件说明

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

## 维护与复盘

- `analyze_journal.py`：一键统计发文成功率、高频意象、情绪分布、剧情进度
- `health_check.py`：检查 API 连接、文件权限、磁盘空间等
- 日志：/opt/blog-src/logs/night-journal.log

## 开发

本项目采用模块化重构，解决了早期单一大脚本导致的代码过度耦合问题。

### 测试

```bash
# 运行所有测试
python -m pytest tests/

# 查看覆盖率
python -m pytest tests/ --cov=night_journal
```

所有核心逻辑都有单元测试覆盖，确保重构安全性。

