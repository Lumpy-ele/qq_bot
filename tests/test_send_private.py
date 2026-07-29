"""POST /api/v1/send/private 接口测试。

覆盖：
- 成功转发到协议端
- 缺少 / 错误 Authorization 返回 401
- 参数校验失败返回 422
- 协议端 retcode != 0 返回非 0 code（HTTP 200 包装）
- 协议端不可达返回 503
"""
import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import OneBotError, OneBotUnavailableError
from app.main import app
from config.settings import settings


@pytest.fixture
def client(monkeypatch):
    """构造 TestClient，并设置一个测试用 API_KEY。"""
    original_key = settings.API_KEY
    settings.API_KEY = "test-secret"
    with TestClient(app) as c:
        yield c
    settings.API_KEY = original_key


def _patch_send_private(monkeypatch, *, return_mid=42, raise_exc=None):
    """替换 send_private 模块内的 OneBotClient.send_private_msg。"""
    from app.api.v1 import send_private as mod

    async def fake_send_private_msg(self, user_id, message, auto_escape=False):
        if raise_exc is not None:
            raise raise_exc
        # 记录调用参数，便于断言
        fake_send_private_msg.last_args = {
            "user_id": user_id,
            "message": message,
            "auto_escape": auto_escape,
        }
        return return_mid

    fake_send_private_msg.last_args = None
    monkeypatch.setattr(mod._client, "send_private_msg", fake_send_private_msg.__get__(mod._client))
    return fake_send_private_msg


def test_send_private_success(client, monkeypatch):
    _patch_send_private(monkeypatch, return_mid=999)
    r = client.post(
        "/api/v1/send/private",
        headers={"Authorization": "Bearer test-secret"},
        json={
            "user_id": 123,
            "message": [
                {"type": "text", "data": {"text": "你好"}},
                {"type": "image", "data": {"url": "https://example.com/a.png"}},
            ],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["msg"] == "ok"
    assert body["data"]["message_id"] == 999


def test_send_private_plain_string_message(client, monkeypatch):
    fake = _patch_send_private(monkeypatch, return_mid=1)
    r = client.post(
        "/api/v1/send/private",
        headers={"Authorization": "Bearer test-secret"},
        json={"user_id": 1, "message": "纯文本"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["message_id"] == 1
    # 验证传给协议端的就是纯字符串（由 OneBotClient 统一处理）
    assert fake.last_args["message"] == "纯文本"


def test_send_private_no_auth_returns_401(client):
    r = client.post(
        "/api/v1/send/private",
        json={"user_id": 1, "message": "x"},
    )
    assert r.status_code == 401


def test_send_private_wrong_auth_returns_401(client):
    r = client.post(
        "/api/v1/send/private",
        headers={"Authorization": "Bearer wrong"},
        json={"user_id": 1, "message": "x"},
    )
    assert r.status_code == 401


def test_send_private_missing_user_id_returns_422(client):
    r = client.post(
        "/api/v1/send/private",
        headers={"Authorization": "Bearer test-secret"},
        json={"message": "x"},  # 缺 user_id
    )
    assert r.status_code == 422
    body = r.json()
    # FastAPI 默认错误结构含 detail 数组
    assert "detail" in body
    assert any("user_id" in str(d) for d in body["detail"])


def test_send_private_missing_message_returns_422(client):
    r = client.post(
        "/api/v1/send/private",
        headers={"Authorization": "Bearer test-secret"},
        json={"user_id": 1},  # 缺 message
    )
    assert r.status_code == 422


def test_send_private_invalid_user_id_type_returns_422(client):
    r = client.post(
        "/api/v1/send/private",
        headers={"Authorization": "Bearer test-secret"},
        json={"user_id": "not-a-number", "message": "x"},
    )
    assert r.status_code == 422


def test_send_private_onebot_failure_returns_nonzero_code(client, monkeypatch):
    """协议端 retcode != 0：HTTP 200 + 非 0 code（符合接口契约）。"""
    _patch_send_private(
        monkeypatch,
        raise_exc=OneBotError(msg="消息发送失败", retcode=1000, data=None),
    )
    r = client.post(
        "/api/v1/send/private",
        headers={"Authorization": "Bearer test-secret"},
        json={"user_id": 1, "message": "x"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 1000
    assert "消息发送失败" in body["msg"]


def test_send_private_onebot_unavailable_returns_503(client, monkeypatch):
    _patch_send_private(
        monkeypatch,
        raise_exc=OneBotUnavailableError("OneBot 协议端不可达"),
    )
    r = client.post(
        "/api/v1/send/private",
        headers={"Authorization": "Bearer test-secret"},
        json={"user_id": 1, "message": "x"},
    )
    assert r.status_code == 503
    body = r.json()
    assert body["code"] == -3
    assert "不可达" in body["msg"]
