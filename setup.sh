#!/bin/bash

# Quanzhen Night Journal - Setup Script
# 一键初始化夜札引擎环境

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Default installation path
ENGINE_ROOT="${ENGINE_ROOT:-$(pwd)}"
DEFAULT_BLOG="${DEFAULT_BLOG:-$HOME/blog-output}"

log_info "=== 全真夜札引擎 - 初始化脚本 ==="
log_info "引擎目录: $ENGINE_ROOT"
log_info "博客输出目录: ${BLOG_OUTPUT_DIR:-$DEFAULT_BLOG}"
echo ""

# Create .env from example if not exists
if [ ! -f "$ENGINE_ROOT/.env" ]; then
    log_info "创建 .env 配置文件..."
    cp "$ENGINE_ROOT/.env.example" "$ENGINE_ROOT/.env"

    # Replace default paths in .env
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|^ENGINE_ROOT=.*|ENGINE_ROOT=$ENGINE_ROOT|" "$ENGINE_ROOT/.env"
        sed -i '' "s|^BLOG_OUTPUT_DIR=.*|BLOG_OUTPUT_DIR=$DEFAULT_BLOG|" "$ENGINE_ROOT/.env"
    else
        # Linux
        sed -i "s|^ENGINE_ROOT=.*|ENGINE_ROOT=$ENGINE_ROOT|" "$ENGINE_ROOT/.env"
        sed -i "s|^BLOG_OUTPUT_DIR=.*|BLOG_OUTPUT_DIR=$DEFAULT_BLOG|" "$ENGINE_ROOT/.env"
    fi

    log_warn ".env 已创建，请编辑以下配置:"
    log_warn "  - OPENAI_API_KEY: OpenAI API 密钥"
    log_warn "  - OPENAI_BASE_URL: API 基础 URL（默认: https://ai.dooo.ng/v1/chat/completions）"
    log_warn "  - OPENAI_MODEL: 模型名称（默认: gpt-5.4）"
    log_warn "  - BLOG_OUTPUT_DIR: 博客输出目录"
    echo ""
    log_warn "编辑完成后运行: $0 --continue"
    exit 0
else
    log_info ".env 已存在"
fi

# Check if API key is configured
source "$ENGINE_ROOT/.env"
if [ "$OPENAI_API_KEY" = "your_api_key_here" ] || [ -z "$OPENAI_API_KEY" ]; then
    log_error "请先在 .env 中配置 OPENAI_API_KEY"
    exit 1
fi

# Create runtime state from templates
log_info "初始化运行时状态..."
cd "$ENGINE_ROOT/automation"

for template in *.example.json; do
    if [ -f "$template" ]; then
        target="${template%.example.json}.json"
        if [ ! -f "$target" ]; then
            cp "$template" "$target"
            log_info "创建: $target"
        fi
    fi
done

# Create necessary directories
log_info "创建目录结构..."
mkdir -p "$ENGINE_ROOT/content/posts"
mkdir -p "$ENGINE_ROOT/draft_review"
mkdir -p "${LOG_DIR:-$ENGINE_ROOT/logs}"
mkdir -p "$BLOG_OUTPUT_DIR"

# Make scripts executable
log_info "设置脚本权限..."
chmod +x "$ENGINE_ROOT/scripts/run_night_journal.sh"
chmod +x "$ENGINE_ROOT/scripts/publish_reviewed_post.sh"
chmod +x "$ENGINE_ROOT/scripts/discard_review_draft.sh" 2>/dev/null || true

# Install Python dependencies if needed
if ! command -v python3 &> /dev/null; then
    log_warn "python3 未安装，请先安装 Python 3"
else
    log_info "Python 3 已安装: $(python3 --version)"
fi

log_info "=== 初始化完成 ==="
echo ""
log_info "手动测试运行:"
echo "  cd $ENGINE_ROOT && bash scripts/run_night_journal.sh"
echo ""
log_info "设置 systemd 定时任务（可选）:"
echo "  sudo cp $ENGINE_ROOT/automation/night-journal.service /etc/systemd/system/"
echo "  sudo cp $ENGINE_ROOT/automation/night-journal.timer /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable --now night-journal.timer"
echo ""
