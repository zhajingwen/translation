#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TextProcessor 单元测试
"""

import pytest
from translation_app.domain.text_processor import TextProcessor


class TestTextProcessor:
    """TextProcessor 测试类"""
    
    def test_init(self):
        """测试初始化"""
        processor = TextProcessor(chunk_size=1000, min_chunk_size=100)
        assert processor.chunk_size == 1000
        assert processor.min_chunk_size == 100
    
    def test_process_empty_content(self):
        """测试空内容处理"""
        processor = TextProcessor()
        result = processor.process_extracted_content([])
        assert result == []
    
    def test_process_small_content(self):
        """测试小内容处理（不需要切割）"""
        processor = TextProcessor(chunk_size=1000)
        content = ["短文本1", "短文本2"]
        result = processor.process_extracted_content(content)
        assert len(result) == 1
        assert "短文本1" in result[0]
        assert "短文本2" in result[0]
    
    def test_process_large_content(self):
        """测试大内容处理（需要切割）"""
        processor = TextProcessor(chunk_size=100, min_chunk_size=50)
        # 创建超过 chunk_size 的内容
        large_content = "这是一个很长的句子。" * 20
        result = processor.process_extracted_content([large_content])
        assert len(result) > 1  # 应该被切割成多个块
    
    def test_find_split_point(self):
        """测试切割点查找"""
        processor = TextProcessor(chunk_size=100, min_chunk_size=50)
        text = "这是第一句话。这是第二句话。这是第三句话。"
        split_point = processor._find_split_point(text, 20)
        assert split_point > 0
        # 应该在句号后切割
        assert text[split_point - 1] == '。'
