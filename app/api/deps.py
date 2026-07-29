"""鉴权依赖：校验 Authorization: Bearer <API_KEY>。"""
from fastapi import Depends, Header, HTTPException, status
from config.settings import settings


def get_api_key(authorization: str | None = Header(default=None)) -> str:
    """校验 Bearer Token，返回 API Key 本身（供后续审计使用）。

    - 缺少 Authorization 头 -> 401
    - 非 Bearer scheme      -> 401
    - token 不匹配          -> 401
    - settings.API_KEY 为空 -> 401（未配置即视为拒绝所有请求，避免裸奔）
    """
    expected = settings.API_KEY
    if not expected:
        # 未配置 API_KEY，直接拒绝，避免服务裸奔
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="服务端未配置 API_KEY，拒绝访问",
        )

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 Authorization 头",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization 格式应为: Bearer <API_KEY>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1].strip()
    if token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API_KEY 无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


# 便于路由复用的依赖别名
RequireApiKey = Depends(get_api_key)
