import time
import os
import requests
import json
from fpdf import FPDF
from ebooklib import epub
from bs4 import BeautifulSoup
from openai import OpenAI
from retry import retry
from PyPDF2 import PdfReader, PdfWriter

import warnings
warnings.filterwarnings("ignore", message="cmap value too big/small")

"""
批处理模式
每本书(833页的英文文档)翻译成本大概是0.2美元，合人民币1.4元；相当划算了！！！
"""
client = OpenAI()

class PDF(FPDF):
    """
    PDF生成的基类
    """
    def __init__(self):
        super().__init__()
        # 添加中文字体
        self.add_font('kaiti', '', './kaiti.ttf', uni=True)

    def footer(self):
        self.set_y(-15)
        self.set_font('kaiti', '', 8)  # 设置中文字体
        self.cell(0, 10, f'第 {self.page_no()} 页', 0, 0, 'C')  # 页脚

class Topdf:
    """
    生成PDF文件
    """
    def __init__(self, pdf_path, txt_file_path):
        """
        pdf_path：输出的PDF文件名
        txt_file_path：需要被转为PDF的txt文件名
        """
        # PDF文件路径
        self.pdf_file = pdf_path
        # 输出的TXT文件路径
        self.txt_file = txt_file_path

    def clean_text(self, text):
        return ''.join(c for c in text if ord(c) <= 0xFFFF)  # 过滤掉超出 BMP 平面的字符

    def to_pdf_from_text_file(self):
        """
        从text文件生成PDF文件
        """
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
        从翻译结果的列表（每一页的文本为一个元素）生成PDF文件
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
            page = self.clean_text(page)
            # 将优化后的文本添加到PDF
            pdf.multi_cell(0, 10, page)
        # 保存PDF文件
        pdf.output(self.pdf_file)
        print(f"翻译结果内容已成功保存到 {self.pdf_file}")


