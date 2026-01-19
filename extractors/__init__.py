#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本提取器模块（兼容入口）
"""

from translation_app.domain.extractors import (
    BaseExtractor,
    PDFExtractor,
    EPUBExtractor,
    TXTExtractor,
    get_extractor
)

__all__ = [
    'BaseExtractor',
    'PDFExtractor',
    'EPUBExtractor',
    'TXTExtractor',
    'get_extractor',
]

