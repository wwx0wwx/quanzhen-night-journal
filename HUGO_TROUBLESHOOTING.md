# Hugo 兼容性问题解决

## 问题现象

- **Hugo 运行版本**：0.131.0
- **主题版本**：PaperMod (latest)
- **错误信息**：`Module "PaperMod" is not compatible with this Hugo version: Min 0.146.0`

## 触发原因

### 1. 版本不匹配

- **问题**：Hugo 运行版本过低，与主题要求版本不兼容
- **详细错误**：`ERROR render of "home" failed: partial "google_analytics.html" not found`
- **影响**：主题无法渲染，首页为空页
- **解决方案**：创建简易 HTML 替换方案

### 2. 设计方案

#### 方案 1: 升级 Hugo

- **预期信息**：Hugo 0.147.0 + Extended + PaperMod 主题
- **实现难点**：服务器大型主题依赖
- **实现复杂度**：高

#### 方案 2: 降级主题版本

- **预期信息**：使用 PaperMod v6.x（兼容 Hugo 0.131.x）
- **实现难点**：功能可能受限
- **实现复杂度**：中

#### 方案 3: 静态 HTML 输出

- **预期信息**：绕过 Hugo 主题系统
- **实现难点**：需要重写模板
- **实现复杂度**：高

## 解决方案

### 推荐：升级 Hugo

```bash
# 1. 删除旧版本
sudo rm /usr/local/bin/hugo

# 2. 下载新版本（Extended）
wget https://github.com/gohugoio/hugo/releases/download/v0.147.0/hugo_extended_0.147.0_Linux-64bit.tar.gz

# 3. 解压安装
tar -xzf hugo_extended_0.147.0_Linux-64bit.tar.gz
sudo mv hugo /usr/local/bin/

# 4. 验证
hugo version
```

### 备选：使用兼容主题版本

```bash
# 1. 进入主题目录
cd themes/PaperMod

# 2. 查看可用版本
git tag -l

# 3. 切换到兼容版本
git checkout v6.3.2
```

## 验证步骤

```bash
# 1. 清理缓存
hugo mod clean

# 2. 更新模块
hugo mod get -u

# 3. 本地测试
hugo server -D

# 4. 检查输出
hugo --verbose
```

## 注意事项

1. **Extended 版本**：某些主题功能需要 Hugo Extended 版本
2. **模块系统**：Hugo 0.93.0+ 引入模块系统，主题可能依赖此功能
3. **模板语法**：新版本可能引入模板语法变更
