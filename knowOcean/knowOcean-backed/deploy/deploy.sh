#!/bin/bash
# ── KnowOcean Backend 快速部署脚本 ──
# 用法: bash deploy/deploy.sh [docker|systemd]
#   docker  - Docker 容器化部署 (推荐)
#   systemd - 传统 systemd 部署

set -euo pipefail

MODE="${1:-docker}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "╔══════════════════════════════════════╗"
echo "║  KnowOcean Backend Deploy           ║"
echo "║  Mode: $MODE"
echo "╚══════════════════════════════════════╝"

# ── 前置检查 ──
check_env() {
    if [ ! -f ".env" ]; then
        echo "❌ 缺少 .env 文件"
        echo "   请从 .env.production 复制并填入真实值:"
        echo "   cp .env.production .env"
        exit 1
    fi
    echo "✅ .env 配置文件存在"
}

check_connections() {
    echo ""
    echo "🔍 检查外部服务连接..."

    # 从 .env 读取配置
    set -a; source .env; set +a

    # PostgreSQL
    if command -v pg_isready &>/dev/null; then
        pg_isready -h "${DATABASE_HOST}" -p "${DATABASE_PORT}" -U "${DATABASE_USER}" -d "${DATABASE_NAME}" \
            && echo "  ✅ PostgreSQL ${DATABASE_HOST}:${DATABASE_PORT}" \
            || echo "  ⚠️  PostgreSQL 连接失败"
    else
        echo "  ⏭️  跳过 PostgreSQL 检查 (pg_isready 未安装)"
    fi

    # Redis
    if command -v redis-cli &>/dev/null; then
        redis-cli -u "${REDIS_URL}" ping &>/dev/null \
            && echo "  ✅ Redis ${REDIS_URL}" \
            || echo "  ⚠️  Redis 连接失败"
    else
        echo "  ⏭️  跳过 Redis 检查 (redis-cli 未安装)"
    fi

    echo "  ℹ️  请确认 ES/MinIO 服务可访问"
}

# ── Docker 部署 ──
deploy_docker() {
    echo ""
    echo "🐳 Docker 容器化部署"

    # 确保使用生产配置
    if [ ! -f ".env" ]; then
        cp .env.production .env
        echo "⚠️  已从 .env.production 生成 .env，请编辑后重新运行"
        exit 1
    fi

    # 构建镜像
    echo "📦 构建 Docker 镜像..."
    docker compose build --no-cache

    # 停止旧容器
    echo "🛑 停止旧容器..."
    docker compose down --remove-orphans 2>/dev/null || true

    # 启动
    echo "🚀 启动容器..."
    docker compose up -d

    # 等待健康检查
    echo "⏳ 等待服务就绪..."
    for i in $(seq 1 20); do
        if curl -sf http://localhost:10001/health >/dev/null 2>&1; then
            echo "✅ KnowOcean Backend 已启动 (http://localhost:10001)"
            break
        fi
        sleep 2
    done

    echo ""
    echo "📋 常用命令:"
    echo "  docker compose logs -f          # 查看日志"
    echo "  docker compose restart          # 重启"
    echo "  docker compose down             # 停止"
    echo "  docker compose exec backend bash # 进入容器"
}

# ── Systemd 部署 ──
deploy_systemd() {
    echo ""
    echo "🖥️  Systemd 传统部署"

    # 安装依赖
    echo "📦 安装 Python 依赖..."
    if [ ! -d ".venv" ]; then
        python3.12 -m venv .venv
    fi
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -e ".[dev]"

    # 安装服务
    echo "🔧 安装 systemd 服务..."
    sudo cp deploy/knowocean-backend.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable knowocean-backend

    # 启动
    echo "🚀 启动服务..."
    sudo systemctl restart knowocean-backend

    # 状态
    echo ""
    echo "📋 常用命令:"
    echo "  sudo systemctl status knowocean-backend  # 查看状态"
    echo "  sudo journalctl -u knowocean-backend -f  # 查看日志"
    echo "  sudo systemctl restart knowocean-backend # 重启"
}

# ── 主流程 ──
check_env
check_connections

case "$MODE" in
    docker)
        deploy_docker
        ;;
    systemd)
        deploy_systemd
        ;;
    *)
        echo "❌ 未知模式: $MODE (可选: docker, systemd)"
        exit 1
        ;;
esac

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  🎉 部署完成                        ║"
echo "╚══════════════════════════════════════╝"
