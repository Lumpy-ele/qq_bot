"""消息段（MessageSegment）Pydantic 模型。

OneBot 11 消息段统一结构：{"type": <str>, "data": {<字段>: <值>}}
本模块定义常用类型（text / image / at / face），其余类型用通用 MessageSegment 兜底。
"""
from __future__ import annotations

from typing import Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class _SegmentBase(BaseModel):
    """消息段基类，序列化为 {"type": ..., "data": {...}}。"""

    model_config = ConfigDict(extra="forbid")

    type: str

    def to_onebot(self) -> dict:
        """转换为 OneBot 11 原生 dict（type + data）。"""
        data = self.model_dump(exclude={"type"}, exclude_none=True)
        return {"type": self.type, "data": data}


class TextSegment(_SegmentBase):
    type: Literal["text"] = "text"
    text: str


class ImageSegment(_SegmentBase):
    type: Literal["image"] = "image"
    url: str
    cache: int | None = None
    proxy: int | None = None
    timeout: int | None = None


class AtSegment(_SegmentBase):
    type: Literal["at"] = "at"
    qq: str | int


class FaceSegment(_SegmentBase):
    type: Literal["face"] = "face"
    id: int


class ReplySegment(_SegmentBase):
    type: Literal["reply"] = "reply"
    id: int


class MessageSegment(_SegmentBase):
    """通用消息段，用于未显式建模的类型。data 字段为任意键值。"""

    model_config = ConfigDict(extra="allow")

    type: str
    data: dict[str, Any] = Field(default_factory=dict)

    def to_onebot(self) -> dict:
        return {"type": self.type, "data": dict(self.data)}


# 便于类型标注的联合类型
Segment = Union[
    TextSegment,
    ImageSegment,
    AtSegment,
    FaceSegment,
    ReplySegment,
    MessageSegment,
]


class Message(BaseModel):
    """消息体：一个有序的消息段集合。

    序列化为 OneBot 11 期望的 message 数组（list[dict]）。
    """

    segments: list[Segment] = Field(default_factory=list)

    def to_onebot(self) -> list[dict]:
        return [s.to_onebot() for s in self.segments]

    @classmethod
    def from_texts(cls, *texts: str) -> "Message":
        """快捷构造：传入多段文本。"""
        return cls(segments=[TextSegment(text=t) for t in texts])

    def __len__(self) -> int:
        return len(self.segments)


# ============================================================
# HTTP 请求体模型（阶段 3）
# ============================================================
from typing import Any, List, Union  # noqa: E402

from pydantic import Field  # noqa: E402


# 调用方可传入的"消息"形态：
#   1) OneBot 11 消息段数组：[{"type": "text", "data": {"text": "..."}}]
#   2) 纯字符串："你好"
# 序列化/校验时保留原样，由 OneBotClient._normalize_message 统一处理
MessageInput = Union[List[dict[str, Any]], str]


class SendPrivateRequest(BaseModel):
    """POST /api/v1/send/private 请求体。"""

    user_id: int = Field(..., description="目标 QQ 号", examples=[123456789])
    message: MessageInput = Field(
        ...,
        description="消息内容：OneBot 11 消息段数组或纯字符串",
        examples=[
            [
                {"type": "text", "data": {"text": "你好"}},
                {"type": "image", "data": {"url": "https://example.com/a.png"}},
            ]
        ],
    )
    auto_escape: bool = Field(False, description="是否对纯文本进行 CQ 码转义")


class SendGroupRequest(BaseModel):
    """POST /api/v1/send/group 请求体。"""

    group_id: int = Field(..., description="目标群号", examples=[987654321])
    message: MessageInput = Field(
        ...,
        description="消息内容：OneBot 11 消息段数组或纯字符串",
        examples=[{"type": "text", "data": {"text": "群消息"}}],
    )
    auto_escape: bool = Field(False, description="是否对纯文本进行 CQ 码转义")


class SendResultData(BaseModel):
    """发送消息成功时的 data 字段。"""

    message_id: int = Field(..., description="OneBot 协议端返回的消息 ID")

