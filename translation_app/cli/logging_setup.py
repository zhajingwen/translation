"""
统一日志初始化
"""

import logging

from config import LogConfig


def setup_logging():
    logging.basicConfig(
        level=getattr(logging, LogConfig.LOG_LEVEL, logging.INFO),
        format=LogConfig.LOG_FORMAT,
        datefmt=LogConfig.LOG_DATE_FORMAT
    )

    openai_logger = logging.getLogger('openai._base_client')
    openai_logger.setLevel(logging.INFO)

    httpx_logger = logging.getLogger('httpx')
    httpx_logger.setLevel(logging.WARNING)

