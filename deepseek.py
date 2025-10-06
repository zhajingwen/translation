import os
from openai import OpenAI
from PyPDF2 import PdfReader
from fpdf import FPDF
from ebooklib import epub
from bs4 import BeautifulSoup

# 使用deepseek API https://platform.deepseek.com/usage
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
    )

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        # 添加中文字体
        try:
            self.add_font('kaiti', '', './kaiti.ttf', uni=True)
        except Exception as e:
            print(f"字体加载失败: {e}")
            # 如果字体加载失败，使用默认字体
            self.add_font('kaiti', '', 'DejaVu', uni=True)

    def footer(self):
        self.set_y(-15)
        self.set_font('kaiti', '', 8)  # 设置中文字体
        self.cell(0, 10, f'第 {self.page_no()} 页', 0, 0, 'C')  # 页脚

class Topdf:
    def __init__(self, pdf_path, txt_file_path):
        # PDF文件路径
        self.pdf_file = pdf_path
        # 输出的TXT文件路径
        self.txt_file = txt_file_path

    def to_pdf_from_text_file(self):
        # 创建PDF对象
        pdf = PDF()
        pdf.set_left_margin(10)
        pdf.set_right_margin(10)
        pdf.add_page()

        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font('kaiti', '', 12)

        # 读取TXT文件并优化文本内容
        with open(self.txt_file, 'r', encoding='utf-8') as file:
            text = file.read()

        # 将优化后的文本添加到PDF
        pdf.multi_cell(0, 10, text)

        # 保存PDF文件
        pdf.output(self.pdf_file)
        print(f"TXT内容已成功保存到 {self.pdf_file}")

    def to_pdf(self, pages_list):
        """
        pages_list: 文本列表
        """
        # 创建PDF对象
        pdf = PDF()
        # 增加页面边距，确保有足够的空间
        pdf.set_left_margin(20)
        pdf.set_right_margin(20)
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.set_font('kaiti', '', 12)

        for page in pages_list:
            try:
                # 清理文本，移除可能导致问题的字符
                clean_text = self.clean_text_for_pdf(page)
                if clean_text.strip():  # 只处理非空文本
                    # 将优化后的文本添加到PDF
                    pdf.multi_cell(0, 10, clean_text)
            except Exception as e:
                print(f"处理页面时出错: {e}")
                # 如果单页出错，尝试用更安全的方式处理
                try:
                    # 分段处理长文本
                    text_chunks = self.split_text_safely(page)
                    for chunk in text_chunks:
                        if chunk.strip():
                            pdf.multi_cell(0, 10, chunk)
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
        # 移除控制字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        # 限制文本长度，避免过长的行
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if len(line) > 200:  # 限制单行长度
                # 在合适的位置断行
                while len(line) > 200:
                    break_pos = line.rfind(' ', 0, 200)
                    if break_pos == -1:
                        break_pos = 200
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


class Translate:
    """
    翻译类

    GPT-4o-mini：输入费用为每百万 tokens $0.15，输出费用为每百万 tokens $0.60
    **批处理打五折**
    """
    def __init__(self, source_file):
        """
        source_file：需要翻译的书名
        """
        self.text_list = []
        directory = 'files/'
        if not os.path.exists(directory):
            os.mkdir(directory)
        # 需要翻译的文件
        self.file_path = directory + source_file
        # 翻译结果输出为txt文件
        self.output_txt = f"{directory}{source_file.split('.')[0]}.txt"
        # 翻译结果输出为PDF文件
        self.output_pdf = f"{directory}{source_file.split('.')[0]}.pdf"

    def extract_text_from_pdf_translate(self, interupt=None):
        """
        抽取每一页的PDF提交给chatgpt翻译
        interupt：上一次翻译异常导致退出的页码，None表示没有任何异常导致中途退出
        """
        reader = PdfReader(self.file_path)
        text = ""
        num = 0
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
            chinese = self.translate(page_text)
            if chinese:
                text += f'{chinese}\n'
                self.text_list.append(chinese)
            else:
                print(f'第 {num} 页失败')
                break

        print(f'全部翻译完成\n\n{text}')
        return text

    def extract_text_from_epub_translate(self, interupt=None):
        """
        解析epub文件
        抽取每一页的PDF提交给chatgpt翻译
        interupt：上一次翻译异常导致退出的页码，None表示没有任何异常导致中途退出
        """
        # 读取 EPUB 文件
        book = epub.read_epub(self.file_path, options={"ignore_ncx": True})
        text = ""
        num = 0
        # 提取内容
        # content = []
        for item in book.get_items():
            num += 1
            # 跳过前面已经翻译过的页面，从上一次翻译异常的页面重新开始
            if interupt:
                if num < interupt:
                    continue
            print(f'开始处理第 {num} 页')
            # 检查 item 是否是正文类型（基于 MIME 类型）
            if item.media_type == 'application/xhtml+xml':  # 处理 xhtml 内容
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                page_text = soup.get_text()
                page_text = page_text.strip()
                if not page_text:
                    continue
                chinese = self.translate(page_text)
                if chinese:
                    text += f'{chinese}\n'
                    self.text_list.append(chinese)
                else:
                    print(f'第 {num} 页失败')
                    break
        print(f'全部翻译完成\n\n{text}')
        return text

    def translate(self, text_origin):
        """
        向DeepSeek发起翻译请求
        """
        try:
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
            return

    def save_to_pdf(self, text):
        """
        保存翻译后的内容为 txt, PDF
        """
        # 保存为txt
        with open(self.output_txt, 'w')as f:
            f.write(text)
        # 保存为pdf
        Topdf(self.output_pdf, self.output_txt).to_pdf(self.text_list)

    def run(self):
        """
        启动入口
        """
        if 'pdf' in self.file_path:
            text = self.extract_text_from_pdf_translate()
        elif 'epub' in self.file_path:
            text = self.extract_text_from_epub_translate()
        else:
            print('不支持的文件类型')
            text = None
        if text:
            self.save_to_pdf(text)

if __name__ == '__main__':
    # 需要翻译的书名
    source_origin_book_name = "The Big Secret for the Small Investor A New Route to Long-Term Investment Success (Joel Greenblatt) (Z-Library).epub"
    Translate(source_origin_book_name).run()