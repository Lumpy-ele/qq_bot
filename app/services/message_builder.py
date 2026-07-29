"""消息段构造器（MessageBuilder）。

提供链式 / 函数式两种用法，最终产出 OneBot 11 消息段列表。
"""
from __future__ import annotations

from typing import Any

from app.schemas.message import (
    AtSegment,
    FaceSegment,
    ImageSegment,
    Message,
    MessageSegment,
    ReplySegment,
    TextSegment,
)


class MessageBuilder:
    """链式构造消息。

    示例：
        msg = (
            MessageBuilder()
            .text("你好")
            .at(123456)
            .image("https://example.com/a.png")
            .build()
        )
        # msg: Message 对象，msg.to_onebot() -> list[dict]
    """

    def __init__(self) -> None:
        self._segments: list[Any] = []

    # ---- 链式构造方法 ----
    def text(self, text: str) -> "MessageBuilder":
        self._segments.append(TextSegment(text=text))
        return self

    def image(
        self,
        url: str,
        *,
        cache: int | None = None,
        proxy: int | None = None,
        timeout: int | None = None,
    ) -> "MessageBuilder":
        self._segments.append(
            ImageSegment(url=url, cache=cache, proxy=proxy, timeout=timeout)
        )
        return self

    def at(self, qq: str | int) -> "MessageBuilder":
        self._segments.append(AtSegment(qq=qq))
        return self

    def face(self, id: int) -> "MessageBuilder":
        self._segments.append(FaceSegment(id=id))
        return self

    def reply(self, id: int) -> "MessageBuilder":
        self._segments.append(ReplySegment(id=id))
        return self

    def raw(self, type_: str, data: dict[str, Any]) -> "MessageBuilder":
        """追加任意类型的消息段（兜底）。"""
        self._segments.append(MessageSegment(type=type_, data=dict(data)))
        return self

    # ---- 产出 ----
    def build(self) -> Message:
        return Message(segments=list(self._segments))

    def to_onebot(self) -> list[dict]:
        return self.build().to_onebot()


# ---- 函数式便捷构造（不使用链式时） ----
def text(text: str) -> TextSegment:
    """构造文本消息段。"""
    return TextSegment(text=text)


def image(url: str, **kwargs: Any) -> ImageSegment:
    """构造图片消息段。"""
    return ImageSegment(url=url, **kwargs)


def at(qq: str | int) -> AtSegment:
    """构造 @ 消息段。"""
    return AtSegment(qq=qq)


def face(id: int) -> FaceSegment:
    """构造 QQ 表情消息段。"""
    return FaceSegment(id=id)


def build_message(*segments: Any) -> Message:
    """由多个消息段组装 Message。"""
    return Message(segments=list(segments))


def build_text_message(*texts: str) -> Message:
    """由多段文本组装 Message。"""
    return Message.from_texts(*texts)
