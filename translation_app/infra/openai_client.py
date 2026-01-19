"""
OpenAI 客户端创建
"""

from typing import Any

from openai import OpenAI

from translation_app.domain.translator import TranslateConfig


def build_openai_client(config: TranslateConfig) -> Any:
    """
    根据 TranslateConfig 创建 OpenAI 客户端
    """
    if not config.api_key:
        raise ValueError("api_key 参数不能为空")
    return OpenAI(
        api_key=config.api_key,
        base_url=config.api_base_url
    )

