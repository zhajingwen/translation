"""
多线程PDF/EPUB/TXT文档翻译工具

功能特点：
1. 支持PDF、EPUB、TXT格式文档翻译
2. 多线程并行翻译，大幅提升翻译速度
3. 自动重试机制，提高翻译成功率
4. 进度跟踪和错误处理
5. 支持自定义线程数和重试参数

使用说明：
1. 设置环境变量 AKASHML_API_KEY
2. 修改 source_origin_book_name 为要翻译的文件名
3. 根据需要调整 TranslateConfig 参数：
   - max_workers: 线程数，建议3-10个（太多可能导致API限流）
   - max_retries: 重试次数，默认3次
   - retry_delay: 重试延迟，默认1秒
   - chunk_size: 文本切割阈值，默认8000字符
   - min_chunk_size: 最小切割长度，默认500字符
   - api_timeout: API超时时间，默认60秒

注意事项：
- akashml 最高支持10个并发，建议线程数不要超过10个
- 网络不稳定时建议增加重试次数和延迟时间
- 翻译大文件时建议先测试小文件确认配置合适
- 这个版本不生成PDF文件，只生成txt文件
"""

import os
import time
import re
import logging
from traceback import format_exc
from openai import OpenAI
from PyPDF2 import PdfReader
from fpdf import FPDF
from ebooklib import epub
from bs4 import BeautifulSoup
# import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# ================== 日志配置 ==================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Translator')

# 使用akashml API https://playground.akashml.com/
client = OpenAI(
    api_key=os.environ.get('AKASHML_API_KEY'),
    base_url="https://api.akashml.com/v1"
    )

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        # 添加中文字体
        try:
            self.add_font('kaiti', '', './kaiti.ttf')
        except Exception as e:
            logger.warning(f"字体加载失败: {e}")
            # 如果字体加载失败，使用默认字体
            try:
                self.add_font('kaiti', '', 'DejaVu')
            except:
                # 如果DejaVu也失败，使用系统默认字体
                pass

    def footer(self):
        self.set_y(-15)
        self.set_font('kaiti', '', 8)  # 设置中文字体
        self.cell(0, 10, f'第 {self.page_no()} 页', 0, new_x='LMARGIN', new_y='NEXT', align='C')  # 页脚

class TranslateConfig:
    """
    翻译配置类
    """
    def __init__(self, max_workers=5, max_retries=3, retry_delay=1,
                 chunk_size=8000, min_chunk_size=500, api_timeout=60):
        self.max_workers = max_workers      # 最大线程数
        self.max_retries = max_retries      # 最大重试次数
        self.retry_delay = retry_delay      # 重试延迟时间(秒)
        self.chunk_size = chunk_size        # 文本切割阈值（字符数）
        self.min_chunk_size = min_chunk_size  # 最小切割长度
        self.api_timeout = api_timeout      # API 超时时间(秒)


# 句子结束标点符号（中英文）
SENTENCE_END_PUNCTUATION = ('。', '！', '？', '…', '.', '!', '?')

