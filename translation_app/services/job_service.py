#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单文件翻译服务
"""

import logging
from pathlib import Path

from translation_app.domain.translator import Translator
from translation_app.core.translate_config import create_translate_config
from translation_app.infra.openai_client import build_openai_client
from translation_app.core.providers import get_provider
from translation_app.core.config import TranslationDefaults


logger = logging.getLogger('JobService')


def run_single_file(source_file: str, provider: str = 'akashml') -> bool:
    """
    单文件翻译入口
    """
    provider_config = get_provider(provider)

    # 验证文件是否存在
    file_path = Path(source_file)
    if not file_path.exists():
        logger.error(f"文件不存在: {source_file}")
        return False

    # 验证文件格式
    supported_extensions = ['.txt', '.pdf', '.epub']
    if file_path.suffix.lower() not in supported_extensions:
        logger.error(f"不支持的文件格式: {file_path.suffix}")
        logger.error(f"支持的格式: {', '.join(supported_extensions)}")
        return False

    logger.info(f"准备翻译文件: {source_file}")
    logger.info(f"使用服务商: {provider_config.name}")

    config = create_translate_config(
        max_workers=TranslationDefaults.JOB_MAX_WORKERS,
        max_retries=TranslationDefaults.JOB_MAX_RETRIES,
        retry_delay=TranslationDefaults.JOB_RETRY_DELAY,
        chunk_size=TranslationDefaults.JOB_CHUNK_SIZE,
        min_chunk_size=TranslationDefaults.JOB_MIN_CHUNK_SIZE,
        api_timeout=TranslationDefaults.JOB_API_TIMEOUT,
        api_base_url=provider_config.api_base_url,
        model=provider_config.model,
        api_key=provider_config.api_key,
        client_factory=build_openai_client
    )

    translator = Translator(source_file, config)
    return translator.run()

