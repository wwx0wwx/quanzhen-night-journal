# 全真夜札引擎 - 部署示例

## VPS 环境准备

### 系统要求

- Ubuntu 22.04 LTS
- Python 3.10+
- Git
- Hugo (静态站点生成器)

### 安装依赖

```bash
# 安装 Python 3.10+
apt update
apt install -y python3 python3-pip python3-venv

# 安装 Hugo
wget -O /tmp/hugo.deb https://github.com/gohugo/hugo/releases/download/v0.147.0/hugo_extended_0.147.0_linux-amd64.deb
dpkg -i /tmp/hugo.deb

# 验证安装
python3 --version
hugo version
```

## 项目部署

### 1. 克隆项目

```bash
# 克隆到生产目录
git clone https://github.com/wwx0wwx/quanzhen-night-journal.git /opt/blog-src
cd /opt/blog-src
```

### 2. 配置文件准备

```bash
# 复制环境变量配置
cp .env.example .env

# 编辑 .env 文件，填入 API 密钥
vim .env
```

`.env` 示例：
```
# OpenAI API 配置
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://your-proxy-url/v1
OPENAI_MODEL=gpt-5.4

# 路径配置
ENGINE_ROOT=/opt/blog-src
BLOG_OUTPUT_DIR=/var/www/shetop.ru

# 日志目录（可选）
LOG_DIR=/opt/blog-src/logs
```

### 3. 确保运行目录存在

```bash
mkdir -p /opt/blog-src/content/posts
mkdir -p /opt/blog-src/draft_review
mkdir -p /opt/blog-src/logs
mkdir -p /var/www/shetop.ru
```

### 4. 配置 systemd 定时任务

```bash
# 复制 systemd 配置到系统目录
cp automation/night-journal.service /etc/systemd/system/
cp automation/night-journal.timer /etc/systemd/system/

# 设置执行权限
chmod +x scripts/run_night_journal.sh
chmod +x scripts/run.py

# 重新加载 systemd 配置
systemctl daemon-reload

# 启用并启动定时器
systemctl enable --now night-journal.timer

# 检查定时器状态
systemctl status night-journal.timer
systemctl list-timers | grep night-journal
```

### 5. 配置 Web 服务器

如果使用 Nginx 作为前端代理：

```bash
# 安装 Nginx
apt install -y nginx

# 创建站点配置
cat > /etc/nginx/sites-available/shetop.ru << 'NGINX_EOF'
server {
    listen 80;
    server_name shetop.ru www.shetop.ru;
    
    root /var/www/shetop.ru;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # 静态资源缓存
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_EOF

# 启用站点
ln -s /etc/nginx/sites-available/shetop.ru /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### 6. SSL 证书（可选）

```bash
# 安装 Certbot
apt install -y certbot python3-certbot-nginx

# 申请证书
certbot --nginx -d shetop.ru -d www.shetop.ru
```

## 验证部署

### 1. 手动运行测试

```bash
cd /opt/blog-src
python3 scripts/run.py --mode review
```

检查 `draft_review/` 目录是否有新生成的文章。

### 2. 检查定时任务

```bash
# 查看定时器下次触发时间
systemctl list-timers | grep night-journal

# 查看日志
journalctl -u night-journal.service -f
```

### 3. 检查站点

```bash
# 检查 Hugo 构建输出
ls -la /var/www/shetop.ru/

# 检查 Nginx 配置
nginx -t
```

## 运行模式切换

### 临时切换模式

```bash
# 审稿模式（生成到草稿箱）
python3 scripts/run.py --mode review

# 手动模式（不自动发布）
python3 scripts/run.py --mode manual-only

# 自动模式（直接发布）
python3 scripts/run.py --mode auto
```

### 永久切换模式

编辑 `automation/manual_overrides.json`：

```json
{
  "mode": "auto",          // "auto", "review", "manual-only"
  "pause_publishing": false
}
```

## 故障排查

### 1. 检查日志

```bash
# 应用日志
tail -f /opt/blog-src/logs/night-journal.log

# 系统日志
journalctl -u night-journal.service -f
```

### 2. 检查 API 连接

```bash
# 运行健康检查
python3 scripts/health_check.py
```

### 3. 检查 Hugo 构建

```bash
# 手动构建
cd /opt/blog-src && hugo --destination /var/www/shetop.ru
```

## 备份策略

### 1. 状态数据备份

```bash
# 备份自动化数据
tar -czf /backup/night-journal-$(date +%Y%m%d-%H%M%S).tar.gz \
  /opt/blog-src/automation/*.json
```

### 2. 定期备份脚本

```bash
# 添加到 crontab
0 2 * * * /opt/blog-src/scripts/backup_data.sh
```

## 更新维护

### 1. 拉取最新代码

```bash
cd /opt/blog-src
git pull origin master

# 重新加载 systemd 配置（如有更新）
systemctl daemon-reload
```

### 2. 重启服务

```bash
systemctl restart night-journal.timer
```

