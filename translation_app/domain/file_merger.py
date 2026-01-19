#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件合并器（领域层）

提供文件合并的核心算法，不涉及 IO 操作
"""

import re
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass


def natural_sort_key(path: Path) -> list:
    """
    自然排序键函数，支持数字前缀的正确排序
    
    例如: ["1.txt", "2.txt", "10.txt"] 会正确排序
    而不是 ["1.txt", "10.txt", "2.txt"]
    
    Args:
        path: 文件路径
    
    Returns:
        用于排序的键列表
    """
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r'(\d+)', path.name)
    ]


@dataclass
class MergeGroup:
    """合并组：表示一组将要合并的文件"""
    files: List[Tuple[Path, int]]  # [(文件路径, 字符数), ...]
    total_chars: int = 0
    
    def add_file(self, file_path: Path, char_count: int):
        """添加文件到组"""
        self.files.append((file_path, char_count))
        self.total_chars += char_count
    
    @property
    def file_names(self) -> List[str]:
        """获取所有文件名"""
        return [f.name for f, _ in self.files]
    
    @property
    def file_count(self) -> int:
        """获取文件数量"""
        return len(self.files)


class FileMerger:
    """
    文件合并器
    
    负责将文件列表按字符数限制分组，不涉及实际的文件读写操作
    """
    
    def __init__(self, merge_limit: int):
        """
        初始化合并器
        
        Args:
            merge_limit: 单个合并文件的最大字符数
        """
        self.merge_limit = merge_limit
    
    def group_files(
        self, 
        file_list: List[Tuple[Path, int]]
    ) -> List[MergeGroup]:
        """
        将文件列表按字符数限制分组
        
        算法：贪心算法，依次添加文件，当超过限制时创建新组
        
        Args:
            file_list: [(文件路径, 字符数), ...] 列表
        
        Returns:
            分组列表
        """
        if not file_list:
            return []
        
        groups = []
        current_group = MergeGroup(files=[])
        
        for file_path, char_count in file_list:
            # 如果当前组不为空且添加后会超限，则保存当前组并创建新组
            if (current_group.file_count > 0 and 
                current_group.total_chars + char_count > self.merge_limit):
                groups.append(current_group)
                current_group = MergeGroup(files=[])
            
            current_group.add_file(file_path, char_count)
        
        # 添加最后一个组
        if current_group.file_count > 0:
            groups.append(current_group)
        
        return groups
    
    def sort_files(
        self, 
        file_list: List[Tuple[Path, int]]
    ) -> List[Tuple[Path, int]]:
        """
        按自然排序对文件列表排序
        
        Args:
            file_list: [(文件路径, 字符数), ...] 列表
        
        Returns:
            排序后的列表
        """
        return sorted(file_list, key=lambda x: natural_sort_key(x[0]))
    
    def filter_by_char_limit(
        self, 
        file_list: List[Tuple[Path, int]], 
        char_limit: int
    ) -> List[Tuple[Path, int]]:
        """
        筛选字符数小于指定限制的文件
        
        Args:
            file_list: [(文件路径, 字符数), ...] 列表
            char_limit: 字符数上限
        
        Returns:
            筛选后的列表
        """
        return [(path, count) for path, count in file_list if count < char_limit]
