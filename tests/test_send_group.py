"""POST /api/v1/send/group 接口测试。"""
import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import OneBotError, OneBotUnavailableError
from app.main import app
from config.settings import settings


@pytest.fixture
def client(monkeypatch):
    original_key = settings.API_KEY
    settings.API_KEY = "test-secret"
    with TestClient(app) as c:
        yield c
    settings.API_KEY = original_key


def _patch_send_group(monkeypatch, *, return_mid=7, raise_exc=None):
    from app.api.v1 import send_group as mod

    async def fake_send_group_msg(self, group_id, message, auto_escape=False):
        if raise_exc is not None:
            raise raise_exc
        fake_send_group_msg.last_args = {
            "group_id": group_id,
            "message": message,
            "auto_escape": auto_escape,
        }
        return return_mid

    fake_send_group_msg.last_args = None
    monkeypatch.setattr(mod._client, "send_group_msg", fake_send_group_msg.__get__(mod._client))
    return fake_send_group_msg


def test_send_group_success(client, monkeypatch):
    fake = _patch_send_group(monkeypatch, return_mid=555)
    r = client.post(
        "/api/v1/send/group",
        headers={"Authorization": "Bearer test-secret"},
        json={"group_id": 999, "message": [{"type": "text", "data": {"text": "群消息"}}]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["message_id"] == 555
    assert fake.last_args["group_id"] == 999


def test_send_group_no_auth_returns_401(client):
    r = client.post("/api/v1/send/group", json={"group_id": 1, "message": "x"})
    assert r.status_code == 401


def test_send_group_missing_group_id_returns_422(client):
    r = client.post(
        "/api/v1/send/group",
        headers={"Authorization": "Bearer test-secret"},
        json={"message": "x"},
    )
    assert r.status_code == 422


def test_send_group_onebot_failure_returns_nonzero_code(client, monkeypatch):
    _patch_send_group(
        monkeypatch,
        raise_exc=OneBotError(msg="群消息发送失败", retcode=2000),
    )
    r = client.post(
        "/api/v1/send/group",
        headers={"Authorization": "Bearer test-secret"},
        json={"group_id": 1, "message": "x"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 2000
    assert "群消息发送失败" in body["msg"]


def test_send_group_onebot_unavailable_returns_503(client, monkeypatch):
    _patch_send_group(monkeypatch, raise_exc=OneBotUnavailableError())
    r = client.post(
        "/api/v1/send/group",
        headers={"Authorization": "Bearer test-secret"},
        json={"group_id": 1, "message": "x"},
    )
    assert r.status_code == 503
