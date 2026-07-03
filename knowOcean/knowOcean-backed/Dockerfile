# ── KnowOcean Python Backend ──
# 多阶段构建，最终镜像约 300MB
# 宝塔面板 Docker 部署专用

FROM python:3.12-slim AS builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖声明文件
COPY pyproject.toml .

# 安装 Python 依赖到 /install 目录
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --target=/install . && \
    pip install --no-cache-dir --target=/install uvicorn[standard]

# ── 运行阶段 ──
FROM python:3.12-slim

WORKDIR /app

# 运行时系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制依赖
COPY --from=builder /install /usr/local/lib/python3.12/site-packages

# 复制应用源码
COPY src/ ./src/
COPY prompts/ ./prompts/
COPY pyproject.toml .

# 创建上传目录
RUN mkdir -p uploads && chmod 755 uploads

# 非 root 用户
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:10001/health || exit 1

EXPOSE 10001

# 启动命令
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "10001", "--workers", "2"]