class Translate:
    """
    GPT-4o-mini：输入费用为每百万 tokens $0.15，输出费用为每百万 tokens $0.60
    批处理打五折
    批处理文档：https://platform.openai.com/docs/api-reference/batch/create
    """
    def __init__(self, source_file):
        """
        source_file: 需要翻译的文件名
        """
        directory = 'files/'
        if not os.path.exists(directory):
            os.mkdir(directory)
        # 需要翻译的文件
        self.file_path = directory + source_file
        # 整本书的翻译请求文件
        self.batch_file = f'{directory}batch_input.jsonl'
        # 翻译结果的json文件
        self.batch_file_job_done = f'{directory}batch_output.jsonl'
        # 翻译结果输出为txt文件
        self.output_txt = f"{directory}{source_file.split('.')[0]}.txt"
        # 翻译结果输出为PDF文件
        self.output_pdf = f"{directory}{source_file.split('.')[0]}.pdf"
        # 通过环境变量获取api key
        OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
        self.api_key = OPENAI_API_KEY

    def extract_text_from_pdf_translate(self):
        """
        从PDF中抽取文本，并且构建请求体，用\n合并所有请求体
        """
        reader = PdfReader(self.file_path)
        request_json_all_lines = ""
        num = 0
        for page in reader.pages:
            page_text = page.extract_text()
            page_text = page_text.strip()
            if not page_text:
                continue
            num += 1
            # 构建每一行的请求体
            line_request_json = self.build_batch_line(num, page_text) + '\n'
            request_json_all_lines += line_request_json
        return request_json_all_lines

    def extract_text_from_epub_translate(self):
        """
        从epub中抽取文本，并且构建请求体，用\n合并所有请求体
        """
        # 读取 EPUB 文件
        book = epub.read_epub(self.file_path, options={"ignore_ncx": True})
        request_json_all_lines = ""
        num = 0
        for item in book.get_items():
            # 检查 item 是否是正文类型（基于 MIME 类型）
            if item.media_type == 'application/xhtml+xml':  # 处理 xhtml 内容
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                page_text = soup.get_text()
                page_text = page_text.strip()
                if not page_text:
                    continue
                num += 1
                # 构建每一行的请求体
                line_request_json = self.build_batch_line(num, page_text) + '\n'
                request_json_all_lines += line_request_json
        return request_json_all_lines

    def build_batch(self):
        """
        将整本书内容抽取出来，构建全部的请求体，并且生成请求体集合的文件
        """
        if '.pdf' in self.file_path:
            request_json_all_lines = self.extract_text_from_pdf_translate()
        elif '.epub' in self.file_path:
            request_json_all_lines = self.extract_text_from_epub_translate()
        else:
            print(f'文件类型有误')
            return
        if not request_json_all_lines.strip():
            print('无法从文档中抽取文本！')
            return
        # 生成批处理的请求体文件
        with open(self.batch_file, 'w')as f:
            f.write(request_json_all_lines)

    def build_batch_line(self, id, text):
        """
        构建列表中的一个请求对象
        """
        data = {
            "custom_id": str(id),
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a translation assistant."},
                    {"role": "user", "content": f"将该文本翻译成中文: {text}"}
                ]
            }
        }
        line = json.dumps(data)
        return line

    def upload_batchfile(self):
        """
        上传批处理文件
        响应体数据结构：
        {
          "object": "file",
          "id": "file-VnK61ScVxBsuZfGCRWn7Lc",
          "purpose": "fine-tune",
          "filename": "batch_input.json",
          "bytes": 5922839,
          "created_at": 1735787655,
          "status": "processed",
          "status_details": null
        }
        """
        batch_input_file = client.files.create(
            file=open(self.batch_file, "rb"),
            purpose="batch"
        )
        print(f'批处理文件上传成功，input_file_id: {batch_input_file.id}')
        return batch_input_file.id


    def create_batch_request(self, input_file_id):
        """
        提交批处理请求, 返回 batch_job_id
        响应体样例：
        {
          "id": "batch_67760717ee4481909b10277c1227dcb7",
          "object": "batch",
          "endpoint": "/v1/chat/completions",
          "errors": null,
          "input_file_id": "file-78RvssonMDx1qE9XpQy7K3",
          "completion_window": "24h",
          "status": "validating",
          "output_file_id": null,
          "error_file_id": null,
          "created_at": 1735788312,
          "in_progress_at": null,
          "expires_at": 1735874712,
          "finalizing_at": null,
          "completed_at": null,
          "failed_at": null,
          "expired_at": null,
          "cancelling_at": null,
          "cancelled_at": null,
          "request_counts": {
            "total": 0,
            "completed": 0,
            "failed": 0
          },
          "metadata": null
        }
        """
        batch_job = client.batches.create(
            input_file_id=input_file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={
                "description": "Translation"
            }
        )
        batch_job_id = batch_job.id
        print(f'批处理文件被接受并处理的回执任务ID：{batch_job_id}')
        return batch_job_id

    def commit_job(self):
        """
        提交任务，并获取任务处理的ID
        return: batch_job_id  正在处理的批任务ID
        """
        # 先生成批处理文件
        self.build_batch()
        # 上传文件并获取回执的文件ID (该环节有可能失败)
        input_file_id = self.upload_batchfile()
        # 获取正在处理的批任务ID
        batch_job_id = self.create_batch_request(input_file_id)
        return batch_job_id

    @retry(tries=10, delay=10)
    def retrieve_batch(self, batch_job_id):
        """
        获取批处理请求的处理完成状态
        数据结构：
        {
            "id": "batch_67760717ee4481909b10277c1227dcb7",
            "object": "batch",
            "endpoint": "/v1/chat/completions",
            "errors": null,
            "input_file_id": "file-78RvssonMDx1qE9XpQy7K3",
            "completion_window": "24h",
            "status": "in_progress",
            "output_file_id": null,
            "error_file_id": null,
            "created_at": 1735788312,
            "in_progress_at": 1735788313,
            "expires_at": 1735874712,
            "finalizing_at": null,
            "completed_at": null,
            "failed_at": null,
            "expired_at": null,
            "cancelling_at": null,
            "cancelled_at": null,
            "request_counts": {
                "total": 110,
                "completed": 60,
                "failed": 0
            },
            "metadata": null
        }
        """
        # 获取批处理请求的处理结果
        url = f'https://api.openai.com/v1/batches/{batch_job_id}'
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers)
        data = response.json()

        # client.batches.retrieve(batch_job_id)

        created_at = data['created_at']
        expires_at = data['expires_at']
        request_counts_total = data['request_counts']['total']
        request_counts_completed = data['request_counts']['completed']
        request_counts_failed = data['request_counts']['failed']
        created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created_at))
        expires_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expires_at))
        print(
            f'创建时间：{created_at}\n过期时间：{expires_at}\n'
            f'总请求数：{request_counts_total}\n完成数：{request_counts_completed}\n'
            f'失败数：{request_counts_failed}\n'
        )
        print('------'*10)
        return data

    def wait_batch_job_done(self, batch_job_id):
        """
        等待批处理任务(openai 执行完毕)处理完成
        """
        while True:
            # 查询处理进度状态 （有可能会失败）
            data = self.retrieve_batch(batch_job_id)
            status = data['status']
            if status == 'completed':
                # string
                output_file_id = data['output_file_id']
                print(f'批处理任务全部处理完成，output_file_id：{output_file_id}')
                break
            time.sleep(100)
        # 获取结果
        content = client.files.content(output_file_id)
        # 保存处理结果
        if content.read():
            with open(self.batch_file_job_done, 'wb') as file:
                file.write(content.read())
            print('File content downloaded successfully to file.jsonl')
        else:
            print('Failed to download file:')

    def save_translation_result(self):
        """
        保存翻译结果为 PDF 和 txt
        """
        pages_content_translated = []
        origin_data_list = []
        # 逐行读取并解析 .jsonl 文件
        with open(self.batch_file_job_done, 'r', encoding='utf-8') as file:
            for line in file:
                # 去掉可能的空行
                if line.strip():
                    line_json = json.loads(line)
                    origin_data_list.append(line_json)

        # custom_id 进行升序排列，才是正确的顺序，避免返回的数据没有按照实际的顺序排列
        data_list = sorted(origin_data_list, key=lambda x: int(x["custom_id"]))
        for data in data_list:
            content = data['response']['body']['choices'][0]['message']['content']
            pages_content_translated.append(content)

        text = '\n'.join(pages_content_translated)
        # 保存为txt
        with open(self.output_txt, 'w', encoding='utf-8')as f:
            f.write(text)
        # 保存为pdf
        Topdf(self.output_pdf, self.output_txt).to_pdf(pages_content_translated)

    def run(self, batch_job_id=None):
        """
        翻译程序执行入口
        """
        if not batch_job_id:
            # 提交任务给OpenAI处理
            batch_job_id = self.commit_job()
        # 获取处理结果 并 保存
        self.wait_batch_job_done(batch_job_id)
        # 转换翻译结果为PDF和TXT
        self.save_translation_result()

if __name__ == '__main__':
    """
    一开始会出现以下情况，属于正常
    总请求数：0
    完成数：0
    """
    # 批处理模式
    # 支持.epub 和 .pdf 文件类型
    source_file = "(Group Therapy 01) Lauren League - Groupthink.epub"
    # 正在处理的批任务ID  (有值则代表继续获取上次的处理结果，None表示全新的处理方式)
    # 批处理文件被接受并处理的回执任务ID：batch_67cf88c03c2c8190bb44414109931212
    # batch_job_id = 'batch_680b493166088190af76da59c55f54ce'
    batch_job_id = None
    Translate(source_file).run(batch_job_id)