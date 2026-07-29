"""FastAPI 入口、路由注册、生命周期管理"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1 import health, send_group, send_private
from app.core.exceptions import (
    OneBotError,
    OneBotTimeoutError,
    OneBotUnavailableError,
)
from app.utils.logger import get_logger, setup_logging
from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：初始化日志
    setup_logging()
    logger = get_logger("app.main")
    logger.info("应用启动: %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("日志级别: %s | 日志目录: %s", settings.LOG_LEVEL, settings.log_dir_path)
    yield
    # 关闭
    logger = get_logger("app.main")
    logger.info("应用关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于小号 QQ 的公网消息发送 API",
    lifespan=lifespan,
)

# 注册路由
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(send_private.router, prefix="/api/v1", tags=["send"])
app.include_router(send_group.router, prefix="/api/v1", tags=["send"])


# ---- 全局异常处理：将 OneBot 相关异常统一包装为 ApiResponse ----
@app.exception_handler(OneBotUnavailableError)
async def _handle_unavailable(_: Request, exc: OneBotUnavailableError):
    """协议端不可达：返回 503 + ApiResponse。"""
    return JSONResponse(
        status_code=503,
        content={"code": exc.code, "msg": exc.msg, "data": exc.data},
    )


@app.exception_handler(OneBotTimeoutError)
async def _handle_timeout(_: Request, exc: OneBotTimeoutError):
    """协议端超时：返回 504 + ApiResponse。"""
    return JSONResponse(
        status_code=504,
        content={"code": exc.code, "msg": exc.msg, "data": exc.data},
    )


@app.exception_handler(OneBotError)
async def _handle_onebot_error(_: Request, exc: OneBotError):
    """协议端业务失败（retcode != 0）：HTTP 200 + 非 0 code（符合接口契约）。"""
    return JSONResponse(
        status_code=200,
        content={"code": exc.code, "msg": exc.msg or "协议端调用失败", "data": exc.data},
    )