class Translate:
    """
    翻译类

    DeepSeek：每100页大概2毛钱
    """
    def __init__(self, source_file, config=None):
        """
        source_file：需要翻译的书名
        config：翻译配置，如果为None则使用默认配置
        """
    
        if 'files/' in source_file:
            source_file = source_file.split('files/')[1]
            
        self.config = config or TranslateConfig()
        self.text_list = []
        directory = 'files/'
        if not os.path.exists(directory):
            os.mkdir(directory)
        # 需要翻译的文件
        self.file_path = directory + source_file
        # 翻译结果输出为txt文件
        self.output_txt = f"{directory}{source_file.split('.')[0]} translated.txt"
        # 翻译结果输出为PDF文件
        self.output_pdf = f"{directory}{source_file.split('.')[0]} translated.pdf"

    def extract_text_from_pdf(self, interupt=None):
        """
        抽取PDF文本并使用统一的切割策略
        interupt：上一次翻译异常导致退出的页码，None表示没有任何异常导致中途退出
        """
        reader = PdfReader(self.file_path)
        num = 0
        content = []
        for page in reader.pages:
            num += 1
            # 跳过前面已经翻译过的页面，从上一次翻译异常的页面重新开始
            if interupt:
                if num < interupt:
                    continue
            logger.debug(f'[PDF] 开始处理第 {num} 页')
            page_text = page.extract_text()
            page_text = page_text.strip()
            if not page_text:
                continue
            content.append(page_text)
        
        # 合并所有页面内容后统一切割
        full_content = '\n'.join(content)
        return self.split_full_content_to_pages(full_content)

    def is_blank_page(self, text):
        """
        判断页面是否为空白页
        更严格的空白页判断逻辑
        """
        if text is None:
            return True
        
        # 去除首尾空白
        text_clean = text.strip()
        
        # 1. 空字符串
        if len(text_clean) == 0:
            return True
        
        # 2. 检查是否只包含空白字符和控制字符
        # 统计可打印字符（非空白、非控制字符）的数量
        printable_chars = sum(1 for c in text_clean if c.isprintable() and not c.isspace())
        total_chars = len(text_clean)
        
        # 如果可打印字符数量很少，认为是空白页
        if total_chars > 0 and printable_chars / total_chars < 0.1:
            # 特别短的文本如果可打印字符少于2个，认为空白
            if printable_chars < 2:
                return True
        
        # 3. 检查是否只包含常见的HTML空白实体和特殊字符
        blank_chars_only = all(c in [' ', '\n', '\t', '\r', '\xa0', '\u2000', '\u2001', 
                                      '\u2002', '\u2003', '\u2004', '\u2005', '\u2006', 
                                      '\u2007', '\u2008', '\u2009', '\u200a', '\u202f', '\u205f'] 
                               for c in text_clean)
        if blank_chars_only:
            return True
        
        # 4. 如果是纯标点符号或特殊符号（没有实际内容）
        if len(text_clean) < 20 and all(not c.isalnum() for c in text_clean):
            return True
        
        return False
    
    def extract_text_from_epub(self, interupt=None):
        """
        解析epub文件
        抽取每一页的PDF提交给chatgpt翻译
        interupt：上一次翻译异常导致退出的页码，None表示没有任何异常导致中途退出
        """
        # 读取 EPUB 文件
        try:
            book = epub.read_epub(self.file_path, options={"ignore_ncx": True})
        except IndexError as e:
            # 处理某些 EPUB 文件缺少导航元素的问题
            logger.warning(f'使用标准方式读取 EPUB 失败: {e}')
            logger.info('尝试使用备用方式读取 EPUB...')
            try:
                # 尝试不忽略 NCX，或者使用其他选项
                book = epub.read_epub(self.file_path)
            except Exception as e2:
                logger.warning(f'备用方式也失败: {e2}')
                # 最后尝试：手动处理 EPUB 文件
                import zipfile
                import xml.etree.ElementTree as ET
                logger.info('尝试手动解析 EPUB 文件...')
                book = epub.EpubBook()
                with zipfile.ZipFile(self.file_path, 'r') as zip_ref:
                    # 读取 container.xml 找到 OPF 文件
                    container_xml = zip_ref.read('META-INF/container.xml')
                    container_root = ET.fromstring(container_xml)
                    # 查找 full-path 属性
                    opf_path = None
                    for rootfile in container_root.findall('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile'):
                        opf_path = rootfile.get('full-path')
                        break
                    if not opf_path:
                        # 如果没有命名空间，尝试直接查找
                        for rootfile in container_root.findall('.//rootfile'):
                            opf_path = rootfile.get('full-path')
                            break
                    
                    if not opf_path:
                        raise Exception('无法找到 OPF 文件路径')
                    
                    # 读取 OPF 文件
                    opf_xml = zip_ref.read(opf_path)
                    opf_root = ET.fromstring(opf_xml)
                    
                    # 定义命名空间
                    namespaces = {
                        'opf': 'http://www.idpf.org/2007/opf',
                        'dc': 'http://purl.org/dc/elements/1.1/'
                    }
                    
                    # 获取所有 manifest 项
                    manifest_items = {}
                    manifest_elem = opf_root.find('opf:manifest', namespaces)
                    if manifest_elem is None:
                        # 尝试不使用命名空间
                        manifest_elem = opf_root.find('manifest')
                        namespaces = {}
                    
                    if manifest_elem is not None:
                        for item in manifest_elem.findall('opf:item', namespaces) if 'opf' in namespaces else manifest_elem.findall('item'):
                            item_id = item.get('id')
                            manifest_items[item_id] = {
                                'href': item.get('href'),
                                'media_type': item.get('media-type')
                            }
                    
                    # 获取 spine 顺序
                    spine_items = []
                    spine_elem = opf_root.find('opf:spine', namespaces) if 'opf' in namespaces else opf_root.find('spine')
                    if spine_elem is not None:
                        for itemref in spine_elem.findall('opf:itemref', namespaces) if 'opf' in namespaces else spine_elem.findall('itemref'):
                            item_id = itemref.get('idref')
                            if item_id in manifest_items:
                                spine_items.append(manifest_items[item_id])
                    
                    # 创建临时 EpubBook 并添加项目
                    import os
                    opf_dir = os.path.dirname(opf_path) if os.path.dirname(opf_path) else ''
                    
                    html_items = []
                    for item_info in spine_items:
                        if item_info['media_type'] in ['application/xhtml+xml', 'application/xhtml', 'text/html', 'text/xhtml']:
                            item_path = os.path.join(opf_dir, item_info['href']).replace('\\', '/')
                            try:
                                content = zip_ref.read(item_path)
                                item = epub.EpubHtml(
                                    uid=item_info['href'],
                                    file_name=item_path,
                                    media_type=item_info['media_type']
                                )
                                item.content = content
                                book.add_item(item)
                                html_items.append(item)
                            except Exception as e3:
                                logger.error(f'无法读取文件 {item_path}: {e3}')
                    
                    # 如果手动解析也失败，抛出异常
                    if not html_items:
                        raise Exception('无法从 EPUB 文件中提取任何内容')
                    
                    # 使用手动解析的 html_items
                    logger.info(f'手动解析成功，找到 {len(html_items)} 个 HTML 项目')
                    # 继续使用下面的代码处理 html_items
                    num = 0
                    content = []
                    blank_count = 0
                    for item in html_items:
                        num += 1
                        if interupt and num < interupt:
                            continue
                        logger.debug(f'[EPUB] 开始处理第 {num} 项: {item.file_name}')
                        try:
                            soup = BeautifulSoup(item.content, 'html.parser')
                            for script in soup(["script", "style"]):
                                script.decompose()
                            page_text = soup.get_text(separator='\n', strip=True)
                            if self.is_blank_page(page_text):
                                blank_count += 1
                                logger.debug(f'[EPUB] 第 {num} 项为空白页，已跳过')
                                continue
                            content.append(page_text)
                        except Exception as e3:
                            logger.error(f'[EPUB] 处理第 {num} 项时出错: {e3}')
                            content.append(f"[处理出错: {e3}]")
                    logger.info(f'共提取 {len(content)} 项有效内容')
                    if blank_count > 0:
                        logger.info(f'共过滤 {blank_count} 个空白项')
                    return content
        
        # 先收集所有需要处理的 HTML/XHTML 内容
        html_items = []
        skipped_items = []
        
        for item in book.get_items():
            # 扩展支持的 MIME 类型
            supported_types = [
                'application/xhtml+xml',
                'application/xhtml', 
                'text/html',
                'text/xhtml',
                'application/html+xml',
                'text/xml',  # 有些 epub 使用 text/xml
            ]
            
            if item.media_type in supported_types:
                try:
                    html_items.append(item)
                except Exception as e:
                    logger.error(f'处理 HTML 项时出错: {e}')
                    skipped_items.append((item.get_name(), item.media_type))
            else:
                skipped_items.append((item.get_name(), item.media_type))
        
        # 打印跳过的项目信息
        if skipped_items:
            logger.debug(f'跳过了 {len(skipped_items)} 个非正文项目 (图片、样式表、字体等)')
            if len(skipped_items) <= 10:  # 如果跳过项目较少，显示详情
                for name, mime_type in skipped_items:
                    logger.debug(f'  - {name} ({mime_type})')
        
        num = 0
        # 提取内容
        content = []
        blank_count = 0  # 统计空白页数量
        for item in html_items:
            num += 1
            # 跳过前面已经翻译过的页面，从上一次翻译异常的页面重新开始
            if interupt:
                if num < interupt:
                    continue
            
            logger.debug(f'[EPUB] 开始处理第 {num} 项: {item.get_name()}')
            
            try:
                # 解析 HTML 内容
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                
                # 移除 script 和 style 标签
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # 提取文本，保留换行
                page_text = soup.get_text(separator='\n', strip=True)
                
                # 检查和过滤空白页
                if self.is_blank_page(page_text):
                    blank_count += 1
                    logger.debug(f'[EPUB] 第 {num} 项为空白页，已跳过')
                    continue  # 跳过空白页，不添加到内容列表
                
                # 添加有效内容
                content.append(page_text)
                    
            except Exception as e:
                logger.error(f'[EPUB] 处理第 {num} 项时出错: {e}, 项名称: {item.get_name()}')
                # 出错时添加占位符，而不是完全跳过
                content.append(f"[处理出错: {e}]")
        
        logger.info(f'共提取 {len(content)} 项有效内容')
        if blank_count > 0:
            logger.info(f'共过滤 {blank_count} 个空白项')
            
        # 重构分页标准
        content = '\n'.join(content)
        page_list = self.split_full_content_to_pages(content)
        return page_list

    def is_sentence_end(self, line):
        """判断一行是否以句子结束标点结尾"""
        line = line.rstrip()
        if not line:
            return False
        return line[-1] in SENTENCE_END_PUNCTUATION

    def split_long_line(self, line, chunk_size=None):
        """
        处理超长单行，按句子标点或固定长度切割
        
        参数：
        - line: 需要切割的单行文本
        - chunk_size: 切割阈值
        
        返回：
        - 切割后的行列表
        """
        chunk_size = chunk_size or self.config.chunk_size
        
        if len(line) <= chunk_size:
            return [line]
        
        result = []
        remaining = line
        
        while len(remaining) > chunk_size:
            # 在 chunk_size 范围内查找最后一个句子结束标点
            search_range = remaining[:chunk_size]
            cut_pos = -1
            
            # 从后向前查找句子结束标点
            for i in range(len(search_range) - 1, -1, -1):
                if search_range[i] in SENTENCE_END_PUNCTUATION:
                    cut_pos = i + 1  # 包含标点符号
                    break
            
            if cut_pos > 0:
                # 找到句子结束点，在此处切割
                result.append(remaining[:cut_pos])
                remaining = remaining[cut_pos:].lstrip()  # 去除切割后的前导空白
            else:
                # 未找到句子结束标点，查找其他断句点（逗号、分号等）
                secondary_punctuation = (',', '，', ';', '；', ':', '：', ' ')
                for i in range(len(search_range) - 1, -1, -1):
                    if search_range[i] in secondary_punctuation:
                        cut_pos = i + 1
                        break
                
                if cut_pos > 0:
                    result.append(remaining[:cut_pos])
                    remaining = remaining[cut_pos:].lstrip()
                else:
                    # 无任何断句点，强制按 chunk_size 切割
                    result.append(remaining[:chunk_size])
                    remaining = remaining[chunk_size:]
        
        # 添加剩余内容
        if remaining:
            result.append(remaining)
        
        return result

    def split_full_content_to_pages(self, content, chunk_size=None, min_chunk_size=None):
        """
        将全文内容按阈值切割成多页
        优先在句子结束标点处切割，保持语义完整性
        
        切割优先级：
        1. 优先在以句子结束标点（。！？…. ! ?）结尾的行处切割
        2. 如果找不到，退而求其次在任意行边界切割
        
        参数：
        - chunk_size: 最大切割阈值（字符数），超过此值会触发切割
        - min_chunk_size: 最小切割长度，块长度未达到此值时不会切割
        """
        chunk_size = chunk_size or self.config.chunk_size
        min_chunk_size = min_chunk_size or self.config.min_chunk_size
        
        if len(content) <= chunk_size:
            return [content]
        
        page_list = []
        rows = content.split('\n')
        
        # 预处理：对超长单行进行切割
        processed_rows = []
        for row in rows:
            if len(row) > chunk_size:
                # 超长行需要切割
                split_lines = self.split_long_line(row, chunk_size)
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
            if current_length + row_length > chunk_size and current_chunk_rows and current_length >= min_chunk_size:
                # 优先在最后一个句子结束点切割
                if last_sentence_end_index >= 0:
                    cut_point = last_sentence_end_index + 1
                    page_list.append('\n'.join(current_chunk_rows[:cut_point]))
                    # 保留未切割的行
                    current_chunk_rows = current_chunk_rows[cut_point:]
                    current_length = sum(len(r) + 1 for r in current_chunk_rows)
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
            # 如果最后一块太短，尝试合并到前一块
            last_chunk = '\n'.join(current_chunk_rows)
            if len(last_chunk) < min_chunk_size and page_list:
                # 合并到前一块
                page_list[-1] = page_list[-1] + '\n' + last_chunk
            else:
                page_list.append(last_chunk)
        
        return page_list

    def extract_text_from_txt(self):
        """
        解析txt文件
        抽取txt文件提交给chatgpt翻译
        使用配置的 chunk_size 进行文本切割
        """
        with open(self.file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        page_list = self.split_full_content_to_pages(content)
        return page_list

    def translate(self, text_origin):
        """
        向DeepSeek发起翻译请求
        """
        try:
            # 如果文本长度大于10，则截取前10个字符
            if len(text_origin) > 100:
                text_origin_head = text_origin[:100]
            else:
                text_origin_head = text_origin
            # 打印翻译文本的头部
            logger.debug(f'翻译文本: {text_origin_head}...')
            response = client.chat.completions.create(
                model="Qwen/Qwen3-30B-A3B",
                messages=[
                    {"role": "system", "content": "You are a translation assistant."},
                    {"role": "user", "content": f"将该文本翻译成中文: {text_origin}"}
                ],
                stream=False,
                timeout=self.config.api_timeout
            )
            return response.choices[0].message.content
        except:
            logger.error(f'翻译异常: {format_exc()}')
            return

    def save_text_to_file(self, text):
        """
        保存翻译后的内容为 txt
        """
        logger.info(f'保存翻译后的内容为 txt: {self.output_txt}')
        # 保存为txt
        with open(self.output_txt, 'w', encoding='utf-8')as f:
            f.write(text)
        logger.info(f'保存翻译后的内容完成')

    def extract_text(self):
        """
        抽取文本
        """
        if '.pdf' in self.file_path:
            return self.extract_text_from_pdf()
        elif '.epub' in self.file_path:
            return self.extract_text_from_epub()
        elif '.txt' in self.file_path:
            return self.extract_text_from_txt()
        else:
            logger.error(f'不支持的文件类型: {self.file_path}')
            return None
    
    def translate_page(self, page_data):
        """
        翻译单个 chunk 文本
        page_data: (page_index, page_content)
        """
        page_index, page_content = page_data
        total = getattr(self, 'total_chunks', '?')
        chunk_tag = f'[Chunk {page_index + 1}/{total}]'
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    logger.warning(f'{chunk_tag} 重试翻译 (第 {attempt + 1} 次尝试)')
                    time.sleep(self.config.retry_delay)  # 重试前等待
                else:
                    logger.debug(f'{chunk_tag} 开始翻译 ({len(page_content)} 字符)')
                
                chinese = self.translate(page_content)
                if chinese:
                    # 只打印翻译结果的前150字符
                    result_preview = chinese[:150] + '...' if len(chinese) > 150 else chinese
                    logger.debug(f'{chunk_tag} 翻译结果: {result_preview}')
                    logger.debug(f'{chunk_tag} 翻译完成')
                    return page_index, chinese
                else:
                    logger.warning(f'{chunk_tag} 翻译失败 (第 {attempt + 1} 次尝试)')
                    
            except Exception as e:
                logger.error(f'{chunk_tag} 翻译异常 (第 {attempt + 1} 次尝试): {e}')
        
        logger.error(f'{chunk_tag} 翻译最终失败，已重试 {self.config.max_retries} 次')
        return page_index, None

    def translate_text(self, page_list):
        """
        多线程翻译文本
        page_list: 页面内容列表
        """
        self.total_chunks = len(page_list)
        self.translate_start_time = time.time()
        logger.info(f'开始多线程翻译，共 {self.total_chunks} 个 chunk，使用 {self.config.max_workers} 个线程')
        
        # 准备页面数据 (索引, 内容)
        page_data_list = [(i, page) for i, page in enumerate(page_list)]
        
        # 初始化结果列表
        results = [None] * len(page_list)
        self.text_list = [None] * len(page_list)
        
        # 使用线程池进行翻译
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # 提交所有翻译任务
            future_to_page = {
                executor.submit(self.translate_page, page_data): page_data[0] 
                for page_data in page_data_list
            }
            
            # 收集结果
            completed_count = 0
            failed_pages = []
            
            for future in as_completed(future_to_page):
                page_index = future_to_page[future]
                try:
                    page_index, translated_text = future.result()
                    results[page_index] = translated_text
                    self.text_list[page_index] = translated_text
                    completed_count += 1
                    
                    if translated_text is None:
                        failed_pages.append(page_index + 1)
                    
                    # 改进进度显示：百分比、已用时间、预估剩余时间
                    total = len(page_list)
                    elapsed = time.time() - self.translate_start_time
                    percent = completed_count / total * 100
                    avg_time = elapsed / completed_count if completed_count > 0 else 0
                    eta = avg_time * (total - completed_count)
                    logger.info(f'进度: {percent:.1f}% ({completed_count}/{total}) | 已用: {elapsed:.0f}s | 预估剩余: {eta:.0f}s')
                    
                except Exception as e:
                    logger.error(f'[Chunk {page_index + 1}/{len(page_list)}] 处理异常: {e}')
                    failed_pages.append(page_index + 1)
                    completed_count += 1
        
        # 检查是否有失败的 chunk
        if failed_pages:
            logger.warning(f'以下 chunk 翻译失败: {failed_pages}')
            logger.info(f'成功翻译: {len(page_list) - len(failed_pages)} 个 chunk')
            logger.warning(f'失败 chunk: {len(failed_pages)} 个')
            
            # # 询问是否继续处理成功的页面
            # user_input = input('是否继续处理成功翻译的页面？(y/n): ').lower().strip()
            # if user_input == 'n':
            #     raise Exception(f'有 {len(failed_pages)} 页翻译失败: {failed_pages}')
            # else:
            #     print('继续处理成功翻译的页面...')
        
        # 按顺序组合翻译结果
        text = ""
        for translated_text in self.text_list:
            if translated_text:
                text += f'{translated_text}\n'
        
        logger.info(f'全部翻译完成，共 {len(page_list)} 个 chunk')
        return text

    def run(self):
        """
        启动入口
        """
        logger.info(f'开始翻译任务: {self.file_path}，使用 {self.config.max_workers} 个线程')
        start_time = time.time()
        
        page_list = self.extract_text()
        if not page_list:
            logger.error('抽取文本失败')
            return False
        
        translated_text = self.translate_text(page_list)
        if translated_text:
            self.save_text_to_file(translated_text)
            end_time = time.time()
            logger.info(f'翻译任务完成，总耗时: {end_time - start_time:.2f} 秒')
            return True
        else:
            logger.error('翻译失败')
            return False

if __name__ == '__main__':
    source_origin_book_name = "files/070 - Hey Tech, Come to Healthcare.txt"
    
    # 可以根据API限制和网络情况调整参数
    config = TranslateConfig(
        max_workers=10,       # 最大线程数，建议3-10个
        max_retries=5,        # 最大重试次数
        retry_delay=10,       # 重试延迟时间(秒)
        chunk_size=8000,      # 文本切割阈值（字符数），默认8000
        min_chunk_size=500,   # 最小切割长度
        api_timeout=60        # API 超时时间(秒)
    )
    
    # 启动翻译任务
    Translate(source_origin_book_name, config).run()