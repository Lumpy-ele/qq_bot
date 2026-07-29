"""发送私聊消息接口：POST /api/v1/send/private"""
from fastapi import APIRouter, Depends

from app.api.deps import RequireApiKey
from app.schemas.common import ApiResponse
from app.schemas.message import SendPrivateRequest, SendResultData
from app.services.onebot_client import OneBotClient
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger("app.api.send_private")

# 复用单例客户端（默认从 settings 读取配置）
_client = OneBotClient()


@router.post(
    "/send/private",
    response_model=ApiResponse,
    summary="发送私聊消息",
    dependencies=[RequireApiKey],
)
async def send_private(req: SendPrivateRequest) -> ApiResponse:
    """向指定 QQ 好友发送定制消息。"""
    logger.info("发送私聊: user_id=%s message=%s", req.user_id, req.message)
    message_id = await _client.send_private_msg(
        user_id=req.user_id,
        message=req.message,
        auto_escape=req.auto_escape,
    )
    return ApiResponse(
        code=0,
        msg="ok",
        data=SendResultData(message_id=message_id).model_dump(),
    )
