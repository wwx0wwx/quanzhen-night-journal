# 全真之夜日记 - 部署指南

## 部署前准备

- 确认目标服务器系统环境（Ubuntu/Debian/CentOS）
- 准备域名解析（A 记录指向服务器 IP）
- 获取 AI API 密钥及端点信息
- 确认服务器时间同步（重要：影响 SSL 证书）

## 部署步骤

### 1. 环境依赖安装

```bash
# Ubuntu/Debian
apt update && apt install -y python3 python3-pip git curl wget

# CentOS/RHEL
yum install -y python3 python3-pip git curl wget
```

### 2. Hugo 安装

- 官方下载：https://gohugo.io/getting-started/installing/
- 推荐版本：0.146.0+ Extended

```bash
wget https://github.com/gohugoio/hugo/releases/download/v0.146.0/hugo_extended_0.146.0_Linux-64bit.tar.gz
tar -xzf hugo_extended_0.146.0_Linux-64bit.tar.gz
sudo mv hugo /usr/local/bin/
```

### 3. 代码部署

```bash
git clone https://github.com/wwx0wwx/quanzhen-night-journal.git
cd quanzhen-night-journal
pip3 install -r requirements.txt
```

### 4. 配置检查

```bash
# 检查 Python 脚本编码
file scripts/*.py

# 确保所有文件为 UTF-8
find . -name "*.py" -exec sed -i 's/\r$//' {} \;
```

### 5. 运行测试

```bash
python3 scripts/generate_night_journal.py --test
```

## Nginx 配置

### 静态文件服务

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /var/www/quanzhen-night-journal/public;
        index index.html;
        try_files $uri $uri/ =404;
    }
    
    # UTF-8 编码设置
    charset utf-8;
    charset_types text/html text/plain text/css application/javascript;
}
```

### HTTPS 配置（Let's Encrypt）

```bash
# 安装 certbot
apt install -y certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com

# 自动续期
crontab -e
# 添加：0 3 * * * certbot renew --quiet
```

## 常见问题

### 1. Hugo 主题兼容性

- 错误：`Module "PaperMod" is not compatible with this Hugo version`
- 解决：升级 Hugo 到 0.146.0+ 或降级主题版本

### 2. 字符编码问题

- 确保所有 Python 脚本以 UTF-8 保存
- HTML 中添加 `<meta charset="utf-8">`
- Nginx 配置中设置 `charset utf-8`

### 3. Front Matter 解析失败

- 检查 YAML 格式是否正确
- 确保没有混用 Tab 和空格
- 特殊字符使用引号包裹

## 部署检查清单

- [ ] 系统依赖已安装
- [ ] Hugo 版本 >= 0.146.0
- [ ] Python 依赖已安装
- [ ] 域名解析生效
- [ ] SSL 证书已配置
- [ ] 文件编码为 UTF-8
- [ ] 测试生成成功
- [ ] Nginx 配置正确

## 版本发布

```bash
# 创建标签
git tag -a v1.0.x -m "版本说明"

# 推送标签
git push origin v1.0.x

# 创建 Release（GitHub UI 或 API）
```
