"""鉴权依赖测试：覆盖 401 各种情况与正常通过。"""
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_api_key


def _build_app(api_key: str):
    """构造一个最小 app，仅用于测试 get_api_key。"""
    from config.settings import settings

    # 临时覆盖 settings.API_KEY
    original = settings.API_KEY
    settings.API_KEY = api_key

    app = FastAPI()

    @app.get("/protected")
    def protected(_: str = Depends(get_api_key)):
        return {"ok": True}

    client = TestClient(app)
    return client, original


def _restore(api_key):
    from config.settings import settings

    settings.API_KEY = api_key


def test_no_authorization_header_returns_401():
    client, original = _build_app("secret")
    try:
        r = client.get("/protected")
        assert r.status_code == 401
        assert "缺少 Authorization" in r.json()["detail"]
    finally:
        _restore(original)


def test_wrong_scheme_returns_401():
    client, original = _build_app("secret")
    try:
        r = client.get("/protected", headers={"Authorization": "Basic secret"})
        assert r.status_code == 401
        assert "Bearer" in r.json()["detail"]
    finally:
        _restore(original)


def test_wrong_token_returns_401():
    client, original = _build_app("secret")
    try:
        r = client.get("/protected", headers={"Authorization": "Bearer wrong"})
        assert r.status_code == 401
        assert "无效" in r.json()["detail"]
    finally:
        _restore(original)


def test_empty_token_returns_401():
    client, original = _build_app("secret")
    try:
        r = client.get("/protected", headers={"Authorization": "Bearer "})
        assert r.status_code == 401
    finally:
        _restore(original)


def test_correct_token_passes():
    client, original = _build_app("secret")
    try:
        r = client.get("/protected", headers={"Authorization": "Bearer secret"})
        assert r.status_code == 200
        assert r.json() == {"ok": True}
    finally:
        _restore(original)


def test_server_unconfigured_api_key_returns_401():
    """settings.API_KEY 为空时应拒绝所有请求（避免裸奔）。"""
    client, original = _build_app("")
    try:
        r = client.get("/protected", headers={"Authorization": "Bearer anything"})
        assert r.status_code == 401
        assert "未配置" in r.json()["detail"]
    finally:
        _restore(original)
