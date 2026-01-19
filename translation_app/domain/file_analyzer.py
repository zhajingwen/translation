#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件分析模块

提供文件内容分析功能：字符数统计、中文检测等
"""

import logging
from pathlib import Path
from typing import Optional

from translation_app.core.config import CharLimits
from translation_app.domain.extractors import get_extractor


logger = logging.getLogger('FileAnalyzer')


def count_file_characters(file_path: Path) -> int:
    """
    统计文件中的文本字符数
    
    支持 txt、pdf、epub 三种文件类型
    
    Args:
        file_path: 文件路径
    
    Returns:
        字符数，如果读取失败返回 -1
    """
    file_ext = file_path.suffix.lower()
    
    try:
        if file_ext == '.txt':
            return _count_txt_characters(file_path)
        elif file_ext == '.pdf':
            return _count_using_extractor(file_path, 'pdf')
        elif file_ext == '.epub':
            return _count_using_extractor(file_path, 'epub')
        else:
            logger.warning(f"不支持的文件类型: {file_ext}")
            return -1
            
    except Exception as e:
        logger.error(f"读取文件字符数失败 {file_path.name}: {e}")
        return -1


def _count_txt_characters(file_path: Path) -> int:
    """统计 TXT 文件字符数"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    return len(content)


def _count_using_extractor(file_path: Path, file_type: str) -> int:
    """
    使用提取器统计文件字符数
    
    Args:
        file_path: 文件路径
        file_type: 文件类型 ('pdf' 或 'epub')
    
    Returns:
        字符数
    """
    extractor = get_extractor(str(file_path))
    content_list = extractor.extract_text()
    
    total_chars = 0
    for content in content_list:
        if content:
            total_chars += len(content.strip())
    
    return total_chars


def is_file_chinese(file_path: Path, threshold: Optional[float] = None) -> bool:
    """
    判断 .txt 文件内容是否主要是中文
    
    Args:
        file_path: 文件路径（仅支持 .txt 文件）
        threshold: 中文字符占比阈值，默认使用配置值
    
    Returns:
        如果中文字符占比 >= threshold 则返回 True，否则返回 False
        如果读取失败返回 False
    """
    if threshold is None:
        threshold = CharLimits.CHINESE_RATIO_THRESHOLD
    
    file_ext = file_path.suffix.lower()
    
    # 只处理 .txt 文件
    if file_ext != '.txt':
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计中文字符数量
        chinese_count = 0
        total_chars = 0
        for char in content:
            if char.strip():  # 忽略空白字符
                total_chars += 1
                if '\u4e00' <= char <= '\u9fff':
                    chinese_count += 1
        
        if total_chars == 0:
            return False
        
        chinese_ratio = chinese_count / total_chars
        return chinese_ratio >= threshold
            
    except Exception as e:
        logger.error(f"判断文件是否中文失败 {file_path.name}: {e}")
        return False


def count_chinese_characters(text: str) -> int:
    """
    统计文本中的中文字符数量
    
    Args:
        text: 输入文本字符串
    
    Returns:
        中文字符数（仅统计汉字，不含标点、空格、英文）
    
    实现：
        使用 Unicode 范围 \\u4e00 - \\u9fff 判断中文字符
    """
    count = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            count += 1
    return count
