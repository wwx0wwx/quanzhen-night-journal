# 数据库升级与备份

## 架构概述

全真夜记使用 SQLite（WAL 模式），数据库文件位于 Docker volume `app_data` 中的 `/app/data/quanzhen.db`。

完整表结构定义见 `doc/database_schema.sql`。

## 自动迁移

系统启动时会自动检测并补全缺失的列和表。迁移逻辑位于 `backend/database.py` 的 `init_database()` 函数中：

```python
async def _ensure_column_exists(conn, table, column, ddl):
    # 检查列是否存在，不存在则执行 ALTER TABLE
```

每次版本更新后重启容器，新增的数据库字段会自动补全，无需手动执行 SQL。

## 手动升级步骤

如果需要手动执行数据库变更：

```bash
# 1. 备份数据库
docker exec qz-core python -c "
import shutil
shutil.copy2('/app/data/quanzhen.db', '/app/data/quanzhen.db.backup')
print('backup created')
"

# 2. 执行 SQL（示例）
docker exec qz-core python -c "
import sqlite3
conn = sqlite3.connect('/app/data/quanzhen.db')
conn.execute('ALTER TABLE personas ADD COLUMN new_field TEXT NOT NULL DEFAULT \"\"')
conn.commit()
conn.close()
print('migration done')
"

# 3. 重启服务
docker compose restart core
```

## 备份与恢复

### 通过管理后台备份

1. 进入 `/admin/ghost` 页面
2. 点击「创建数据库备份」
3. 在备份列表中点击「下载」

### 通过命令行备份

```bash
# 导出数据库文件
docker cp qz-core:/app/data/quanzhen.db ./quanzhen-backup-$(date +%Y%m%d).db

# 导出 Hugo 内容
docker cp qz-hugo:/hugo/content ./content-backup/
```

### 恢复数据库

```bash
# 停止服务
docker compose stop core

# 替换数据库文件
docker cp ./quanzhen-backup.db qz-core:/app/data/quanzhen.db

# 重启服务
docker compose start core
```

### 定时备份

系统内置了定时备份任务（通过 APScheduler），可在 `/admin/ghost` 页面查看备份历史。备份文件保存在 `/app/data/backups/` 目录中。

## JWT Secret 轮换

```bash
# 生成新密钥
openssl rand -base64 32

# 更新 .env 文件中的 JWT_SECRET
# 重启服务
docker compose restart core

# 注意：所有现有登录会话将失效，用户需重新登录
```

## 注意事项

- SQLite 不支持并发写入，但 WAL 模式允许并发读写
- 单用户博客场景下 SQLite 性能完全足够
- 备份时建议先停止 core 服务，避免写入冲突
- 每次升级前务必备份数据库
