"""
应用主入口 - FastAPI 应用工厂和 Uvicorn 启动配置。
"""
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 将项目根目录加入 Python 路径，确保导入正常
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.webhook import router as webhook_router
from src.api.admin import router as admin_router
from src.api.dashboard import router as dashboard_router
from src.utils.logger import logger
from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - 启动和关闭时的初始化/清理逻辑"""
    # === 启动阶段 ===
    logger.info("=" * 50)
    logger.info("🚀 PDD AI 智能客服机器人启动中...")
    logger.info(f"   LLM 模型: {settings.main_chat_model}")
    logger.info(f"   API Key 数量: {len(settings.zhipu_key_list)}")
    logger.info(f"   最大历史长度: {settings.max_history_length}")
    logger.info(f"   数据库: {settings.db_url}")
    logger.info("=" * 50)

    # 确保目录存在
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data/sqlite", exist_ok=True)
    os.makedirs("data/chroma", exist_ok=True)

    # === 初始化 SQLite 数据库（建表，幂等）===
    try:
        from src.models.database import create_tables
        create_tables()
        logger.info("✅ SQLite 数据库初始化完成（messages / sessions / escalations 表）")
    except Exception as e:
        logger.error(f"❌ SQLite 初始化失败: {e}")

    # 预初始化 LLM 客户端（验证配置）
    from src.core.llm_client import get_llm_client
    try:
        get_llm_client()
        logger.info("✅ LLM 客户端初始化成功")
    except Exception as e:
        logger.error(f"❌ LLM 客户端初始化失败: {e}")

    yield  # 应用运行中

    # === 关闭阶段 ===
    logger.info("👋 PDD AI 客服机器人正在关闭...")


# 创建 FastAPI 应用
app = FastAPI(
    title="PDD E-Commerce AI Bot",
    description="基于 RAG + LLM + SQLite 持久化的拼多多智能客服系统",
    version="0.2.0",
    lifespan=lifespan,
)

# 允许跨域（开发阶段）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件 (必须在路由注册之前)
if not os.path.exists("static"):
    os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ===== P1-1: 引入 Redis 限流中间件 =====
import redis
from fastapi.responses import JSONResponse
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # 仅针对 API 接口限流
    if request.url.path.startswith("/api/v1/chat"):
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}"
        
        # 简单滑动窗口限流：每分钟 60 次
        current_count = redis_client.incr(key)
        if current_count == 1:
            redis_client.expire(key, 60)
            
        if current_count > 60:
            logger.warning(f"触发限流 | IP: {client_ip} | 请求已被拦截")
            return JSONResponse(
                status_code=429,
                content={"status": "error", "message": "请求过于频繁，请稍后再试 (Too Many Requests)"}
            )
            
    response = await call_next(request)
    return response

# 注册路由
app.include_router(dashboard_router, prefix="", tags=["可视化大屏"])      # 首页仪表盘
app.include_router(webhook_router, prefix="/api/v1", tags=["客服接口"])
app.include_router(admin_router, prefix="/admin", tags=["管理后台"])     # 明确后台路径


@app.get("/api_root", tags=["系统"])
async def api_root():
    return {
        "app": "PDD E-Commerce AI Bot",
        "version": "0.2.0",
        "status": "running",
        "docs": "/docs",
        "dashboard": "/",
        "admin": "/admin",
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常拦截：防止未处理异常导致进程崩溃或服务假死"""
    logger.error(f"全局未捕获异常 | URI: {request.url.path} | 错误: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "服务器内部未知错误，已记录"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8100,
        reload=True,  # 开发模式热重载
        log_level="info",
    )
