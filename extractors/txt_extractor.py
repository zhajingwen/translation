#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TXT 文本提取器
"""

import logging
from typing import List, Optional

from extractors.base_extractor import BaseExtractor


logger = logging.getLogger('TXTExtractor')


class TXTExtractor(BaseExtractor):
    """TXT 文本提取器"""
    
    def extract_text(self, interrupt: Optional[int] = None) -> List[str]:
        """
        从 TXT 文件中提取文本内容
        
        Args:
            interrupt: 此参数对 TXT 文件无效（因为是全文读取）
        
        Returns:
            文本内容列表，包含整个文件内容
        """
        with open(self.file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 返回完整内容，后续由 TextProcessor 进行切割
        return [content] if content else []
