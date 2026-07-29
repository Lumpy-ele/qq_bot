"""OneBot 11 HTTP 客户端封装。

对接协议端（NapCat / Lagrange）的 HTTP API，封装发送私聊 / 群聊消息等常用动作。
统一处理：
  - access_token 鉴权头
  - 超时控制
  - 协议端 retcode != 0 抛出 OneBotError
  - 连接失败 / 超时抛出 OneBotUnavailableError / OneBotTimeoutError
"""
from __future__ import annotations

from typing import Any

import httpx

from app.core.exceptions import (
    OneBotError,
    OneBotTimeoutError,
    OneBotUnavailableError,
)
from app.schemas.message import Message
from app.utils.logger import get_logger
from config.settings import settings

logger = get_logger("app.services.onebot")


class OneBotResponse(dict):
    """OneBot 响应（dict 子类，便于访问 status / retcode / data / msg）。"""

    @property
    def ok(self) -> bool:
        return self.get("status") == "ok" and self.get("retcode") == 0

    @property
    def retcode(self) -> int:
        return int(self.get("retcode", -1))

    @property
    def data(self) -> Any:
        return self.get("data")

    @property
    def msg(self) -> str:
        return self.get("msg") or self.get("wording") or ""


class OneBotClient:
    """OneBot 11 HTTP 客户端。

    用法：
        client = OneBotClient()  # 默认从 settings 读取 URL / token
        resp = await client.send_private_msg(user_id=123, message=msg)
    """

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        *,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = (base_url or settings.ONEBOT_HTTP_URL).rstrip("/")
        self.token = token if token is not None else settings.ONEBOT_TOKEN
        self.timeout = timeout
        self._headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.token:
            self._headers["Authorization"] = f"Bearer {self.token}"

    # ---- 内部 ----
    async def _call(self, action: str, payload: dict[str, Any]) -> OneBotResponse:
        url = f"{self.base_url}/{action}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers=self._headers)
        except httpx.ConnectError as e:
            logger.error("OneBot 不可达: %s | action=%s payload=%s", e, action, payload)
            raise OneBotUnavailableError(f"OneBot 协议端不可达: {e}") from e
        except httpx.TimeoutException as e:
            logger.error("OneBot 超时: %s | action=%s payload=%s", e, action, payload)
            raise OneBotTimeoutError() from e

        if resp.status_code >= 400:
            raise OneBotError(
                f"OneBot HTTP {resp.status_code}: {resp.text}",
                retcode=resp.status_code,
            )

        try:
            body = resp.json()
        except ValueError as e:
            raise OneBotError(f"OneBot 响应非 JSON: {resp.text!r}") from e

        ob = OneBotResponse(body)
        if not ob.ok:
            logger.warning(
                "OneBot 调用失败 action=%s retcode=%s msg=%s data=%s",
                action, ob.retcode, ob.msg, ob.data,
            )
            raise OneBotError(
                msg=ob.msg or f"OneBot 调用失败: {action}",
                retcode=ob.retcode,
                data=ob.data,
            )
        logger.debug("OneBot 调用成功 action=%s data=%s", action, ob.data)
        return ob

    @staticmethod
    def _normalize_message(message: Message | list[dict] | str) -> list[dict]:
        """统一 Message / list[dict] / 纯文本 三种输入为 OneBot message 数组。"""
        if isinstance(message, str):
            return [{"type": "text", "data": {"text": message}}]
        if isinstance(message, Message):
            return message.to_onebot()
        return list(message)

    # ---- 对外动作 ----
    async def send_private_msg(
        self,
        user_id: int,
        message: Message | list[dict] | str,
        *,
        auto_escape: bool = False,
    ) -> int:
        """发送私聊消息，返回 message_id。"""
        payload = {
            "user_id": user_id,
            "message": self._normalize_message(message),
            "auto_escape": auto_escape,
        }
        ob = await self._call("send_private_msg", payload)
        data = ob.data or {}
        return int(data.get("message_id", 0))

    async def send_group_msg(
        self,
        group_id: int,
        message: Message | list[dict] | str,
        *,
        auto_escape: bool = False,
    ) -> int:
        """发送群聊消息，返回 message_id。"""
        payload = {
            "group_id": group_id,
            "message": self._normalize_message(message),
            "auto_escape": auto_escape,
        }
        ob = await self._call("send_group_msg", payload)
        data = ob.data or {}
        return int(data.get("message_id", 0))

    async def get_login_info(self) -> dict:
        """获取协议端登录账号信息，常用于健康检查。"""
        ob = await self._call("get_login_info", {})
        return dict(ob.data or {})
