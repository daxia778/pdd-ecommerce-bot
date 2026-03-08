"""
应用主入口 - FastAPI 应用工厂和 Uvicorn 启动配置。
"""

import asyncio  # P0-1: 移至顶部，避免 lifespan 预热时 name error
import os
import sys
import uuid
from contextlib import asynccontextmanager

from cachetools import TTLCache
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

# 将项目根目录加入 Python 路径，确保导入正常
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from src.api.admin import auth_router
from src.api.admin import router as admin_router
from src.api.dashboard import public_router, ws_router
from src.api.dashboard import router as dashboard_router
from src.api.webhook import router as webhook_router
from src.utils.logger import logger


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
    os.makedirs("data/output", exist_ok=True)  # PPT 生成输出目录

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

    # P1-4: 安全校验 — 生产环境强制拦截弱 JWT 密钥
    _app_env = os.getenv("APP_ENV", "development").lower()
    _jwt_key = getattr(settings, "jwt_secret_key", "")
    _jwt_is_weak = not _jwt_key or _jwt_key == "dev-secret-key-change-in-prod" or len(_jwt_key) < 32
    if _jwt_is_weak:
        if _app_env == "production":
            # 生产环境：硬性拦截，阻止服务以不安全状态启动
            raise SystemExit(
                "❌ [FATAL] 生产环境禁止使用弱 JWT 密钥！\n"
                "   请在 .env 中设置不少于 32 字符的随机字符串：\n"
                "   JWT_SECRET_KEY=$(openssl rand -hex 32)"
            )
        else:
            logger.warning(
                "⚠️  JWT_SECRET_KEY 使用了默认开发密钥（长度不足或未配置）。"
                "部署到生产前请在 .env 设置强密钥，否则 API Token 存在伪造风险！"
            )

    # 预热 RAG 模型（后台异步，避免第一个用户请求超时）
    async def _prewarm_rag():
        try:
            logger.info("⏳ 后台预热 RAG 模型...")
            from src.core.rag_engine import get_rag_engine

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, get_rag_engine)  # 阻塞模型加载放线程池
            logger.info("✅ RAG 模型预热完成，首次查询将立即响应")
        except Exception as e:
            logger.warning(f"⚠️ RAG 模型预热失败（不影响服务启动）: {e}")

    asyncio.create_task(_prewarm_rag())

    # P0-Root-Cause-Sweep: 启动死单巡检看门狗（后台任务，每 15 分钟自动回收超时订单）
    from src.services.task_coordinator import start_stale_order_watchdog

    asyncio.create_task(start_stale_order_watchdog())

    yield  # 应用运行中

    # === 关闭阶段 ===
    logger.info("👋 PDD AI 客服机器人正在关闭...")

    # P0-Root-Cause-Sweep: 优雅关闭持久化 HTTP 连接池
    import contextlib

    from src.services.pdd_api_client import pdd_api_client
    from src.services.wecom_client import wecom_client

    with contextlib.suppress(Exception):
        await pdd_api_client.close()
        logger.info("✅ PDD API 客户端连接池已关闭")
    with contextlib.suppress(Exception):
        await wecom_client.close()
        logger.info("✅ 企业微信客户端连接池已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="PDD E-Commerce AI Bot",
    description="基于 RAG + LLM + SQLite 持久化的拼多多智能客服系统",
    version="0.2.0",
    lifespan=lifespan,
)

# 允许跨域（从 .env CORS_ORIGINS 读取，生产环境请替换为实际域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True,
)

# 挂载静态文件 (必须在路由注册之前)
if not os.path.exists("static"):
    os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 挂载 PPT 生成文件目录，使生成的 .pptx 可以通过 /files/<filename> 直接下载
os.makedirs("data/output", exist_ok=True)
app.mount("/files", StaticFiles(directory="data/output"), name="generated_files")

# ===== Prometheus 监控埋点 =====
Instrumentator().instrument(app).expose(app)

# ===== P0-Fix-3: 基于 TTLCache 的内存限流器 =====
# 每个 IP 的访问计数在 60s 后自动淘汰，无需手动清理
_rate_limit_store: TTLCache = TTLCache(maxsize=10000, ttl=60)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """注入 Request-ID 到日志上下文"""
    request_id = str(uuid.uuid4())[:8]
    with logger.contextualize(request_id=f"REQ-{request_id}"):
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # 仅针对 API 接口限流
    if request.url.path.startswith("/api/v1/chat"):
        client_ip = request.client.host if request.client else "unknown"

        # P0-Fix-3: 基于 TTLCache 的滑动窗口限流，每分钟 60 次
        current_count = _rate_limit_store.get(client_ip, 0)
        if current_count >= 60:
            logger.warning(f"触发限流 | IP: {client_ip} | 请求已被拦截")
            return JSONResponse(
                status_code=429, content={"status": "error", "message": "请求过于频繁，请稍后再试 (Too Many Requests)"}
            )
        _rate_limit_store[client_ip] = current_count + 1

    response = await call_next(request)
    return response


# Register routes — public_router first so GET / serves Vue shell without auth
app.include_router(public_router, prefix="", tags=["前端"])  # GET / — Vue shell (public)
app.include_router(dashboard_router, prefix="", tags=["可视化大屏"])  # /api/dashboard/* (auth)
app.include_router(ws_router, prefix="", tags=["WebSocket"])
app.include_router(webhook_router, prefix="/api/v1", tags=["客服接口"])
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
app.include_router(admin_router, prefix="/admin", tags=["管理后台"])


@app.get("/api_root", tags=["系统"])
async def api_root():
    return {
        "app": "PDD E-Commerce AI Bot",
        "version": "0.2.0",
        "status": "running",
        "docs": "/docs",
        "dashboard": "/",
        "admin": "/admin",
        "admin_vue": "/admin2",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常拦截：防止未处理异常导致进程崩溃或服务假死。
    P0-Fix-1: 显式放行框架级异常（HTTPException / RequestValidationError），
    避免将 401/404/422 等误转为 500。
    """
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    # 框架级异常应由 FastAPI/Starlette 默认处理器返回正确状态码
    if isinstance(exc, HTTPException | StarletteHTTPException | RequestValidationError):
        raise exc

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
