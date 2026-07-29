"""健康检查接口"""
from fastapi import APIRouter

from app.schemas.common import ApiResponse
from config.settings import settings

router = APIRouter()


@router.get("/health", response_model=ApiResponse, summary="健康检查")
async def health() -> ApiResponse:
    """返回服务存活状态与版本信息。"""
    return ApiResponse(
        code=0,
        msg="ok",
        data={
            "status": "ok",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        },
    )
