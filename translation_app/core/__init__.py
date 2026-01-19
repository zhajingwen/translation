#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心配置和工具模块
"""

from translation_app.core.config import (
    PathConfig,
    CharLimits,
    TranslationDefaults,
    LogConfig,
    FileFormats,
    SENTENCE_END_PUNCTUATION,
    SECONDARY_PUNCTUATION,
    get_work_dir,
    get_combined_dir,
)
from translation_app.core.providers import (
    ProviderConfig,
    Providers,
    get_provider,
)
from translation_app.core.translate_config import (
    ChunkingConfig,
    RetryConfig,
    ApiConfig,
    TranslateConfig,
    create_translate_config,
)
from translation_app.core.file_ops import (
    safe_delete,
    safe_rename,
)
from translation_app.core.file_analyzer import (
    count_file_characters,
    is_file_chinese,
    count_chinese_characters,
)
from translation_app.core.path_utils import (
    normalize_file_path,
    get_translated_filename,
    get_translated_path,
)

__all__ = [
    # config
    'PathConfig',
    'CharLimits',
    'TranslationDefaults',
    'LogConfig',
    'FileFormats',
    'SENTENCE_END_PUNCTUATION',
    'SECONDARY_PUNCTUATION',
    'get_work_dir',
    'get_combined_dir',
    # providers
    'ProviderConfig',
    'Providers',
    'get_provider',
    # translate_config
    'ChunkingConfig',
    'RetryConfig',
    'ApiConfig',
    'TranslateConfig',
    'create_translate_config',
    # file_ops
    'safe_delete',
    'safe_rename',
    'count_file_characters',
    'is_file_chinese',
    'count_chinese_characters',
    'normalize_file_path',
    'get_translated_filename',
    'get_translated_path',
]
