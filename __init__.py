#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Translation Package

文档翻译工具包，支持 PDF、EPUB、TXT 格式的批量翻译。
"""

# 导出主要的类和函数
from translator import Translator, Translate, TranslateConfig
from providers import get_provider, ProviderConfig, Providers
from config import (
    PathConfig,
    CharLimits,
    TranslationDefaults,
    LogConfig,
    FileFormats,
)
from utils import (
    safe_delete,
    safe_rename,
    count_file_characters,
    is_file_chinese,
    count_chinese_characters,
    normalize_file_path,
    get_translated_filename,
    get_translated_path,
)
from extractors import get_extractor
from text_processor import TextProcessor

__version__ = '2.0.0'
__author__ = 'Translation Team'

__all__ = [
    # 核心翻译
    'Translator',
    'Translate',
    'TranslateConfig',
    
    # 服务商配置
    'get_provider',
    'ProviderConfig',
    'Providers',
    
    # 配置类
    'PathConfig',
    'CharLimits',
    'TranslationDefaults',
    'LogConfig',
    'FileFormats',
    
    # 工具函数
    'safe_delete',
    'safe_rename',
    'count_file_characters',
    'is_file_chinese',
    'count_chinese_characters',
    'normalize_file_path',
    'get_translated_filename',
    'get_translated_path',
    
    # 提取器
    'get_extractor',
    
    # 文本处理
    'TextProcessor',
]
