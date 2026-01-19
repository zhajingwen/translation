"""
文本提取器（领域层）
"""

from translation_app.domain.extractors.base_extractor import BaseExtractor
from translation_app.domain.extractors.pdf_extractor import PDFExtractor
from translation_app.domain.extractors.epub_extractor import EPUBExtractor
from translation_app.domain.extractors.txt_extractor import TXTExtractor


def get_extractor(file_path: str) -> BaseExtractor:
    """
    根据文件类型获取对应的提取器
    """
    file_lower = file_path.lower()

    if file_lower.endswith('.pdf'):
        return PDFExtractor(file_path)
    if file_lower.endswith('.epub'):
        return EPUBExtractor(file_path)
    if file_lower.endswith('.txt'):
        return TXTExtractor(file_path)
    raise ValueError(f'不支持的文件类型: {file_path}')


__all__ = [
    'BaseExtractor',
    'PDFExtractor',
    'EPUBExtractor',
    'TXTExtractor',
    'get_extractor',
]

