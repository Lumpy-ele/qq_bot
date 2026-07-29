"""消息段构造器单元测试。"""
import pytest

from app.services.message_builder import (
    MessageBuilder,
    at,
    build_message,
    build_text_message,
    face,
    image,
    text,
)
from app.schemas.message import Message


# ---- 基础消息段 ----
def test_text_segment():
    seg = text("你好")
    ob = seg.to_onebot()
    assert ob == {"type": "text", "data": {"text": "你好"}}


def test_image_segment():
    seg = image("https://example.com/a.png")
    assert seg.to_onebot() == {
        "type": "image",
        "data": {"url": "https://example.com/a.png"},
    }


def test_image_segment_with_options():
    seg = image("https://example.com/a.png", cache=0, proxy=1, timeout=30)
    ob = seg.to_onebot()
    assert ob["type"] == "image"
    assert ob["data"]["cache"] == 0
    assert ob["data"]["proxy"] == 1
    assert ob["data"]["timeout"] == 30


def test_at_segment_accepts_int():
    seg = at(123456)
    assert seg.to_onebot() == {"type": "at", "data": {"qq": 123456}}


def test_at_segment_accepts_str():
    seg = at("123456")
    assert seg.to_onebot() == {"type": "at", "data": {"qq": "123456"}}


def test_face_segment():
    seg = face(14)
    assert seg.to_onebot() == {"type": "face", "data": {"id": 14}}


# ---- Builder 链式 ----
def test_builder_chain_text_at_image():
    msg = (
        MessageBuilder()
        .text("你好")
        .at(123456)
        .image("https://example.com/a.png")
        .build()
    )
    assert isinstance(msg, Message)
    assert msg.to_onebot() == [
        {"type": "text", "data": {"text": "你好"}},
        {"type": "at", "data": {"qq": 123456}},
        {"type": "image", "data": {"url": "https://example.com/a.png"}},
    ]


def test_builder_to_onebot_directly():
    arr = (
        MessageBuilder()
        .text("a")
        .text("b")
        .to_onebot()
    )
    assert arr == [
        {"type": "text", "data": {"text": "a"}},
        {"type": "text", "data": {"text": "b"}},
    ]


def test_builder_raw_segment():
    msg = (
        MessageBuilder()
        .text("前")
        .raw("poke", {"type": "poke", "id": "1"})
        .build()
    )
    arr = msg.to_onebot()
    assert arr[0] == {"type": "text", "data": {"text": "前"}}
    assert arr[1] == {"type": "poke", "data": {"type": "poke", "id": "1"}}


# ---- 函数式构造 ----
def test_build_message_from_segments():
    msg = build_message(text("a"), at(1), image("u"))
    assert len(msg) == 3
    assert msg.to_onebot()[1] == {"type": "at", "data": {"qq": 1}}


def test_build_text_message():
    msg = build_text_message("你好", "世界")
    assert msg.to_onebot() == [
        {"type": "text", "data": {"text": "你好"}},
        {"type": "text", "data": {"text": "世界"}},
    ]


def test_message_from_texts_classmethod():
    msg = Message.from_texts("x", "y")
    assert len(msg) == 2


# ---- 边界 ----
def test_empty_builder():
    msg = MessageBuilder().build()
    assert isinstance(msg, Message)
    assert msg.to_onebot() == []


def test_text_segment_extra_forbidden():
    """TextSegment 不允许出现未知字段。"""
    from app.schemas.message import TextSegment
    with pytest.raises(Exception):
        TextSegment(text="a", unknown_field=1)  # type: ignore[arg-type]
