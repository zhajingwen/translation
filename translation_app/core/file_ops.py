#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件操作模块

提供安全的文件操作功能
"""

import logging
from pathlib import Path


logger = logging.getLogger('FileOps')


def safe_delete(file_path: Path) -> bool:
    """
    安全删除文件，捕获异常并记录
    
    Args:
        file_path: 文件路径
    
    Returns:
        是否删除成功
    """
    try:
        file_path.unlink()
        logger.info(f"已删除: {file_path.name}")
        return True
    except Exception as e:
        logger.error(f"删除失败 {file_path.name}: {e}")
        return False


def safe_rename(file_path: Path, new_name: str) -> bool:
    """
    安全重命名文件，捕获异常并记录
    
    Args:
        file_path: 原文件路径
        new_name: 新文件名（不含路径）
    
    Returns:
        是否重命名成功
    """
    try:
        new_path = file_path.parent / new_name
        # 如果目标文件已存在，不重命名
        if new_path.exists():
            logger.warning(f"重命名失败，目标文件已存在: {new_name}")
            return False
        file_path.rename(new_path)
        logger.info(f"重命名: {file_path.name} -> {new_name}")
        return True
    except Exception as e:
        logger.error(f"重命名失败 {file_path.name}: {e}")
        return False
