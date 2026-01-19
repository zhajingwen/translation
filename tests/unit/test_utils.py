#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数单元测试
"""

import pytest
from pathlib import Path
from translation_app.core.utils import (
    count_chinese_characters,
    normalize_file_path,
    get_translated_filename,
    get_translated_path,
)


class TestUtils:
    """工具函数测试类"""
    
    def test_count_chinese_characters(self):
        """测试中文字符统计"""
        text = "这是中文123ABC"
        count = count_chinese_characters(text)
        assert count == 4  # "这是中文"
    
    def test_count_chinese_characters_empty(self):
        """测试空字符串"""
        assert count_chinese_characters("") == 0
    
    def test_count_chinese_characters_no_chinese(self):
        """测试无中文字符"""
        assert count_chinese_characters("Hello123!") == 0
    
    def test_normalize_file_path(self):
        """测试文件路径标准化"""
        result = normalize_file_path("test.txt", "files")
        assert isinstance(result, Path)
        assert result == Path("files/test.txt")
    
    def test_normalize_file_path_with_prefix(self):
        """测试带前缀的文件路径标准化"""
        result = normalize_file_path("files/test.txt", "files")
        assert result == Path("files/test.txt")
    
    def test_get_translated_filename(self):
        """测试翻译后文件名生成"""
        file_path = Path("test.pdf")
        result = get_translated_filename(file_path)
        assert result == "test translated.txt"
    
    def test_get_translated_path(self):
        """测试翻译后完整路径生成"""
        file_path = Path("files/test.pdf")
        result = get_translated_path(file_path)
        assert result == Path("files/test translated.txt")
