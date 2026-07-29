"""OneBotClient 单元测试。

使用 httpx.MockTransport 模拟协议端响应，覆盖：
- send_private_msg 成功
- send_group_msg 成功
- retcode != 0 抛 OneBotError
- 不可达抛 OneBotUnavailableError
"""
import httpx
import pytest

from app.core.exceptions import OneBotError, OneBotUnavailableError
from app.schemas.message import Message
from app.services.message_builder import MessageBuilder
from app.services.onebot_client import OneBotClient


def _make_client(handler, base_url="http://mock:3000"):
    """构造一个使用 MockTransport 的 OneBotClient。

    通过 monkeypatch 替换其内部 httpx.AsyncClient 行为：实际上我们直接
    注入一个自定义 _call，更简单稳定。这里改用重写 _call 的方式不优雅，
    因此改为：让 OneBotClient 在调用 httpx.AsyncClient 时使用 mock transport。
    实现方式——临时把 httpx.AsyncClient 替换为带 transport 的版本。
    """
    transport = httpx.MockTransport(handler)
    client = OneBotClient(base_url=base_url, token="")

    original_asyncclient = httpx.AsyncClient

    class _PatchedAsyncClient(original_asyncclient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    return client, _PatchedAsyncClient


@pytest.mark.asyncio
async def test_send_private_msg_success(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/send_private_msg"
        body = request.read()
        assert b"user_id" in body
        return httpx.Response(
            200,
            json={"status": "ok", "retcode": 0, "data": {"message_id": 42}},
        )

    client, patched = _make_client(handler)
    monkeypatch.setattr("app.services.onebot_client.httpx.AsyncClient", patched)

    msg = MessageBuilder().text("hello").build()
    mid = await client.send_private_msg(user_id=123, message=msg)
    assert mid == 42


@pytest.mark.asyncio
async def test_send_group_msg_success(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/send_group_msg"
        return httpx.Response(
            200,
            json={"status": "ok", "retcode": 0, "data": {"message_id": 7}},
        )

    client, patched = _make_client(handler)
    monkeypatch.setattr("app.services.onebot_client.httpx.AsyncClient", patched)

    mid = await client.send_group_msg(group_id=999, message=[{"type": "text", "data": {"text": "hi"}}])
    assert mid == 7


@pytest.mark.asyncio
async def test_send_msg_accepts_plain_string(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ok", "retcode": 0, "data": {"message_id": 1}})

    client, patched = _make_client(handler)
    monkeypatch.setattr("app.services.onebot_client.httpx.AsyncClient", patched)

    mid = await client.send_private_msg(user_id=1, message="纯文本")
    assert mid == 1


@pytest.mark.asyncio
async def test_retcode_nonzero_raises_onebot_error(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"status": "failed", "retcode": 1000, "msg": "消息发送失败", "data": None},
        )

    client, patched = _make_client(handler)
    monkeypatch.setattr("app.services.onebot_client.httpx.AsyncClient", patched)

    with pytest.raises(OneBotError) as exc_info:
        await client.send_private_msg(user_id=1, message="x")
    assert exc_info.value.retcode == 1000
    assert "消息发送失败" in exc_info.value.msg


@pytest.mark.asyncio
async def test_connection_error_raises_unavailable(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    client, patched = _make_client(handler)
    monkeypatch.setattr("app.services.onebot_client.httpx.AsyncClient", patched)

    with pytest.raises(OneBotUnavailableError):
        await client.send_private_msg(user_id=1, message="x")


@pytest.mark.asyncio
async def test_message_object_serialized_correctly(monkeypatch):
    """验证传入 Message 对象时，序列化结果符合 OneBot 11。"""
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json as _json
        captured["body"] = _json.loads(request.read())
        return httpx.Response(200, json={"status": "ok", "retcode": 0, "data": {"message_id": 1}})

    client, patched = _make_client(handler)
    monkeypatch.setattr("app.services.onebot_client.httpx.AsyncClient", patched)

    msg = MessageBuilder().text("你好").at(123).image("http://x/a.png").build()
    await client.send_group_msg(group_id=1, message=msg)
    assert captured["body"]["message"] == [
        {"type": "text", "data": {"text": "你好"}},
        {"type": "at", "data": {"qq": 123}},
        {"type": "image", "data": {"url": "http://x/a.png"}},
    ]
