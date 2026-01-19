#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件预处理服务

提供批量翻译前的文件预处理功能
"""

import logging
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass

from translation_app.core.config import CharLimits, FileFormats
from translation_app.core.file_ops import safe_delete, safe_rename
from translation_app.core.file_analyzer import count_file_characters, is_file_chinese
from translation_app.core.path_utils import get_translated_path


logger = logging.getLogger('FilePreprocessor')


@dataclass
class PreprocessStats:
    """预处理统计"""
    skipped_already_translated: int = 0
    skipped_already_chinese: int = 0
    skipped_char_too_few: int = 0
    skipped_result_exists: int = 0
    
    @property
    def total_skipped(self) -> int:
        """总跳过数"""
        return (
            self.skipped_already_translated +
            self.skipped_already_chinese +
            self.skipped_char_too_few +
            self.skipped_result_exists
        )


class FilePreprocessor:
    """文件预处理器"""
    
    def __init__(self):
        self.stats = PreprocessStats()
    
    def preprocess_files(self, files: List[Path]) -> Tuple[List[Path], PreprocessStats]:
        """
        预处理文件列表
        
        Args:
            files: 待处理的文件列表
        
        Returns:
            (需要处理的文件列表, 预处理统计)
        """
        self.stats = PreprocessStats()
        files_to_process = []
        
        for file_path in files:
            if self._should_process_file(file_path):
                files_to_process.append(file_path)
        
        return files_to_process, self.stats
    
    def _should_process_file(self, file_path: Path) -> bool:
        """
        判断文件是否需要处理
        
        Args:
            file_path: 文件路径
        
        Returns:
            是否需要处理
        """
        file_name = file_path.name
        
        # 策略 1: 跳过已翻译文件
        if self._is_already_translated(file_name):
            self.stats.skipped_already_translated += 1
            logger.debug(f"[预处理] 跳过已翻译文件: {file_name}")
            return False
        
        # 策略 2: 检测并重命名中文文件（仅针对 .txt 文件）
        if self._is_chinese_file(file_path):
            self.stats.skipped_already_chinese += 1
            self._rename_chinese_file(file_path)
            return False
        
        # 策略 3: 删除字符数不足的文件
        if self._is_char_count_too_low(file_path):
            self.stats.skipped_char_too_few += 1
            self._delete_small_file(file_path)
            return False
        
        # 策略 4: 跳过已存在翻译结果的文件
        if self._translation_result_exists(file_path):
            self.stats.skipped_result_exists += 1
            self._delete_original_with_result(file_path)
            return False
        
        return True
    
    def _is_already_translated(self, file_name: str) -> bool:
        """判断是否已翻译文件"""
        return file_name.endswith(FileFormats.TRANSLATED_SUFFIX)
    
    def _is_chinese_file(self, file_path: Path) -> bool:
        """判断是否中文文件（仅 .txt）"""
        return file_path.suffix.lower() == '.txt' and is_file_chinese(file_path)
    
    def _is_char_count_too_low(self, file_path: Path) -> bool:
        """判断字符数是否过少"""
        char_count = count_file_characters(file_path)
        return 0 <= char_count < CharLimits.MIN_FILE_CHARS
    
    def _translation_result_exists(self, file_path: Path) -> bool:
        """判断翻译结果是否已存在"""
        translated_path = get_translated_path(file_path)
        return translated_path.exists()
    
    def _rename_chinese_file(self, file_path: Path):
        """重命名中文文件"""
        new_name = f"{file_path.stem}{FileFormats.TRANSLATED_SUFFIX}"
        if safe_rename(file_path, new_name):
            logger.info(f"[预处理] 跳过中文文件并重命名: {file_path.name} -> {new_name}")
        else:
            logger.info(f"[预处理] 跳过中文文件（重命名失败）: {file_path.name}")
    
    def _delete_small_file(self, file_path: Path):
        """删除字符数不足的文件"""
        char_count = count_file_characters(file_path)
        logger.info(
            f"[预处理] 删除文件（字符数 {char_count} < {CharLimits.MIN_FILE_CHARS}）: "
            f"{file_path.name}"
        )
        safe_delete(file_path)
    
    def _delete_original_with_result(self, file_path: Path):
        """删除已有翻译结果的原文件"""
        logger.info(f"[预处理] 删除文件（已存在翻译结果）: {file_path.name}")
        safe_delete(file_path)
    
    def log_stats(self):
        """记录统计信息"""
        if self.stats.total_skipped == 0:
            return
        
        logger.info('[任务] 预处理统计:')
        if self.stats.skipped_already_translated > 0:
            logger.info(f'  - 跳过已翻译文件: {self.stats.skipped_already_translated} 个')
        if self.stats.skipped_already_chinese > 0:
            logger.info(f'  - 跳过中文文件: {self.stats.skipped_already_chinese} 个（不删除）')
        if self.stats.skipped_char_too_few > 0:
            logger.info(
                f'  - 删除字符数不足文件: {self.stats.skipped_char_too_few} 个'
                f'（字符数 < {CharLimits.MIN_FILE_CHARS}）'
            )
        if self.stats.skipped_result_exists > 0:
            logger.info(f'  - 删除已存在翻译结果的文件: {self.stats.skipped_result_exists} 个')
        logger.info(f'  - 预处理跳过总计: {self.stats.total_skipped} 个文件')
