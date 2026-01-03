import logging
import sys
from pathlib import Path

# ================== 日志配置 ==================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Translation Batch')

from akashml import TranslateConfig, Translate
from PyPDF2 import PdfReader
from ebooklib import epub
from bs4 import BeautifulSoup

def safe_delete(file_path: Path):
    """安全删除文件，捕获异常并记录"""
    try:
        file_path.unlink()
        logger.info(f"已删除: {file_path.name}")
    except Exception as e:
        logger.error(f"删除失败 {file_path.name}: {e}")

def count_file_characters(file_path: Path):
    """
    统计文件中的文本字符数
    支持 txt、pdf、epub 三种文件类型
    返回字符数，如果读取失败返回 -1
    """
    file_ext = file_path.suffix.lower()
    
    try:
        if file_ext == '.txt':
            # 读取txt文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            return len(content)
        
        elif file_ext == '.pdf':
            # 读取PDF文件
            reader = PdfReader(file_path)
            total_chars = 0
            for page in reader.pages:
                page_text = page.extract_text().strip()
                if page_text:
                    total_chars += len(page_text)
            return total_chars
        
        elif file_ext == '.epub':
            # 读取EPUB文件
            book = epub.read_epub(str(file_path), options={"ignore_ncx": True})
            total_chars = 0
            for item in book.get_items():
                # 只处理HTML/XHTML内容
                if item.media_type in ['application/xhtml+xml', 'application/xhtml', 'text/html', 'text/xhtml']:
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
        
        else:
            logger.warning(f"不支持的文件类型: {file_ext}")
            return -1
            
    except Exception as e:
        logger.error(f"读取文件字符数失败 {file_path.name}: {e}")
        return -1

def batch_translate():
    """
    批量翻译文件，支持 txt、pdf、epub 三种文件类型
    """
    # 可以根据API限制和网络情况调整参数
    #  model="Qwen/Qwen3-30B-A3B", 上下文限制为32K
    #  无法达到理论值，尚未达到理论值就会出现该问题：2025-12-20 20:15:48,362 - httpx - INFO - HTTP Request: POST https://api.akashml.com/v1/chat/completions "HTTP/1.1 502 Bad Gateway"
    config = TranslateConfig(
        max_workers=9,       # 最大线程数，建议5-6个
        max_retries=6,        # 最大重试次数
        retry_delay=120,       # 重试延迟时间(秒)
        chunk_size=3000,      # 文本切割阈值（字符数），默认8000
        min_chunk_size=1000,   # 最小切割长度（字符数），默认500
        api_timeout=60        # API 超时时间(秒)
    )
    
    current_dir = Path("./files")
    # 支持的文件扩展名
    supported_extensions = ['.txt', '.pdf', '.epub']
    
    # 收集所有支持的文件
    all_files = []
    for ext in supported_extensions:
        all_files.extend(sorted(current_dir.glob(f"*{ext}")))
    
    if not all_files:
        print("等待翻译的文件（txt/pdf/epub），退出。")
        return
    
    processed = 0
    for file_path in all_files:
        file_ext = file_path.suffix.lower()
        file_name = file_path.name
        
        # 如果文件本身是以 translated.txt 结尾，则跳过
        if file_name.endswith("translated.txt"):
            logger.info(f"跳过已翻译文件: {file_name}")
            continue
        
        # 检查文件字符数，如果小于1000则跳过并删除
        char_count = count_file_characters(file_path)
        if char_count >= 0 and char_count < 1000:
            logger.info(f"跳过文件（字符数 {char_count} < 1000）: {file_name}")
            safe_delete(file_path)
            continue
        
        # 检查翻译结果文件是否存在
        # 翻译后的文件名格式：原文件名（不含扩展名） + " translated.txt"
        translated_path = file_path.parent / f"{file_path.stem} translated.txt"
        
        # 如果有翻译结果了，那么就跳过
        if translated_path.exists():
            print(f"跳过: {file_name} 已存在翻译结果")
            # 删除原始文件
            safe_delete(file_path)
            logger.info(f'删除成功：{file_name}')
            continue
        
        try:
            # 启动翻译任务
            logger.info(f'开始翻译：{file_name} (类型: {file_ext})')
            result = Translate(file_name, config).run()
            if not result:
                print(f"翻译失败: {file_name}")
                continue
            processed += 1
            logger.info(f'翻译成功：{file_name}')
            # 删除原始文件
            safe_delete(file_path)
            logger.info(f'删除成功：{file_name}')
            logger.info(f'翻译成功结束：{file_name}')

        except Exception as e:
            print(f"错误翻译 {file_name}: {e}", file=sys.stderr)
            logger.error(f"处理失败: {file_name} - {e}")


if __name__ == '__main__':
    batch_translate()