#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 文本提取器
"""

import logging
from typing import List, Optional

from PyPDF2 import PdfReader

from extractors.base_extractor import BaseExtractor


logger = logging.getLogger('PDFExtractor')


class PDFExtractor(BaseExtractor):
    """PDF 文本提取器"""
    
    def extract_text(self, interrupt: Optional[int] = None) -> List[str]:
        """
        从 PDF 文件中提取文本内容
        
        Args:
            interrupt: 上一次翻译异常导致退出的页码，None表示没有任何异常导致中途退出
        
        Returns:
            文本内容列表，每个元素是一页的内容
        """
        reader = PdfReader(self.file_path)
        num = 0
        content = []
        
        for page in reader.pages:
            num += 1
            # 跳过前面已经翻译过的页面，从上一次翻译异常的页面重新开始
            if interrupt and num < interrupt:
                continue
            
            logger.debug(f'[提取][PDF] 处理第 {num} 页')
            page_text = page.extract_text()
            page_text = page_text.strip()
            
            if not page_text:
                continue
            
            content.append(page_text)
        
        return content
