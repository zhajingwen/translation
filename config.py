#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块（兼容入口）

此文件仅用于向后兼容，实际实现已移至 translation_app.core.config
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

__all__ = [
    'PathConfig',
    'CharLimits',
    'TranslationDefaults',
    'LogConfig',
    'FileFormats',
    'SENTENCE_END_PUNCTUATION',
    'SECONDARY_PUNCTUATION',
    'get_work_dir',
    'get_combined_dir',
]
