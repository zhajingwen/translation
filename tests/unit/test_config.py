#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模块单元测试
"""

import pytest
from pathlib import Path
from translation_app.core.config import (
    PathConfig,
    CharLimits,
    TranslationDefaults,
    LogConfig,
    FileFormats,
)


class TestPathConfig:
    """PathConfig 测试类"""
    
    def test_work_dir(self):
        """测试工作目录配置"""
        assert PathConfig.WORK_DIR == Path("files")
    
    def test_combined_dir(self):
        """测试合并目录配置"""
        assert PathConfig.COMBINED_DIR == Path("files/combined")
    
    def test_backup_dir(self):
        """测试备份目录配置"""
        assert PathConfig.BACKUP_DIR == Path("files/.backup")


class TestCharLimits:
    """CharLimits 测试类"""
    
    def test_min_file_chars(self):
        """测试最小文件字符数"""
        assert CharLimits.MIN_FILE_CHARS == 1000
    
    def test_small_file_limit(self):
        """测试小文件上限"""
        assert CharLimits.SMALL_FILE_LIMIT == 100000
    
    def test_merge_file_limit(self):
        """测试合并文件上限"""
        assert CharLimits.MERGE_FILE_LIMIT == 200000
    
    def test_chinese_ratio_threshold(self):
        """测试中文比例阈值"""
        assert CharLimits.CHINESE_RATIO_THRESHOLD == 0.3


class TestTranslationDefaults:
    """TranslationDefaults 测试类"""
    
    def test_batch_config(self):
        """测试批量翻译配置"""
        assert TranslationDefaults.BATCH_MAX_WORKERS == 8
        assert TranslationDefaults.BATCH_MAX_RETRIES == 6
        assert TranslationDefaults.BATCH_RETRY_DELAY == 120
    
    def test_job_config(self):
        """测试单文件翻译配置"""
        assert TranslationDefaults.JOB_MAX_WORKERS == 1
        assert TranslationDefaults.JOB_MAX_RETRIES == 6
        assert TranslationDefaults.JOB_RETRY_DELAY == 120


class TestFileFormats:
    """FileFormats 测试类"""
    
    def test_supported_extensions(self):
        """测试支持的文件扩展名"""
        assert '.txt' in FileFormats.SUPPORTED_EXTENSIONS
        assert '.pdf' in FileFormats.SUPPORTED_EXTENSIONS
        assert '.epub' in FileFormats.SUPPORTED_EXTENSIONS
    
    def test_translated_suffix(self):
        """测试翻译后缀"""
        assert FileFormats.TRANSLATED_SUFFIX == " translated.txt"
