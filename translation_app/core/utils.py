#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块（向后兼容层）

此模块已重构，功能拆分到以下模块：
- file_ops.py: 文件操作
- file_analyzer.py: 文件分析
- path_utils.py: 路径处理

为保持向后兼容性，此模块重新导出所有函数
"""

# 文件操作
from translation_app.core.file_ops import (
    safe_delete,
    safe_rename,
)

# 文件分析
from translation_app.core.file_analyzer import (
    count_file_characters,
    is_file_chinese,
    count_chinese_characters,
)

# 路径处理
from translation_app.core.path_utils import (
    normalize_file_path,
    get_translated_filename,
    get_translated_path,
)


__all__ = [
    # file_ops
    'safe_delete',
    'safe_rename',
    # file_analyzer
    'count_file_characters',
    'is_file_chinese',
    'count_chinese_characters',
    # path_utils
    'normalize_file_path',
    'get_translated_filename',
    'get_translated_path',
]
