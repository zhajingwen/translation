#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径处理模块

提供文件路径处理和转换功能
"""

from pathlib import Path


def normalize_file_path(source_file: str, work_dir: str = "files") -> Path:
    """
    标准化文件路径，自动处理 files/ 前缀
    
    Args:
        source_file: 源文件路径
        work_dir: 工作目录，默认 "files"
    
    Returns:
        标准化后的完整路径
    """
    # 如果路径中包含 work_dir，提取文件名
    if f'{work_dir}/' in source_file:
        source_file = source_file.split(f'{work_dir}/')[1]
    
    # 构建完整路径
    return Path(work_dir) / source_file


def get_translated_filename(file_path: Path) -> str:
    """
    获取翻译后的文件名
    
    Args:
        file_path: 原文件路径
    
    Returns:
        翻译后的文件名（格式：原文件名（不含扩展名） + " translated.txt"）
    """
    base_name = file_path.stem
    return f"{base_name} translated.txt"


def get_translated_path(file_path: Path) -> Path:
    """
    获取翻译后的文件完整路径
    
    Args:
        file_path: 原文件路径
    
    Returns:
        翻译后的文件完整路径
    """
    return file_path.parent / get_translated_filename(file_path)
