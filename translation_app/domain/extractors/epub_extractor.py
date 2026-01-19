#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB 文本提取器
"""

import logging
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Optional

from ebooklib import epub
from bs4 import BeautifulSoup

from translation_app.domain.extractors.base_extractor import BaseExtractor
from config import FileFormats


logger = logging.getLogger('EPUBExtractor')


class EPUBExtractor(BaseExtractor):
    """EPUB 文本提取器"""

    def extract_text(self, interrupt: Optional[int] = None) -> List[str]:
        """
        从 EPUB 文件中提取文本内容

        Args:
            interrupt: 上一次翻译异常导致退出的页码，None表示没有任何异常导致中途退出

        Returns:
            文本内容列表，每个元素是一个HTML项的内容
        """
        try:
            book = epub.read_epub(self.file_path, options={"ignore_ncx": True})
        except IndexError as e:
            logger.warning(f'[提取][EPUB] 标准方式读取失败: {e}')
            logger.info('[提取][EPUB] 尝试备用方式读取...')
            try:
                book = epub.read_epub(self.file_path)
            except Exception as e2:
                logger.warning(f'[提取][EPUB] 备用方式也失败: {e2}')
                # 手动解析 EPUB 文件
                return self._manual_extract(interrupt)

        # 收集所有需要处理的 HTML/XHTML 内容
        html_items = self._collect_html_items(book)

        # 提取内容
        return self._extract_from_items(html_items, interrupt)

    def _collect_html_items(self, book) -> List:
        """收集所有 HTML/XHTML 项"""
        html_items = []
        skipped_items = []

        for item in book.get_items():
            if item.media_type in FileFormats.EPUB_MIME_TYPES:
                try:
                    html_items.append(item)
                except Exception as e:
                    logger.error(f'[提取][EPUB] 处理HTML项时出错: {e}')
                    skipped_items.append((item.get_name(), item.media_type))
            else:
                skipped_items.append((item.get_name(), item.media_type))

        if skipped_items:
            logger.debug(f'[提取][EPUB] 跳过 {len(skipped_items)} 个非正文项目')

        return html_items

    def _extract_from_items(self, html_items: List, interrupt: Optional[int]) -> List[str]:
        """从 HTML 项中提取文本"""
        num = 0
        content = []
        blank_count = 0

        for item in html_items:
            num += 1
            if interrupt and num < interrupt:
                continue

            logger.debug(f'[提取][EPUB] 处理第 {num} 项')

            try:
                soup = BeautifulSoup(item.get_content(), 'html.parser')

                # 移除 script 和 style 标签
                for script in soup(["script", "style"]):
                    script.decompose()

                # 提取文本，保留换行
                page_text = soup.get_text(separator='\n', strip=True)

                # 检查和过滤空白页
                if self.is_blank_page(page_text):
                    blank_count += 1
                    logger.debug(f'[提取][EPUB] 第 {num} 项为空白页，已跳过')
                    continue

                content.append(page_text)

            except Exception as e:
                logger.error(f'[提取][EPUB] 处理第 {num} 项时出错: {e}')
                content.append(f"[处理出错: {e}]")

        logger.info(f'[提取][EPUB] 完成，有效内容: {len(content)} 项，过滤空白: {blank_count} 项')
        return content

    def _manual_extract(self, interrupt: Optional[int]) -> List[str]:
        """手动解析 EPUB 文件（降级方案）"""
        logger.info('[提取][EPUB] 尝试手动解析...')

        html_items = []

        with zipfile.ZipFile(self.file_path, 'r') as zip_ref:
            # 读取 container.xml 找到 OPF 文件
            container_xml = zip_ref.read('META-INF/container.xml')
            container_root = ET.fromstring(container_xml)

            # 查找 OPF 路径
            opf_path = self._find_opf_path(container_root)
            if not opf_path:
                raise Exception('无法找到 OPF 文件路径')

            # 读取 OPF 文件
            opf_xml = zip_ref.read(opf_path)
            opf_root = ET.fromstring(opf_xml)

            # 获取 manifest 和 spine
            manifest_items, spine_items = self._parse_opf(opf_root)

            # 读取 HTML 内容
            html_items = self._read_html_items(zip_ref, opf_path, spine_items, manifest_items)

        if not html_items:
            raise Exception('无法从 EPUB 文件中提取任何内容')

        logger.info(f'[提取][EPUB] 手动解析成功，找到 {len(html_items)} 个HTML项目')
        return self._extract_from_manual_items(html_items, interrupt)

    def _find_opf_path(self, container_root) -> Optional[str]:
        """查找 OPF 文件路径"""
        # 尝试带命名空间
        for rootfile in container_root.findall('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile'):
            opf_path = rootfile.get('full-path')
            if opf_path:
                return opf_path

        # 尝试不带命名空间
        for rootfile in container_root.findall('.//rootfile'):
            opf_path = rootfile.get('full-path')
            if opf_path:
                return opf_path

        return None

    def _parse_opf(self, opf_root):
        """解析 OPF 文件，获取 manifest 和 spine"""
        namespaces = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }

        # 获取 manifest
        manifest_items = {}
        manifest_elem = opf_root.find('opf:manifest', namespaces)
        if manifest_elem is None:
            manifest_elem = opf_root.find('manifest')
            namespaces = {}

        if manifest_elem is not None:
            items = manifest_elem.findall('opf:item', namespaces) if 'opf' in namespaces else manifest_elem.findall('item')
            for item in items:
                item_id = item.get('id')
                manifest_items[item_id] = {
                    'href': item.get('href'),
                    'media_type': item.get('media-type')
                }

        # 获取 spine
        spine_items = []
        spine_elem = opf_root.find('opf:spine', namespaces) if 'opf' in namespaces else opf_root.find('spine')
        if spine_elem is not None:
            itemrefs = spine_elem.findall('opf:itemref', namespaces) if 'opf' in namespaces else spine_elem.findall('itemref')
            for itemref in itemrefs:
                item_id = itemref.get('idref')
                if item_id in manifest_items:
                    spine_items.append(manifest_items[item_id])

        return manifest_items, spine_items

    def _read_html_items(self, zip_ref, opf_path, spine_items, manifest_items):
        """读取 HTML 项内容"""
        import os
        opf_dir = os.path.dirname(opf_path) if os.path.dirname(opf_path) else ''

        html_items = []
        for item_info in spine_items:
            if item_info['media_type'] in FileFormats.EPUB_MIME_TYPES:
                item_path = os.path.join(opf_dir, item_info['href']).replace('\\', '/')
                try:
                    content = zip_ref.read(item_path)
                    item = epub.EpubHtml(
                        uid=item_info['href'],
                        file_name=item_path,
                        media_type=item_info['media_type']
                    )
                    item.content = content
                    html_items.append(item)
                except Exception as e:
                    logger.error(f'[提取][EPUB] 无法读取文件 {item_path}: {e}')
                    # 添加错误占位符
                    error_item = epub.EpubHtml(
                        uid=item_info['href'],
                        file_name=item_path,
                        media_type=item_info['media_type']
                    )
                    error_item.content = f"[读取出错: {e}]".encode('utf-8')
                    html_items.append(error_item)

        return html_items

    def _extract_from_manual_items(self, html_items: List, interrupt: Optional[int]) -> List[str]:
        """从手动解析的 HTML 项中提取文本"""
        num = 0
        content = []
        blank_count = 0

        for item in html_items:
            num += 1
            if interrupt and num < interrupt:
                continue

            logger.debug(f'[提取][EPUB] 处理第 {num} 项')

            try:
                soup = BeautifulSoup(item.content, 'html.parser')
                for script in soup(["script", "style"]):
                    script.decompose()
                page_text = soup.get_text(separator='\n', strip=True)

                if self.is_blank_page(page_text):
                    blank_count += 1
                    logger.debug(f'[提取][EPUB] 第 {num} 项为空白页，已跳过')
                    continue

                content.append(page_text)
            except Exception as e:
                logger.error(f'[提取][EPUB] 处理第 {num} 项时出错: {e}')
                content.append(f"[处理出错: {e}]")

        logger.info(f'[提取][EPUB] 完成，有效内容: {len(content)} 项，过滤空白: {blank_count} 项')
        return content

