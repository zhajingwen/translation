#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块

统一管理项目的所有配置项：
- 文件路径配置
- 字符数阈值配置
- 日志配置
- 翻译配置默认值
"""

import os
from pathlib import Path
from typing import Optional


# ================== 路径配置 ==================

class PathConfig:
    """文件路径配置"""
    
    # 工作目录
    WORK_DIR = Path("files")
    
    # 合并文件输出目录
    COMBINED_DIR = WORK_DIR / "combined"
    
    # 备份目录
    BACKUP_DIR = WORK_DIR / ".backup"
    
    @classmethod
    def ensure_dirs(cls):
        """确保必要的目录存在"""
        cls.WORK_DIR.mkdir(parents=True, exist_ok=True)
        cls.COMBINED_DIR.mkdir(parents=True, exist_ok=True)


# ================== 字符数阈值配置 ==================

class CharLimits:
    """字符数相关阈值配置"""
    
    # 最小文件字符数（小于此值的文件会被删除）
    MIN_FILE_CHARS = 1000
    
    # 小文件上限（用于合并，中文字数 < 10万字的文件会被合并）
    SMALL_FILE_LIMIT = 100000
    
    # 合并文件上限（单个合并文件的中文字数不超过 20万字）
    MERGE_FILE_LIMIT = 200000
    
    # 中文文件判断阈值（中文字符占比 >= 30% 视为中文文件）
    CHINESE_RATIO_THRESHOLD = 0.3


# ================== 翻译配置默认值 ==================

class TranslationDefaults:
    """翻译配置的默认值"""
    
    # 批量翻译默认配置
    BATCH_MAX_WORKERS = 8
    BATCH_MAX_RETRIES = 6
    BATCH_RETRY_DELAY = 120
    BATCH_CHUNK_SIZE = 3000
    BATCH_MIN_CHUNK_SIZE = 1000
    BATCH_API_TIMEOUT = 60
    
    # 单文件翻译默认配置
    JOB_MAX_WORKERS = 1
    JOB_MAX_RETRIES = 6
    JOB_RETRY_DELAY = 120
    JOB_CHUNK_SIZE = 50000
    JOB_MIN_CHUNK_SIZE = 30000
    JOB_API_TIMEOUT = 60


# ================== 日志配置 ==================

class LogConfig:
    """日志相关配置"""
    
    # 日志级别
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # 是否在日志中显示翻译内容预览（隐私保护）
    LOG_SHOW_CONTENT = os.environ.get('LOG_SHOW_CONTENT', 'true').lower() == 'true'
    
    # 日志格式
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


# ================== 文件格式配置 ==================

class FileFormats:
    """支持的文件格式"""
    
    # 支持的文件扩展名
    SUPPORTED_EXTENSIONS = ['.txt', '.pdf', '.epub']
    
    # 翻译后文件名后缀
    TRANSLATED_SUFFIX = " translated.txt"
    
    # EPUB 支持的 MIME 类型
    EPUB_MIME_TYPES = [
        'application/xhtml+xml',
        'application/xhtml', 
        'text/html',
        'text/xhtml',
        'application/html+xml',
        'text/xml',
    ]


# ================== 句子结束标点符号 ==================

# 句子结束标点符号（中英文）
SENTENCE_END_PUNCTUATION = ('。', '！', '？', '…', '.', '!', '?')

# 次要断句标点符号
SECONDARY_PUNCTUATION = (',', '，', ';', '；', ':', '：', ' ')


# ================== 便捷访问函数 ==================

def get_work_dir() -> Path:
    """获取工作目录"""
    PathConfig.ensure_dirs()
    return PathConfig.WORK_DIR


def get_combined_dir() -> Path:
    """获取合并文件输出目录"""
    PathConfig.ensure_dirs()
    return PathConfig.COMBINED_DIR
