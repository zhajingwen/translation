#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本处理模块

提供文本切割和分块功能：
- 智能文本切割（保持句子完整性）
- 超长行切割
- 文本分块
"""

import logging
from typing import List, Tuple

from config import SENTENCE_END_PUNCTUATION, SECONDARY_PUNCTUATION


logger = logging.getLogger('TextProcessor')


class TextProcessor:
    """文本处理器"""
    
    def __init__(self, chunk_size: int = 8000, min_chunk_size: int = 500):
        """
        初始化文本处理器
        
        Args:
            chunk_size: 文本切割阈值（字符数），默认 8000
            min_chunk_size: 最小切割长度（字符数），默认 500
        """
        self.chunk_size = chunk_size
        self.min_chunk_size = min_chunk_size
    
    def is_sentence_end(self, line: str) -> bool:
        """
        判断一行是否以句子结束标点结尾
        
        Args:
            line: 文本行
        
        Returns:
            是否以句子结束标点结尾
        """
        line = line.rstrip()
        if not line:
            return False
        return line[-1] in SENTENCE_END_PUNCTUATION
    
    def split_long_line(self, line: str) -> List[str]:
        """
        处理超长单行，按句子标点或固定长度切割
        
        Args:
            line: 需要切割的单行文本
        
        Returns:
            切割后的行列表
        """
        if len(line) <= self.chunk_size:
            return [line]
        
        result = []
        remaining = line
        
        while len(remaining) > self.chunk_size:
            # 在 chunk_size 范围内查找最后一个句子结束标点
            search_range = remaining[:self.chunk_size]
            cut_pos = -1
            
            # 从后向前查找句子结束标点
            for i in range(len(search_range) - 1, -1, -1):
                if search_range[i] in SENTENCE_END_PUNCTUATION:
                    cut_pos = i + 1  # 包含标点符号
                    break
            
            if cut_pos > 0:
                # 找到句子结束点，在此处切割
                result.append(remaining[:cut_pos])
                remaining = remaining[cut_pos:].lstrip()
            else:
                # 未找到句子结束标点，查找次要断句点
                for i in range(len(search_range) - 1, -1, -1):
                    if search_range[i] in SECONDARY_PUNCTUATION:
                        cut_pos = i + 1
                        break
                
                if cut_pos > 0:
                    result.append(remaining[:cut_pos])
                    remaining = remaining[cut_pos:].lstrip()
                else:
                    # 无任何断句点，强制按 chunk_size 切割
                    result.append(remaining[:self.chunk_size])
                    remaining = remaining[self.chunk_size:]
        
        # 添加剩余内容
        if remaining:
            result.append(remaining)
        
        return result
    
    def split_text_to_chunks(self, content: str) -> List[str]:
        """
        将文本切割成多个 chunk
        优先在句子结束标点处切割，保持语义完整性
        
        切割优先级：
        1. 优先在以句子结束标点（。！？…. ! ?）结尾的行处切割
        2. 如果找不到，退而求其次在任意行边界切割
        
        Args:
            content: 要切割的文本内容
        
        Returns:
            切割后的 chunk 列表
        """
        if len(content) <= self.chunk_size:
            return [content]
        
        page_list = []
        rows = content.split('\n')
        
        # 预处理：对超长单行进行切割
        processed_rows = []
        for row in rows:
            if len(row) > self.chunk_size:
                # 超长行需要切割
                split_lines = self.split_long_line(row)
                processed_rows.extend(split_lines)
            else:
                processed_rows.append(row)
        
        current_chunk_rows = []
        current_length = 0
        last_sentence_end_index = -1  # 记录最后一个句子结束点
        
        for i, row in enumerate(processed_rows):
            row_length = len(row) + 1  # +1 for newline
            
            # 检查是否是句子结束行
            if self.is_sentence_end(row):
                last_sentence_end_index = len(current_chunk_rows)
            
            # 如果加入当前行会超过阈值，且当前块已达到最小长度要求
            if (current_length + row_length > self.chunk_size and 
                current_chunk_rows and 
                current_length >= self.min_chunk_size):
                
                # 优先在最后一个句子结束点切割
                if last_sentence_end_index >= 0:
                    cut_point = last_sentence_end_index + 1
                    page_list.append('\n'.join(current_chunk_rows[:cut_point]))
                    # 保留未切割的行
                    current_chunk_rows = current_chunk_rows[cut_point:]
                    current_length = sum(len(r) + 1 for r in current_chunk_rows)
                    # 重新计算保留行中的句子结束点
                    last_sentence_end_index = -1
                    for idx, remaining_row in enumerate(current_chunk_rows):
                        if self.is_sentence_end(remaining_row):
                            last_sentence_end_index = idx
                else:
                    # 没有句子结束点，在当前位置切割
                    page_list.append('\n'.join(current_chunk_rows))
                    current_chunk_rows = []
                    current_length = 0
                    last_sentence_end_index = -1
            
            current_chunk_rows.append(row)
            current_length += row_length
        
        # 处理最后剩余的内容
        if current_chunk_rows:
            last_chunk = '\n'.join(current_chunk_rows)
            if len(last_chunk) < self.min_chunk_size and page_list:
                # 合并到前一块
                page_list[-1] = page_list[-1] + '\n' + last_chunk
            else:
                page_list.append(last_chunk)
        
        return page_list
    
    def process_extracted_content(self, content_list: List[str]) -> List[str]:
        """
        处理提取的内容列表，合并后统一切割
        
        Args:
            content_list: 提取器返回的内容列表（每个元素可能是一页或一个段落）
        
        Returns:
            切割后的 chunk 列表
        """
        # 合并所有内容
        full_content = '\n'.join(content_list)
        
        # 统一切割
        return self.split_text_to_chunks(full_content)
