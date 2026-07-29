"""全局配置加载（环境变量优先于 .env 文件）"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录：config/settings.py 的上两级
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """应用配置，字段与 .env 中的变量名一一对应。"""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用
    APP_NAME: str = "QQ Bot API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # 日志
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    # 鉴权（阶段 3 启用）
    API_KEY: str = ""

    # OneBot 协议端（阶段 2 启用）
    ONEBOT_HTTP_URL: str = "http://127.0.0.1:3000"
    ONEBOT_TOKEN: str = ""

    @property
    def log_dir_path(self) -> Path:
        """返回绝对路径的日志目录，支持相对路径。"""
        p = Path(self.LOG_DIR)
        if not p.is_absolute():
            p = BASE_DIR / p
        return p


# 全局单例
settings = Settings()
