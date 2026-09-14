#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 文本提取器
"""

import logging
from typing import List, Optional

import pymupdf as fitz
import pytesseract
from PIL import Image
from PyPDF2 import PdfReader
from PyPDF2._page import PageObject

from translation_app.domain.extractors.base_extractor import BaseExtractor


logger = logging.getLogger('PDFExtractor')

# 扫描件目前只处理英文文档，如需支持其他语种需额外安装 tesseract 对应语言包
OCR_LANGUAGE = 'eng'
OCR_RENDER_DPI = 300


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
        # 扫描件（无文本层）走 OCR 兜底时才需要渲染页面图片，这里懒加载，避免拖慢正常 PDF 的处理
        ocr_doc = None
        num = 0
        content = []

        try:
            for page in reader.pages:
                num += 1
                # 跳过前面已经翻译过的页面，从上一次翻译异常的页面重新开始
                if interrupt and num < interrupt:
                    continue

                logger.debug(f'[提取][PDF] 处理第 {num} 页')
                try:
                    page_text = page.extract_text()
                except Exception as e:
                    logger.warning(f'[提取][PDF] 第 {num} 页提取失败，跳过该页: {e}')
                    continue

                page_text = page_text.strip()

                if not page_text and self._is_scanned_page(page):
                    if ocr_doc is None:
                        ocr_doc = fitz.open(self.file_path)
                    page_text = self._ocr_page(ocr_doc, num - 1)

                if not page_text:
                    continue

                content.append(page_text)
        finally:
            if ocr_doc is not None:
                ocr_doc.close()

        return content

    @staticmethod
    def _is_scanned_page(page: PageObject) -> bool:
        """
        判断该页是否为扫描页：本身没有文本层，但内嵌了图片（通常是整页扫描图）
        """
        try:
            return len(page.images) > 0
        except Exception as e:
            logger.debug(f'[提取][PDF] 读取页面图片信息失败: {e}')
            return False

    @staticmethod
    def _ocr_page(ocr_doc: 'fitz.Document', page_index: int) -> str:
        """
        将指定页面渲染为图片后做 OCR 识别（目前仅支持英文）

        Args:
            ocr_doc: 用于渲染页面的 PyMuPDF 文档对象
            page_index: 页码（从 0 开始）
        """
        try:
            zoom = OCR_RENDER_DPI / 72
            matrix = fitz.Matrix(zoom, zoom)
            pixmap = ocr_doc[page_index].get_pixmap(matrix=matrix, colorspace=fitz.csRGB)
            image = Image.frombytes('RGB', (pixmap.width, pixmap.height), pixmap.samples)
            text = pytesseract.image_to_string(image, lang=OCR_LANGUAGE)
        except Exception as e:
            logger.warning(f'[提取][PDF] 第 {page_index + 1} 页 OCR 识别失败，跳过该页: {e}')
            return ''

        text = text.strip()
        if text:
            logger.info(f'[提取][PDF] 第 {page_index + 1} 页无文本层，已通过 OCR 识别')
        return text
