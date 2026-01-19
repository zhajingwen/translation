#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块（兼容入口）

此文件仅用于向后兼容，实际实现已移至 translation_app.core.utils
"""

from translation_app.core.utils import (
    safe_delete,
    safe_rename,
    count_file_characters,
    is_file_chinese,
    count_chinese_characters,
    normalize_file_path,
    get_translated_filename,
    get_translated_path,
)

__all__ = [
    'safe_delete',
    'safe_rename',
    'count_file_characters',
    'is_file_chinese',
    'count_chinese_characters',
    'normalize_file_path',
    'get_translated_filename',
    'get_translated_path',
]
