"""发送群聊消息接口：POST /api/v1/send/group"""
from fastapi import APIRouter, Depends

from app.api.deps import RequireApiKey
from app.schemas.common import ApiResponse
from app.schemas.message import SendGroupRequest, SendResultData
from app.services.onebot_client import OneBotClient
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger("app.api.send_group")

_client = OneBotClient()


@router.post(
    "/send/group",
    response_model=ApiResponse,
    summary="发送群聊消息",
    dependencies=[RequireApiKey],
)
async def send_group(req: SendGroupRequest) -> ApiResponse:
    """向指定群聊发送定制消息。"""
    logger.info("发送群聊: group_id=%s message=%s", req.group_id, req.message)
    message_id = await _client.send_group_msg(
        group_id=req.group_id,
        message=req.message,
        auto_escape=req.auto_escape,
    )
    return ApiResponse(
        code=0,
        msg="ok",
        data=SendResultData(message_id=message_id).model_dump(),
    )
