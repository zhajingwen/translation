#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础提取器接口

定义文本提取器的通用接口
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional


logger = logging.getLogger('BaseExtractor')


class BaseExtractor(ABC):
    """文本提取器基类"""
    
    def __init__(self, file_path: str):
        """
        初始化提取器
        
        Args:
            file_path: 文件路径
        """
        self.file_path = file_path
    
    @abstractmethod
    def extract_text(self, interrupt: Optional[int] = None) -> List[str]:
        """
        提取文本内容
        
        Args:
            interrupt: 上一次处理中断的位置（页码或项索引），None表示从头开始
        
        Returns:
            文本内容列表，每个元素是一页或一个chunk的内容
        """
        pass
    
    def is_blank_page(self, text: str) -> bool:
        """
        判断页面是否为空白页
        
        Args:
            text: 页面文本
        
        Returns:
            是否为空白页
        """
        if text is None:
            return True
        
        # 去除首尾空白
        text_clean = text.strip()
        
        # 1. 空字符串
        if len(text_clean) == 0:
            return True
        
        # 2. 检查是否只包含空白字符和控制字符
        printable_chars = sum(1 for c in text_clean if c.isprintable() and not c.isspace())
        total_chars = len(text_clean)
        
        # 可打印字符少于2个，直接认为空白
        if printable_chars < 2:
            return True
        
        # 可打印字符比例小于10%也认为空白
        if total_chars > 0 and printable_chars / total_chars < 0.1:
            return True
        
        # 3. 检查是否只包含常见的HTML空白实体和特殊字符
        blank_chars = [' ', '\n', '\t', '\r', '\xa0', '\u2000', '\u2001', 
                      '\u2002', '\u2003', '\u2004', '\u2005', '\u2006', 
                      '\u2007', '\u2008', '\u2009', '\u200a', '\u202f', '\u205f']
        blank_chars_only = all(c in blank_chars for c in text_clean)
        if blank_chars_only:
            return True
        
        # 4. 如果是纯标点符号或特殊符号（没有实际内容）
        if len(text_clean) < 20 and all(not c.isalnum() for c in text_clean):
            return True
        
        return False
