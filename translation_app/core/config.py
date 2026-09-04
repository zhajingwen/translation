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
    """
    文件路径配置
    
    支持通过环境变量覆盖：
    - TRANSLATION_WORK_DIR: 工作目录（默认: files）
    """
    
    # 工作目录（支持环境变量覆盖）
    WORK_DIR = Path(os.environ.get('TRANSLATION_WORK_DIR', 'files'))
    
    # 合并文件输出目录
    COMBINED_DIR = WORK_DIR / "combined"
    
    # 备份目录
    BACKUP_DIR = WORK_DIR / ".backup"
    
    @classmethod
    def refresh(cls):
        """
        重新加载路径配置（从环境变量）
        
        当运行时动态修改环境变量后，调用此方法刷新配置
        """
        cls.WORK_DIR = Path(os.environ.get('TRANSLATION_WORK_DIR', 'files'))
        cls.COMBINED_DIR = cls.WORK_DIR / "combined"
        cls.BACKUP_DIR = cls.WORK_DIR / ".backup"
    
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

    # OpenRouter 限流较严（尤其是 stealth/免费模型），批量翻译时自动降低并发
    OPENROUTER_BATCH_MAX_WORKERS = 2

    # BAI 限流较严，批量翻译时自动降低并发为单线程
    BAI_BATCH_MAX_WORKERS = 1

    # Ollama 本地服务并发线程数，需与 launchctl setenv OLLAMA_NUM_PARALLEL 保持一致
    OLLAMA_BATCH_MAX_WORKERS = 4

    # 单文件翻译默认配置
    JOB_MAX_WORKERS = 1
    JOB_MAX_RETRIES = 6
    JOB_RETRY_DELAY = 120
    JOB_CHUNK_SIZE = 50000
    JOB_MIN_CHUNK_SIZE = 30000
    JOB_API_TIMEOUT = 60


# ================== Gemini Batch API 配置 ==================

class GeminiBatchDefaults:
    """Gemini 官方异步批处理（Batch API）默认配置

    与实时 chat.completions 批量翻译（TranslationDefaults.BATCH_*）不同，
    Gemini Batch API 是把所有翻译请求打包异步提交，由服务端排队处理，
    通常能拿到官方 Batch 档位约 50% 的价格折扣，但结果不是实时返回的。
    """

    # 文本切割参数，复用普通批量翻译的粒度
    CHUNK_SIZE = TranslationDefaults.BATCH_CHUNK_SIZE
    MIN_CHUNK_SIZE = TranslationDefaults.BATCH_MIN_CHUNK_SIZE

    # `run` 命令轮询任务状态的间隔（秒）
    POLL_INTERVAL = 30

    # 内联（inline）请求数的建议上限，超过时仅记录警告，仍会尝试提交
    MAX_INLINE_REQUESTS = 3000


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


# ================== 翻译 Prompt 配置 ==================

class TranslatePromptConfig:
    """翻译请求的 system/user prompt 配置

    源文本来自 PDF/EPUB 等文档的自动抽取，抽取过程本身会引入排版噪音
    （断行错乱、连字符断词、页眉页脚、页码、重复标题、乱码等）。
    prompt 需要显式提示模型识别并剔除这些噪音，而不是原样保留或翻译进译文。
    """

    SYSTEM_INSTRUCTION = (
        "你是一名专业的中文译者。用户提供的原文是从 PDF/扫描文档中自动抽取的文本，"
        "抽取过程可能引入断行错乱、单词被连字符拆断、页眉页脚、页码、重复标题、"
        "乱码或多余空白等噪音。翻译前请先在理解层面识别并剔除这些抽取噪音，"
        "只翻译正文的实际语义内容；不要把页码、页眉页脚、重复的章节标题等噪音"
        "翻译或保留到译文中。译文使用简体中文（白话文），要求语义忠实于原文、"
        "语言通顺自然、表达精炼，不得增删或编造原文信息。"
        "直接输出译文正文本身，不要添加解释、前后缀或其他标注。"
    )

    TRANSLATE_PROMPT_TEMPLATE = "请翻译以下文本：\n\n{text}"


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
