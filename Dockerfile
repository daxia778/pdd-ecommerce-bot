# ============================================================
#   多阶段构建 — PDD AI 智能客服后端
#   Stage 1: 安装依赖（缓存层）
#   Stage 2: 精简运行镜像
# ============================================================

# --- Stage 1: 依赖安装 ---
FROM python:3.11-slim AS builder

WORKDIR /build

# 先复制依赖清单，利用 Docker 缓存
COPY requirements.txt .

# 安装编译依赖（部分包如 psycopg2 需要 gcc）
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt && \
    pip install --no-cache-dir --prefix=/install pytest pytest-asyncio httpx && \
    apt-get purge -y gcc && apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# --- Stage 2: 运行环境 ---
FROM python:3.11-slim

LABEL maintainer="daxia778"
LABEL description="PDD E-Commerce AI Bot — RAG + LLM + SQLite 智能客服系统"

WORKDIR /app

# 从 builder 复制已编译的 Python 包
COPY --from=builder /install /usr/local

# 安装运行时系统依赖（libpq 给 psycopg2，sqlite3 调试用）
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 sqlite3 curl && \
    rm -rf /var/lib/apt/lists/*

# 复制项目代码
COPY . .

# 创建数据目录（运行时会挂载 volume）
RUN mkdir -p data/sqlite data/chroma data/output logs

# 环境变量默认值
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8100

# 暴露端口
EXPOSE ${PORT}

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100", "--workers", "1"]
