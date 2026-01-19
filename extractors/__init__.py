#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本提取器模块

提供统一的文本提取接口，支持多种文件格式：
- PDF
- EPUB
- TXT
"""

from extractors.base_extractor import BaseExtractor
from extractors.pdf_extractor import PDFExtractor
from extractors.epub_extractor import EPUBExtractor
from extractors.txt_extractor import TXTExtractor


def get_extractor(file_path: str) -> BaseExtractor:
    """
    根据文件类型获取对应的提取器
    
    Args:
        file_path: 文件路径
    
    Returns:
        对应的提取器实例
    
    Raises:
        ValueError: 不支持的文件类型
    """
    file_lower = file_path.lower()
    
    if file_lower.endswith('.pdf'):
        return PDFExtractor(file_path)
    elif file_lower.endswith('.epub'):
        return EPUBExtractor(file_path)
    elif file_lower.endswith('.txt'):
        return TXTExtractor(file_path)
    else:
        raise ValueError(f'不支持的文件类型: {file_path}')


__all__ = [
    'BaseExtractor',
    'PDFExtractor',
    'EPUBExtractor',
    'TXTExtractor',
    'get_extractor',
]
