"""自定义异常"""
from typing import Any, Optional


class AppError(Exception):
    """应用异常基类。"""

    def __init__(self, msg: str, code: int = -1, data: Optional[Any] = None):
        super().__init__(msg)
        self.msg = msg
        self.code = code
        self.data = data


class OneBotError(AppError):
    """OneBot 协议端返回失败（retcode != 0）或调用异常时抛出。"""

    def __init__(self, msg: str, retcode: int = -1, data: Optional[Any] = None):
        super().__init__(msg=msg, code=retcode, data=data)
        self.retcode = retcode


class OneBotTimeoutError(OneBotError):
    """调用 OneBot 协议端超时。"""

    def __init__(self, msg: str = "调用 OneBot 协议端超时"):
        super().__init__(msg=msg, retcode=-2)


class OneBotUnavailableError(OneBotError):
    """OneBot 协议端不可达（连接失败）。"""

    def __init__(self, msg: str = "OneBot 协议端不可达"):
        super().__init__(msg=msg, retcode=-3)
