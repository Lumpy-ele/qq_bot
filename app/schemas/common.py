"""通用响应包装模型"""
from typing import Any, Optional

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一响应格式。

    code=0 表示成功，非 0 表示失败；msg 为可读信息；data 为业务数据。
    """

    code: int = 0
    msg: str = "ok"
    data: Optional[Any] = None
