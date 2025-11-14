from openai import OpenAI
from PyPDF2 import PdfReader
from fpdf import FPDF
from ebooklib import epub
from bs4 import BeautifulSoup

# openai API的使用方式：https://platform.openai.com/docs/quickstart?language-preference=python
client = OpenAI()
"""
每本书(833页的英文文档)翻译成本大概是0.4美元，合人民币3块钱；相当划算了！！！
"""

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        # 添加中文字体
        self.add_font('kaiti', '', './kaiti.ttf', uni=True)

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
        pdf.set_left_margin(10)
        pdf.set_right_margin(10)
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font('kaiti', '', 12)

        for page in pages_list:
            # 将优化后的文本添加到PDF
            pdf.multi_cell(0, 10, page)
        # 保存PDF文件
        pdf.output(self.pdf_file)
        print(f"TXT内容已成功保存到 {self.pdf_file}")


class Translate:
    """
    翻译类

    GPT-4o-mini：输入费用为每百万 tokens $0.15，输出费用为每百万 tokens $0.60
    **批处理打五折**
    """
    def __init__(self, source_origin_book_name):
        """
        source_origin_book_name：需要翻译的书名
        """
        self.file_path = source_origin_book_name
        self.output_txt = "output_translated.txt"
        self.output_pdf = "output_translated.pdf"
        self.text_list = []

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
        向OpenAI发起翻译请求
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a translation assistant."},
                    {"role": "user", "content": f"将该文本翻译成中文: {text_origin}"}
                ]
            )
            return response.choices[0].message.content
        except:
            return

    def save_to_pdf(self, text):
        """
        保存翻译后的内容为 txt, PDF
        """
        # 保存为txt
        with open(self.output_txt, 'w', encoding='utf-8')as f:
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
    source_origin_book_name = "Games people play.pdf"
    Translate(source_origin_book_name).run()