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

注意事项：
- 网络不稳定时建议增加重试次数和延迟时间
- 翻译大文件时建议先测试小文件确认配置合适
- 这个版本不生成PDF文件，只生成txt文件
"""

import os
import time
import re
from traceback import format_exc
from openai import OpenAI
from PyPDF2 import PdfReader
from fpdf import FPDF
from ebooklib import epub
from bs4 import BeautifulSoup
# import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

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
            print(f"字体加载失败: {e}")
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
    def __init__(self, max_workers=5, max_retries=3, retry_delay=1):
        self.max_workers = max_workers  # 最大线程数
        self.max_retries = max_retries  # 最大重试次数
        self.retry_delay = retry_delay  # 重试延迟时间(秒)

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
        抽取每一页的PDF提交给chatgpt翻译
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
            print(f'开始处理第 {num} 页')
            page_text = page.extract_text()
            page_text = page_text.strip()
            if not page_text:
                continue
            content.append(page_text)
        return content

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
            print(f'使用标准方式读取 EPUB 失败: {e}')
            print('尝试使用备用方式读取 EPUB...')
            try:
                # 尝试不忽略 NCX，或者使用其他选项
                book = epub.read_epub(self.file_path)
            except Exception as e2:
                print(f'备用方式也失败: {e2}')
                # 最后尝试：手动处理 EPUB 文件
                import zipfile
                import xml.etree.ElementTree as ET
                print('尝试手动解析 EPUB 文件...')
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
                                print(f'无法读取文件 {item_path}: {e3}')
                    
                    # 如果手动解析也失败，抛出异常
                    if not html_items:
                        raise Exception('无法从 EPUB 文件中提取任何内容')
                    
                    # 使用手动解析的 html_items
                    print(f'手动解析成功，找到 {len(html_items)} 个 HTML 项目')
                    # 继续使用下面的代码处理 html_items
                    num = 0
                    content = []
                    blank_count = 0
                    for item in html_items:
                        num += 1
                        if interupt and num < interupt:
                            continue
                        print(f'开始处理第 {num} 页: {item.file_name}')
                        try:
                            soup = BeautifulSoup(item.content, 'html.parser')
                            for script in soup(["script", "style"]):
                                script.decompose()
                            page_text = soup.get_text(separator='\n', strip=True)
                            if self.is_blank_page(page_text):
                                blank_count += 1
                                print(f'第 {num} 页为空白页，已跳过')
                                continue
                            content.append(page_text)
                        except Exception as e3:
                            print(f'处理第 {num} 页时出错: {e3}')
                            content.append(f"[处理出错: {e3}]")
                    print(f'共提取 {len(content)} 页有效内容')
                    if blank_count > 0:
                        print(f'共过滤 {blank_count} 个空白页')
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
                    print(f'处理 HTML 项时出错: {e}')
                    skipped_items.append((item.get_name(), item.media_type))
            else:
                skipped_items.append((item.get_name(), item.media_type))
        
        # 打印跳过的项目信息
        if skipped_items:
            print(f'跳过了 {len(skipped_items)} 个非正文项目 (图片、样式表、字体等)')
            if len(skipped_items) <= 10:  # 如果跳过项目较少，显示详情
                for name, mime_type in skipped_items:
                    print(f'  - {name} ({mime_type})')
        
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
            
            print(f'开始处理第 {num} 页: {item.get_name()}')
            
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
                    print(f'第 {num} 页为空白页，已跳过')
                    continue  # 跳过空白页，不添加到内容列表
                
                # 添加有效内容
                content.append(page_text)
                    
            except Exception as e:
                print(f'处理第 {num} 页时出错: {e}')
                print(f'  页面名称: {item.get_name()}')
                # 出错时添加占位符，而不是完全跳过
                content.append(f"[处理出错: {e}]")
        
        print(f'共提取 {len(content)} 页有效内容')
        if blank_count > 0:
            print(f'共过滤 {blank_count} 个空白页')
            
        # 重构分页标准
        content = '\n'.join(content)
        page_list = self.split_full_content_to_pages(content)
        return page_list

    def split_full_content_to_pages(self, content):
        """
        将全文内容切割成每2000字一页
        """
        if len(content) > 2000:
            # 切割点
            split_points = []
            page_list = []
            # 按行进行切割
            rows = content.split('\n')
            for index, row in enumerate(rows):
                if index == 0:
                    continue
                # 第一次切割
                if not split_points:
                    page_content = rows[:index+1]
                    page_content = '\n'.join(page_content)
                    if len(page_content) > 2000:
                        split_points.append(index)
                        # 第一页加入列表
                        page_list.append('\n'.join(rows[:index]))
                # 非第一次切割
                else:
                    start_point = split_points[-1]
                    page_content = rows[start_point:index+1]
                    page_content = '\n'.join(page_content)
                    if len(page_content) > 2000:
                        split_points.append(index)
                        page_list.append('\n'.join(rows[start_point:index]))
            the_last_page = '\n'.join(rows[split_points[-1]:])
            page_list.append(the_last_page)
            return page_list
        else:
            return [content]

    def extract_text_from_txt(self):
        """
        解析txt文件
        抽取txt文件提交给chatgpt翻译
        每一段文本呢限制在2000字以内
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
            print(f'翻译文本: {text_origin_head} ...')
            response = client.chat.completions.create(
                model="Qwen/Qwen3-30B-A3B",
                messages=[
                    {"role": "system", "content": "You are a translation assistant."},
                    {"role": "user", "content": f"将该文本翻译成中文: {text_origin}"}
                ],
                stream=False,
                timeout=30
            )
            return response.choices[0].message.content
        except:
            print(f'翻译异常: {format_exc()}')
            return

    def save_text_to_file(self, text):
        """
        保存翻译后的内容为 txt
        """
        print(f'保存翻译后的内容为txt')
        # 保存为txt
        with open(self.output_txt, 'w', encoding='utf-8')as f:
            f.write(text)
        print(f'保存翻译后的内容为txt 完成')

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
            print('不支持的文件类型')
            return None
    
    def translate_page(self, page_data):
        """
        翻译单页文本
        page_data: (page_index, page_content)
        """
        page_index, page_content = page_data
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    print(f'重试翻译第 {page_index + 1} 页 (第 {attempt + 1} 次尝试)')
                    time.sleep(self.config.retry_delay)  # 重试前等待
                else:
                    print(f'开始翻译第 {page_index + 1} 页')
                
                chinese = self.translate(page_content)
                if chinese:
                    print(f'翻译结果: {chinese}')
                    print(f'第 {page_index + 1} 页翻译完成')
                    return page_index, chinese
                else:
                    print(f'第 {page_index + 1} 页翻译失败 (第 {attempt + 1} 次尝试)')
                    
            except Exception as e:
                print(f'第 {page_index + 1} 页翻译异常 (第 {attempt + 1} 次尝试): {e}')
        
        print(f'第 {page_index + 1} 页翻译最终失败，已重试 {self.config.max_retries} 次')
        return page_index, None

    def translate_text(self, page_list):
        """
        多线程翻译文本
        page_list: 页面内容列表
        """
        print(f'开始多线程翻译，共 {len(page_list)} 页，使用 {self.config.max_workers} 个线程')
        
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
                    
                    print(f'进度: {completed_count}/{len(page_list)} 页完成')
                    
                except Exception as e:
                    print(f'第 {page_index + 1} 页处理异常: {e}')
                    failed_pages.append(page_index + 1)
                    completed_count += 1
        
        # 检查是否有失败的页面
        if failed_pages:
            print(f'以下页面翻译失败: {failed_pages}')
            print(f'成功翻译: {len(page_list) - len(failed_pages)} 页')
            print(f'失败页面: {len(failed_pages)} 页')
            
            # 询问是否继续处理成功的页面
            user_input = input('是否继续处理成功翻译的页面？(y/n): ').lower().strip()
            if user_input == 'n':
                raise Exception(f'有 {len(failed_pages)} 页翻译失败: {failed_pages}')
            else:
                print('继续处理成功翻译的页面...')
        
        # 按顺序组合翻译结果
        text = ""
        for translated_text in self.text_list:
            if translated_text:
                text += f'{translated_text}\n'
        
        print(f'全部翻译完成，共 {len(page_list)} 页')
        return text

    def run(self):
        """
        启动入口
        """
        print(f'开始翻译任务，使用 {self.config.max_workers} 个线程')
        start_time = time.time()
        
        page_list = self.extract_text()
        if not page_list:
            print('抽取文本失败')
            return False
        
        translated_text = self.translate_text(page_list)
        if translated_text:
            self.save_text_to_file(translated_text)
            end_time = time.time()
            print(f'翻译任务完成，总耗时: {end_time - start_time:.2f} 秒')
            return True
        else:
            print('翻译失败')
            return False

if __name__ == '__main__':
    source_origin_book_name = "files/070 - Hey Tech, Come to Healthcare.txt"
    
    # 可以根据API限制和网络情况调整参数
    config = TranslateConfig(
        max_workers=10,      # 最大线程数，建议3-10个
        max_retries=5,      # 最大重试次数
        retry_delay=10       # 重试延迟时间(秒)
    )
    
    # 启动翻译任务
    Translate(source_origin_book_name, config).run()