# 全真夜札系统（私有迁移模板）

这是 **全真夜札** 的 Hugo 博客与自动发文系统仓库。

当前仓库包含：
- Hugo 站点源码
- 夜札生成脚本
- 世界状态 / 记忆 / 素材池
- systemd 定时任务模板
- Nginx + VPS 迁移样例文档

## 快速迁移

### 1. 拉取代码

```bash
git clone --recurse-submodules <your-private-repo-url> /opt/blog-src
```

### 2. 准备运行时配置

复制 `.env.example` 为 `.env`，填入真实值：

```bash
cp /opt/blog-src/.env.example /opt/blog-src/.env
```

重点字段：
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `ENGINE_ROOT`
- `BLOG_OUTPUT_DIR`

### 3. 一键初始化新 VPS

```bash
bash /opt/blog-src/scripts/bootstrap_server.sh <domain>
```

例如：

```bash
bash /opt/blog-src/scripts/bootstrap_server.sh iuaa.de
```

这个脚本会完成：
- 安装基础依赖
- 安装 Hugo（若缺失）
- 创建发布目录
- 安装 systemd service/timer
- 配置 Nginx
- 首次构建站点

### 4. 启用 HTTPS

```bash
certbot --nginx -d <domain> -d www.<domain> --non-interactive --agree-tos -m admin@<domain> --redirect
```

### 5. 验证系统

```bash
systemctl status night-journal.timer --no-pager
systemctl status night-journal.service --no-pager
curl -I http://<domain>
curl -I https://<domain>
```

## 详细部署样例

完整实战步骤见：

- `DEPLOY_EXAMPLE.md`

## 不建议直接入库的内容

已通过 `.gitignore` 排除：
- `.env`
- `logs/`
- `automation/backups/`
- Python 缓存
- `.hugo_build.lock`

后续若要继续标准化，可再补：
- 运行态与示例态分离
- 初始化状态脚本
- 发布审核工作流说明
