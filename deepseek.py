"""
多线程PDF/EPUB/TXT文档翻译工具

功能特点：
1. 支持PDF、EPUB、TXT格式文档翻译
2. 多线程并行翻译，大幅提升翻译速度
3. 自动重试机制，提高翻译成功率
4. 进度跟踪和错误处理
5. 支持自定义线程数和重试参数

使用说明：
1. 设置环境变量 DEEPSEEK_API_KEY
2. 修改 source_origin_book_name 为要翻译的文件名
3. 根据需要调整 TranslateConfig 参数：
   - max_workers: 线程数，建议3-10个（太多可能导致API限流）
   - max_retries: 重试次数，默认3次
   - retry_delay: 重试延迟，默认1秒

注意事项：
- DeepSeek API有速率限制，建议线程数不要超过10个
- 网络不稳定时建议增加重试次数和延迟时间
- 翻译大文件时建议先测试小文件确认配置合适
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

# 使用deepseek API https://platform.deepseek.com/usage
# 每100页大概2毛钱
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
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

class Topdf:
    def __init__(self, pdf_path, txt_file_path):
        # PDF文件路径
        self.pdf_file = pdf_path
        # 输出的TXT文件路径
        self.txt_file = txt_file_path

    def to_pdf_from_text_file(self):
        # 创建PDF对象
        pdf = PDF()
        pdf.set_left_margin(15)
        pdf.set_right_margin(15)
        pdf.add_page()

        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.set_font('kaiti', '', 11)

        # 读取TXT文件并优化文本内容
        with open(self.txt_file, 'r', encoding='utf-8') as file:
            text = file.read()

        # 清理和优化文本
        clean_text = self.clean_text_for_pdf(text)
        
        # 将优化后的文本添加到PDF
        pdf.multi_cell(0, 8, clean_text)

        # 保存PDF文件
        pdf.output(self.pdf_file)
        print(f"TXT内容已成功保存到 {self.pdf_file}")

    def to_pdf(self, pages_list):
        """
        pages_list: 文本列表
        """
        # 创建PDF对象
        pdf = PDF()
        # 设置合适的页面边距，确保有足够的空间
        pdf.set_left_margin(15)
        pdf.set_right_margin(15)
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.set_font('kaiti', '', 11)

        for page in pages_list:
            if not page or not page.strip():  # 跳过空页面
                continue
                
            try:
                # 清理文本，移除可能导致问题的字符
                clean_text = self.clean_text_for_pdf(page)
                if clean_text.strip():  # 只处理非空文本
                    # 将优化后的文本添加到PDF，使用更小的行高
                    pdf.multi_cell(0, 8, clean_text)
                    # 添加段落间距
                    pdf.ln(2)
            except Exception as e:
                print(f"处理页面时出错: {e}")
                # 如果单页出错，尝试用更安全的方式处理
                try:
                    # 分段处理长文本
                    text_chunks = self.split_text_safely(page)
                    for chunk in text_chunks:
                        if chunk.strip():
                            pdf.multi_cell(0, 8, chunk)
                            pdf.ln(1)
                except Exception as e2:
                    print(f"分段处理也失败: {e2}")
                    continue
        
        # 保存PDF文件
        pdf.output(self.pdf_file)
        print(f"TXT内容已成功保存到 {self.pdf_file}")
    
    def clean_text_for_pdf(self, text):
        """清理文本，移除可能导致PDF渲染问题的字符"""
        if not text:
            return ""
        
        # 移除或替换可能导致问题的字符
        import re
        # 移除控制字符和特殊字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        # 移除或替换可能导致问题的Unicode字符
        text = re.sub(r'[\u200b-\u200d\u2060\ufeff]', '', text)  # 零宽字符
        
        # 限制文本长度，避免过长的行
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # 移除行首行尾空白
            line = line.strip()
            if not line:
                cleaned_lines.append('')
                continue
                
            if len(line) > 150:  # 限制单行长度，减少到150字符
                # 在合适的位置断行
                while len(line) > 150:
                    break_pos = line.rfind(' ', 0, 150)
                    if break_pos == -1:
                        # 如果没有空格，强制在150字符处断行
                        break_pos = 150
                    cleaned_lines.append(line[:break_pos])
                    line = line[break_pos:].lstrip()
                if line:
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def split_text_safely(self, text):
        """安全地分割文本"""
        if not text:
            return []
        
        # 按段落分割
        paragraphs = text.split('\n\n')
        chunks = []
        for paragraph in paragraphs:
            if len(paragraph) > 1000:  # 如果段落太长，进一步分割
                sentences = paragraph.split('. ')
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk + sentence) > 1000:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
                    else:
                        current_chunk += ". " + sentence if current_chunk else sentence
                if current_chunk:
                    chunks.append(current_chunk)
            else:
                chunks.append(paragraph)
        
        return chunks

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
        book = epub.read_epub(self.file_path, options={"ignore_ncx": True})
        
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
        return content

    def extract_text_from_txt(self):
        """
        解析txt文件
        抽取txt文件提交给chatgpt翻译
        每一段文本呢限制在2000字以内
        """
        with open(self.file_path, 'r', encoding='utf-8') as file:
            content = file.read()
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

    def translate(self, text_origin):
        """
        向DeepSeek发起翻译请求
        """
        try:
            print(f'翻译文本: {text_origin}')
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a translation assistant."},
                    {"role": "user", "content": f"将该文本翻译成中文: {text_origin}"}
                ],
                stream=False
            )
            return response.choices[0].message.content
        except:
            print(f'翻译异常: {format_exc()}')
            return

    def save_text_to_file(self, text):
        """
        保存翻译后的内容为 txt, PDF
        """
        print(f'保存翻译后的内容为 txt, PDF')
        # 保存为txt
        with open(self.output_txt, 'w')as f:
            f.write(text)
        print(f'保存翻译后的内容为 txt 完成')
        # 保存为pdf
        Topdf(self.output_pdf, self.output_txt).to_pdf(self.text_list)
        print(f'保存翻译后的内容为 PDF 完成')

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
        # print(f'翻译单页文本: {page_data}')
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
            if user_input != 'y':
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
            return
        
        translated_text = self.translate_text(page_list)
        if translated_text:
            self.save_text_to_file(translated_text)
            end_time = time.time()
            print(f'翻译任务完成，总耗时: {end_time - start_time:.2f} 秒')
        else:
            print('翻译失败')

if __name__ == '__main__':
    # 需要翻译的书名
    # source_origin_book_name = "Modernization, Cultural Change, and Democracy The Human Development Sequence.pdf"
    # source_origin_book_name = "files/017 - Jeffrey Wasserstrom： China, Xi Jinping, Trade War, Taiwan, Hong Kong, Mao ｜ Lex Fridman Podcast #466.txt"
    source_origin_book_name = "files/Becoming a Supple Leopard The Ultimate Guide to Resolving Pain, Preventing Injury, and Optimizing Athletic Performance (Kelly Starrett) (Z-Library).pdf"
    
    if 'files/' in source_origin_book_name:
        source_origin_book_name = source_origin_book_name.split('files/')[1]
    # 创建翻译配置
    # 可以根据API限制和网络情况调整参数
    config = TranslateConfig(
        max_workers=10,      # 最大线程数，建议3-10个
        max_retries=10,      # 最大重试次数
        retry_delay=10       # 重试延迟时间(秒)
    )
    
    # 启动翻译任务
    Translate(source_origin_book_name, config).run()