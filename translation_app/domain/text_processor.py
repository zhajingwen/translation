#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本处理器模块

提供智能文本切割功能，保持句子完整性
"""

import logging
from typing import List

from translation_app.core.config import SENTENCE_END_PUNCTUATION, SECONDARY_PUNCTUATION


logger = logging.getLogger('TextProcessor')


class TextProcessor:
    """
    文本处理器：智能切割文本，保持句子完整性

    功能：
    - 将提取器返回的内容列表切割成合适大小的文本块
    - 优先在句子边界处切割，保持语义完整性
    - 处理超长文本的递归切割
    """

    def __init__(self, chunk_size: int = 8000, min_chunk_size: int = 500):
        """
        初始化文本处理器

        Args:
            chunk_size: 文本切割阈值（字符数），默认 8000
            min_chunk_size: 最小切割长度（字符数），默认 500
        """
        self.chunk_size = chunk_size
        self.min_chunk_size = min_chunk_size
        logger.debug(f'[初始化] chunk_size={chunk_size}, min_chunk_size={min_chunk_size}')

    def process_extracted_content(self, content_list: List[str]) -> List[str]:
        """
        处理提取器返回的内容列表，切割成合适大小的文本块

        Args:
            content_list: 提取器返回的内容列表（每个元素是一页或一个章节）

        Returns:
            切割后的文本块列表
        """
        if not content_list:
            logger.warning('[处理] 输入内容为空')
            return []

        chunks = []
        current_chunk = ""

        for content in content_list:
            # 跳过空内容
            if not content or not content.strip():
                continue

            # 如果当前内容本身就超过 chunk_size，需要单独切割
            if len(content) > self.chunk_size:
                # 先保存当前积累的内容
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # 切割超长内容
                large_chunks = self._split_large_text(content)
                chunks.extend(large_chunks)
                continue

            # 检查是否可以合并到当前块
            if len(current_chunk) + len(content) <= self.chunk_size:
                # 可以合并
                current_chunk += content + "\n"
            else:
                # 不能合并，需要切割当前块
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = content + "\n"

        # 添加最后一个块
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        logger.info(f'[处理] 完成，共切割成 {len(chunks)} 个chunk')
        return chunks

    def _split_large_text(self, text: str) -> List[str]:
        """
        切割超长文本，在句子边界处切割

        Args:
            text: 需要切割的超长文本

        Returns:
            切割后的文本块列表
        """
        chunks = []
        remaining_text = text

        while len(remaining_text) > self.chunk_size:
            # 在 chunk_size 附近寻找切割点
            split_point = self._find_split_point(remaining_text, self.chunk_size)

            if split_point == -1:
                # 找不到合适的切割点，强制在 chunk_size 处切割
                logger.warning(f'[切割] 未找到合适的切割点，强制切割 (长度={len(remaining_text)})')
                split_point = self.chunk_size

            # 切割文本
            chunk = remaining_text[:split_point].strip()
            if chunk:
                chunks.append(chunk)

            remaining_text = remaining_text[split_point:].strip()

        # 添加剩余文本
        if remaining_text.strip():
            chunks.append(remaining_text.strip())

        logger.debug(f'[切割] 大文本切割完成，共 {len(chunks)} 个chunk')
        return chunks

    def _find_split_point(self, text: str, target_length: int) -> int:
        """
        在文本中寻找最佳切割点

        策略：
        1. 从 target_length 位置向前搜索，优先在句子结束标点处切割
        2. 如果找不到句子结束标点，尝试在次要标点处切割
        3. 搜索范围为 [min_chunk_size, target_length]

        Args:
            text: 文本内容
            target_length: 目标长度

        Returns:
            切割位置索引，-1 表示未找到合适的切割点
        """
        if len(text) <= target_length:
            return len(text)

        # 搜索范围：从 target_length 向前到 min_chunk_size
        search_start = max(self.min_chunk_size, target_length - 1000)
        search_end = min(target_length, len(text))

        # 策略 1: 寻找句子结束标点
        for i in range(search_end - 1, search_start - 1, -1):
            if text[i] in SENTENCE_END_PUNCTUATION:
                # 找到句子结束标点，在其后切割
                return i + 1

        # 策略 2: 寻找次要标点
        for i in range(search_end - 1, search_start - 1, -1):
            if text[i] in SECONDARY_PUNCTUATION:
                # 找到次要标点，在其后切割
                return i + 1

        # 策略 3: 寻找空白字符
        for i in range(search_end - 1, search_start - 1, -1):
            if text[i].isspace():
                return i + 1

        # 未找到合适的切割点
        return -1

