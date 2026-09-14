"""
统一日志初始化
"""

import logging

from translation_app.core.config import LogConfig


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

    # PyPDF2 对部分不规范 PDF（如字体 /W 宽度数组格式异常）会打印大量 WARNING，
    # 该异常已在库内部捕获处理（不影响文本提取），因此屏蔽掉避免刷屏干扰日志
    pypdf2_logger = logging.getLogger('PyPDF2')
    pypdf2_logger.setLevel(logging.ERROR)

