import argparse
import logging
import os
import sys
import time
from pathlib import Path

# ================== 日志配置 ==================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Translation Batch')

from PyPDF2 import PdfReader
from ebooklib import epub
from bs4 import BeautifulSoup
from job import TranslateConfig, Translate
# from
from merge_translated_files import merge_entrance

def safe_delete(file_path: Path):
    """安全删除文件，捕获异常并记录"""
    try:
        file_path.unlink()
        logger.info(f"已删除: {file_path.name}")
    except Exception as e:
        logger.error(f"删除失败 {file_path.name}: {e}")

def safe_rename(file_path: Path, new_name: str):
    """安全重命名文件，捕获异常并记录"""
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

def is_file_chinese(file_path: Path, threshold: float = 0.3) -> bool:
    """
    判断 .txt 文件内容是否主要是中文
    
    Args:
        file_path: 文件路径（仅支持 .txt 文件）
        threshold: 中文字符占比阈值，默认 0.3 (30%)
    
    Returns:
        如果中文字符占比 >= threshold 则返回 True，否则返回 False
        如果读取失败返回 False
    """
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

def batch_translate(provider='akashml'):
    """
    批量翻译文件，支持 txt、pdf、epub 三种文件类型
    
    Args:
        provider: 服务商选择，可选值为 'akashml'、'deepseek' 或 'hyperbolic'，默认为 'akashml'
    """
    # 根据服务商选择配置
    if provider == 'akashml':
        LLM_API_BASE_URL = 'https://api.akashml.com/v1'
        LLM_MODEL = 'Qwen/Qwen3-30B-A3B'
        LLM_API_KEY = os.environ.get('AKASHML_API_KEY')
    elif provider == 'deepseek':
        LLM_API_BASE_URL = 'https://api.deepseek.com'
        LLM_MODEL = 'deepseek-chat'
        LLM_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
    elif provider == 'hyperbolic':
        LLM_API_BASE_URL = 'https://api.hyperbolic.xyz/v1'
        LLM_MODEL = 'openai/gpt-oss-20b'
        LLM_API_KEY = os.environ.get('HYPERBOLIC_API_KEY')
    else:
        raise ValueError(f"不支持的服务商: {provider}，请选择 'akashml'、'deepseek' 或 'hyperbolic'")
    
    # 可以根据API限制和网络情况调整参数
    #  model="Qwen/Qwen3-30B-A3B", 上下文限制为32K
    #  无法达到理论值，尚未达到理论值就会出现该问题：2025-12-20 20:15:48,362 - httpx - INFO - HTTP Request: POST https://api.akashml.com/v1/chat/completions "HTTP/1.1 502 Bad Gateway"
    config = TranslateConfig(
        max_workers=8,       # 最大线程数，建议5-6个
        max_retries=6,        # 最大重试次数
        retry_delay=120,       # 重试延迟时间(秒)
        chunk_size=3000,      # 文本切割阈值（字符数），默认8000
        min_chunk_size=1000,   # 最小切割长度（字符数），默认500
        api_timeout=60,        # API 超时时间(秒)
        api_base_url=LLM_API_BASE_URL,
        model=LLM_MODEL,
        api_key=LLM_API_KEY
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
    
    # 筛选出需要处理的文件（排除已翻译的、字符数不足的）
    files_to_process = []
    skipped_already_translated = 0  # 跳过：文件名本身是翻译结果
    skipped_already_chinese = 0  # 跳过：文件内容已经是中文
    skipped_char_too_few = 0  # 跳过并删除：字符数不足
    skipped_result_exists = 0  # 跳过并删除：已存在翻译结果
    
    for file_path in all_files:
        file_name = file_path.name
        
        # 如果文件本身是以 translated.txt 结尾，则跳过
        if file_name.endswith("translated.txt"):
            skipped_already_translated += 1
            logger.debug(f"[预处理] 跳过已翻译文件: {file_name}")
            continue
        
        # 检查文件内容是否已经是中文，如果是则跳过但不删除（仅针对 .txt 文件）
        if file_path.suffix.lower() == '.txt' and is_file_chinese(file_path, threshold=0.3):
            skipped_already_chinese += 1
            # 重命名文件为 "原文件名 translated.txt" 格式
            new_name = f"{file_path.stem} translated.txt"
            if safe_rename(file_path, new_name):
                logger.info(f"[预处理] 跳过中文文件并重命名: {file_name} -> {new_name}")
            else:
                logger.info(f"[预处理] 跳过中文文件（重命名失败）: {file_name}")
            continue
        
        # 检查文件字符数，如果小于1000则跳过并删除
        char_count = count_file_characters(file_path)
        if char_count >= 0 and char_count < 1000:
            skipped_char_too_few += 1
            logger.info(f"[预处理] 删除文件（字符数 {char_count} < 1000）: {file_name}")
            safe_delete(file_path)
            continue
        
        # 检查翻译结果文件是否存在
        # 翻译后的文件名格式：原文件名（不含扩展名） + " translated.txt"
        translated_path = file_path.parent / f"{file_path.stem} translated.txt"
        
        # 如果有翻译结果了，那么就跳过
        if translated_path.exists():
            skipped_result_exists += 1
            logger.info(f"[预处理] 删除文件（已存在翻译结果）: {file_name}")
            safe_delete(file_path)
            continue
        
        files_to_process.append(file_path)
    
    skipped_pre_count = skipped_already_translated + skipped_already_chinese + skipped_char_too_few + skipped_result_exists
    
    if not files_to_process:
        logger.info(f"没有需要处理的文件（预处理跳过 {skipped_pre_count} 个文件）")
        return
    
    # 初始化进度统计变量
    total_files = len(files_to_process)
    current_index = 0
    success_count = 0
    failed_count = 0
    skipped_count = skipped_pre_count
    start_time = time.time()
    
    # 记录任务开始信息
    logger.info('=' * 60)
    logger.info('[任务] 批量翻译任务开始')
    logger.info(f'[任务] 总文件数: {total_files}')
    logger.info(f'[任务] 配置: 线程数={config.max_workers}, 重试次数={config.max_retries}, '
                f'重试延迟={config.retry_delay}秒, chunk大小={config.chunk_size}, '
                f'最小chunk={config.min_chunk_size}, 超时={config.api_timeout}秒')
    if skipped_pre_count > 0:
        logger.info(f'[任务] 预处理统计:')
        if skipped_already_translated > 0:
            logger.info(f'  - 跳过已翻译文件: {skipped_already_translated} 个')
        if skipped_already_chinese > 0:
            logger.info(f'  - 跳过中文文件: {skipped_already_chinese} 个（不删除）')
        if skipped_char_too_few > 0:
            logger.info(f'  - 删除字符数不足文件: {skipped_char_too_few} 个（字符数 < 1000）')
        if skipped_result_exists > 0:
            logger.info(f'  - 删除已存在翻译结果的文件: {skipped_result_exists} 个')
        logger.info(f'  - 预处理跳过总计: {skipped_pre_count} 个文件')
    logger.info('=' * 60)
    
    # 处理每个文件
    for file_path in files_to_process:
        current_index += 1
        file_ext = file_path.suffix.lower()
        file_name = file_path.name
        
        # 计算进度百分比
        progress_percent = (current_index / total_files) * 100
        
        # 打印当前进度
        logger.info(f'[进度] 处理第 {current_index}/{total_files} 个文件 ({progress_percent:.1f}%)：{file_name}')
        
        try:
            # 启动翻译任务
            logger.info(f'开始翻译：{file_name} (类型: {file_ext})')
            result = Translate(file_name, config).run()
            if not result:
                failed_count += 1
                logger.error(f"翻译失败: {file_name}")
                # 打印当前统计
                remaining = total_files - current_index
                logger.info(f'[统计] 成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}, 剩余: {remaining}')
                continue
            
            success_count += 1
            logger.info(f'翻译成功：{file_name}')
            # 删除原始文件
            safe_delete(file_path)
            logger.info(f'删除成功：{file_name}')
            
            # 打印当前统计
            remaining = total_files - current_index
            logger.info(f'[统计] 成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}, 剩余: {remaining}')

        except Exception as e:
            failed_count += 1
            print(f"错误翻译 {file_name}: {e}", file=sys.stderr)
            logger.error(f"处理失败: {file_name} - {e}")
            # 打印当前统计
            remaining = total_files - current_index
            logger.info(f'[统计] 成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}, 剩余: {remaining}')
    
    # 计算总耗时
    end_time = time.time()
    total_duration = end_time - start_time
    
    # 打印最终统计
    logger.info('=' * 60)
    logger.info('[任务] 批量翻译任务完成')
    logger.info(f'[统计] 总耗时: {total_duration:.1f} 秒 ({total_duration/60:.1f} 分钟)')
    logger.info(f'[统计] 总文件数: {total_files}')
    logger.info(f'[统计] 成功: {success_count} ({success_count/total_files*100:.1f}%)')
    logger.info(f'[统计] 失败: {failed_count} ({failed_count/total_files*100:.1f}%)')
    if skipped_count > 0:
        logger.info(f'[统计] 预处理跳过: {skipped_count} 个文件')
        if skipped_already_translated > 0:
            logger.info(f'  - 跳过已翻译文件: {skipped_already_translated} 个')
        if skipped_already_chinese > 0:
            logger.info(f'  - 跳过中文文件: {skipped_already_chinese} 个（不删除）')
        if skipped_char_too_few > 0:
            logger.info(f'  - 删除字符数不足文件: {skipped_char_too_few} 个（字符数 < 1000）')
        if skipped_result_exists > 0:
            logger.info(f'  - 删除已存在翻译结果的文件: {skipped_result_exists} 个')
    if success_count > 0:
        avg_time = total_duration / success_count
        logger.info(f'[统计] 平均处理时间: {avg_time:.1f} 秒/文件')
    logger.info('=' * 60)


if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='批量翻译文件工具')
    parser.add_argument(
        '--provider', '-p',
        type=str,
        choices=['akashml', 'deepseek', 'hyperbolic'],
        default='akashml',
        help='选择服务商: akashml、deepseek 或 hyperbolic (默认: akashml)'
    )
    args = parser.parse_args()
    
    # 批量翻译文件
    batch_translate(provider=args.provider)
    # 合并翻译后的文件
    merge_entrance(
        files_dir="files", # 输入文件目录
        delete_originals=True, # 删除原文件
        backup=False # 是否备份原文件
    )