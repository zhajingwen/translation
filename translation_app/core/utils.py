#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块

提供通用的工具函数：
- 文件操作（删除、重命名）
- 文件字符数统计
- 中文文件检测
- 文件路径处理
"""

import logging
from pathlib import Path
from typing import Optional

from PyPDF2 import PdfReader
from ebooklib import epub
from bs4 import BeautifulSoup

from translation_app.core.config import CharLimits


logger = logging.getLogger('Utils')


# ================== 文件操作 ==================

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


# ================== 文件字符数统计 ==================

def count_file_characters(file_path: Path) -> int:
    """
    统计文件中的文本字符数
    
    支持 txt、pdf、epub 三种文件类型
    
    Args:
        file_path: 文件路径
    
    Returns:
        字符数，如果读取失败返回 -1
    """
    file_ext = file_path.suffix.lower()
    
    try:
        if file_ext == '.txt':
            return _count_txt_characters(file_path)
        elif file_ext == '.pdf':
            return _count_pdf_characters(file_path)
        elif file_ext == '.epub':
            return _count_epub_characters(file_path)
        else:
            logger.warning(f"不支持的文件类型: {file_ext}")
            return -1
            
    except Exception as e:
        logger.error(f"读取文件字符数失败 {file_path.name}: {e}")
        return -1


def _count_txt_characters(file_path: Path) -> int:
    """统计 TXT 文件字符数"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    return len(content)


def _count_pdf_characters(file_path: Path) -> int:
    """统计 PDF 文件字符数"""
    reader = PdfReader(file_path)
    total_chars = 0
    for page in reader.pages:
        page_text = page.extract_text().strip()
        if page_text:
            total_chars += len(page_text)
    return total_chars


def _count_epub_characters(file_path: Path) -> int:
    """统计 EPUB 文件字符数"""
    book = epub.read_epub(str(file_path), options={"ignore_ncx": True})
    total_chars = 0
    for item in book.get_items():
        # 只处理HTML/XHTML内容
        if item.media_type in ['application/xhtml+xml', 'application/xhtml', 
                               'text/html', 'text/xhtml']:
            try:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                # 移除script和style标签
                for script in soup(["script", "style"]):
                    script.decompose()
                page_text = soup.get_text().strip()
                if page_text:
                    total_chars += len(page_text)
            except Exception as e:
                logger.debug(f"读取EPUB项失败: {e}")
                continue
    return total_chars


# ================== 中文文件检测 ==================

def is_file_chinese(file_path: Path, threshold: Optional[float] = None) -> bool:
    """
    判断 .txt 文件内容是否主要是中文
    
    Args:
        file_path: 文件路径（仅支持 .txt 文件）
        threshold: 中文字符占比阈值，默认使用配置值
    
    Returns:
        如果中文字符占比 >= threshold 则返回 True，否则返回 False
        如果读取失败返回 False
    """
    if threshold is None:
        threshold = CharLimits.CHINESE_RATIO_THRESHOLD
    
    file_ext = file_path.suffix.lower()
    
    # 只处理 .txt 文件
    if file_ext != '.txt':
        return False
    
    try:
        # 读取txt文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计中文字符数量（Unicode 范围 \u4e00 - \u9fff）
        chinese_count = 0
        total_chars = 0
        for char in content:
            if char.strip():  # 忽略空白字符
                total_chars += 1
                if '\u4e00' <= char <= '\u9fff':
                    chinese_count += 1
        
        # 如果总字符数为0，返回False
        if total_chars == 0:
            return False
        
        # 计算中文字符占比
        chinese_ratio = chinese_count / total_chars
        return chinese_ratio >= threshold
            
    except Exception as e:
        logger.error(f"判断文件是否中文失败 {file_path.name}: {e}")
        return False


def count_chinese_characters(text: str) -> int:
    """
    统计文本中的中文字符数量
    
    Args:
        text: 输入文本字符串
    
    Returns:
        中文字符数（仅统计汉字，不含标点、空格、英文）
    
    实现：
        使用 Unicode 范围 \u4e00 - \u9fff 判断中文字符
    """
    count = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            count += 1
    return count


# ================== 文件路径处理 ==================

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
