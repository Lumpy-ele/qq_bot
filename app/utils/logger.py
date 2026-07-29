"""日志封装：输出到控制台与文件，按天切割，保留 7 天。

使用方式：
    from app.utils.logger import setup_logging, get_logger
    setup_logging()              # 应用启动时调用一次
    logger = get_logger("app.main")
    logger.info("...")
"""
import logging
import logging.config
import sys

from config.settings import settings


def _build_dict_config() -> dict:
    """根据 settings 构造 logging dictConfig。"""
    level = settings.LOG_LEVEL.upper()

    # 确保日志目录存在
    log_dir = settings.log_dir_path
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": fmt,
                "datefmt": datefmt,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "default",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": level,
                "formatter": "default",
                "filename": str(log_file),
                "when": "midnight",
                "backupCount": 7,
                "encoding": "utf-8",
                "utc": False,
            },
        },
        "loggers": {
            "app": {
                "level": level,
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
        "root": {
            "level": level,
            "handlers": ["console", "file"],
        },
    }


def setup_logging() -> None:
    """初始化全局日志配置，应用启动时调用一次。"""
    logging.config.dictConfig(_build_dict_config())


def get_logger(name: str = "app") -> logging.Logger:
    """获取 logger，name 一般传模块名（如 app.main）。"""
    return logging.getLogger(name)
