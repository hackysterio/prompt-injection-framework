import logging
import os
from datetime import datetime
from typing import Optional

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


def get_logger(name: str = "promptguard", log_file: Optional[str] = None, level: str = "INFO") -> logging.Logger:
    from typing import Optional

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    if HAS_COLORLOG:
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s [%(levelname)s]%(reset)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
