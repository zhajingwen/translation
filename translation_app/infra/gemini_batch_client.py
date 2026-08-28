#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini Batch API 客户端创建

使用官方 google-genai SDK（区别于 OpenAI 兼容接口），
用于提交/查询/拉取 Gemini 官方异步批处理任务。
"""

from typing import Any

from google import genai


def build_gemini_batch_client(api_key: str) -> Any:
    """
    根据 API Key 创建 google-genai 客户端

    Args:
        api_key: Gemini API Key

    Returns:
        genai.Client 实例
    """
    if not api_key:
        raise ValueError("api_key 参数不能为空")
    return genai.Client(api_key=api_key)
