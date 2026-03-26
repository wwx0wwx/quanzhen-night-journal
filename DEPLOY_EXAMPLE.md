# 全真夜札系统：新 VPS 复刻部署样例

这份文档记录如何在一台全新的 Ubuntu VPS 上，完整复刻 **全真夜札博客 + 自动发文系统**，并完成访问验证与 HTTPS 收口。

适用场景：
- 新机器迁移
- 灾备恢复
- 复制一套相同结构到另一台 VPS

---

## 1. 目标结构

部署完成后，核心目录如下：

- 代码目录：`/opt/blog-src`
- 站点发布目录：`/var/www/<domain>`
- systemd service：`/etc/systemd/system/night-journal.service`
- systemd timer：`/etc/systemd/system/night-journal.timer`
- Nginx 站点配置：`/etc/nginx/sites-available/<domain>`

---

## 2. 前置条件

在开始前，请确保：

1. VPS 已可 SSH 登录
2. 域名已经解析到 VPS IP
3. 仓库代码可获取（GitHub 私有仓库，或从旧机 rsync）
4. 你手里有运行时模型配置：
   - `OPENAI_API_KEY`
   - `OPENAI_BASE_URL`
   - `OPENAI_MODEL`

> 注意：这些敏感配置**不要直接提交到公开仓库**。私有仓库虽然风险较低，仍建议最终切成 `.env.example` + 本地真实 `.env`。

---

## 3. 安装基础依赖

在新机执行：

```bash
apt-get update
apt-get install -y git nginx python3 python3-venv python3-pip certbot python3-certbot-nginx rsync curl jq unzip
```

如果系统中没有 Hugo，可安装扩展版 Hugo：

```bash
HUGO_VER=0.147.0
curl -L "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VER}/hugo_extended_${HUGO_VER}_linux-amd64.tar.gz" -o /tmp/hugo.tgz
tar -xzf /tmp/hugo.tgz -C /tmp
install -m 0755 /tmp/hugo /usr/local/bin/hugo
```

验证：

```bash
hugo version
python3 --version
nginx -v
```

---

## 4. 获取代码

### 方案 A：从 GitHub 仓库拉取

```bash
git clone --recurse-submodules <your-repo-url> /opt/blog-src
```

若仓库已存在：

```bash
git -C /opt/blog-src fetch --all --prune
git -C /opt/blog-src reset --hard origin/master
git -C /opt/blog-src submodule update --init --recursive
```

### 方案 B：从旧机器直接同步

如果新机暂时不能直接拉私有仓库，可从旧机同步：

```bash
rsync -az --delete \
  --exclude '.git' \
  --exclude '.env' \
  --exclude 'logs/' \
  --exclude 'automation/backups/' \
  /opt/blog-src/ root@NEW_VPS:/opt/blog-src/
```

---

## 5. 准备运行时目录与 .env

```bash
mkdir -p /opt/blog-src/logs
mkdir -p /opt/blog-src/draft_review
mkdir -p /opt/blog-src/automation/backups
mkdir -p /var/www/<domain>
```

创建 `/opt/blog-src/.env`：

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://ai.dooo.ng/v1/chat/completions
OPENAI_MODEL=gpt-5.4
ENGINE_ROOT=/opt/blog-src
BLOG_OUTPUT_DIR=/var/www/<domain>
```

---

## 6. 配置 systemd

复制模板：

```bash
cp /opt/blog-src/automation/night-journal.service /etc/systemd/system/night-journal.service
cp /opt/blog-src/automation/night-journal.timer /etc/systemd/system/night-journal.timer
systemctl daemon-reload
systemctl enable --now night-journal.timer
```

检查：

```bash
systemctl status night-journal.timer --no-pager
systemctl status night-journal.service --no-pager
systemctl list-timers --all | grep night-journal
```

默认定时配置：

- `Tue,Thu,Sat 16:00:00 UTC`

---

## 7. 配置 Nginx

创建 `/etc/nginx/sites-available/<domain>`：

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name <domain> www.<domain>;
    root /var/www/<domain>;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

启用站点：

```bash
ln -sf /etc/nginx/sites-available/<domain> /etc/nginx/sites-enabled/<domain>
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable --now nginx
systemctl reload nginx
```

---

## 8. 首次构建站点

```bash
cd /opt/blog-src
hugo --destination /var/www/<domain>
```

验证本机：

```bash
curl -I http://127.0.0.1
```

---

## 9. 验证自动发文系统

手动触发一次：

```bash
systemctl start night-journal.service
```

检查状态：

```bash
systemctl status night-journal.service --no-pager
```

建议同时检查：

```bash
ls -la /opt/blog-src/draft_review
sed -n '1,120p' /opt/blog-src/automation/world_state.json
```

若系统处于 `review-first` 模式，成功后通常会看到：
- `draft_review/` 新增一篇草稿
- `world_state.json` 中 `post_count` 增长
- `last_successful_post_at` 更新

---

## 10. 配置 HTTPS

域名解析已生效后，执行：

```bash
certbot --nginx -d <domain> -d www.<domain> --non-interactive --agree-tos -m admin@<domain> --redirect
```

成功后检查：

```bash
curl -I https://<domain>
curl -I https://www.<domain>
```

Certbot 会自动安装续期任务。

---

## 11. 本次实战样例

本次已验证通过的一组真实参数：

- 新 VPS IP：`103.52.154.208`
- 域名：`iuaa.de`
- 站点目录：`/var/www/iuaa.de`
- 代码目录：`/opt/blog-src`

实测结果：

- `http://103.52.154.208` → `200 OK`
- `http://iuaa.de` → `200 OK`
- `https://iuaa.de` → `200 OK`
- `https://www.iuaa.de` → `200 OK`
- `night-journal.timer` 已 active
- `night-journal.service` 手动执行成功
- 自动发文验证通过，新增审核草稿，`world_state.json` 已推进

---

## 12. 迁移时的注意事项

### 建议提交到仓库的内容
- `automation/*.json`
- `automation/*.md`
- `automation/*.service`
- `automation/*.timer`
- `scripts/*.py`
- `scripts/*.sh`
- Hugo 配置与内容目录

### 不建议直接提交的内容
- `.env`
- `logs/`
- `automation/backups/`
- Python 缓存
- `.hugo_build.lock`

### 建议后续再做的一步
把当前私有仓库继续打磨成更标准的迁移模板：

- 增加 `.env.example`
- 增加 `DEPLOY.md`
- 增加一键部署脚本 `scripts/bootstrap_server.sh`
- 视需要把运行态 JSON 与“示例状态”拆开

---

## 13. 最小验收清单

部署完后，至少确认以下几点：

- [ ] `hugo version` 正常
- [ ] `nginx -t` 正常
- [ ] `systemctl status night-journal.timer` 为 active
- [ ] `systemctl status night-journal.service` 可成功执行
- [ ] `curl -I http://<domain>` 返回 200
- [ ] `curl -I https://<domain>` 返回 200
- [ ] `draft_review/` 或 `content/posts/` 有新产物
- [ ] `world_state.json` 有推进

---

若只是照着这份文档走，一台新机已经足够把整套夜札系统重新立起来。
