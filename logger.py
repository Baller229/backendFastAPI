# logger.py
import logging
import os
import sys


def setup_logging(level: str | None = None) -> None:
    if getattr(setup_logging, "_configured", False):
        return

    level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(module)s.%(funcName)s:%(lineno)d | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=datefmt,
        stream=sys.stdout,
        force=True,
    )

    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(level)

    setup_logging._configured = True


def get_logger(name: str = "app") -> logging.Logger:
    return logging.getLogger(name)
