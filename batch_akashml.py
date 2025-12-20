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

def safe_delete(file_path: Path):
    """安全删除文件，捕获异常并记录"""
    try:
        file_path.unlink()
        logger.info(f"已删除: {file_path.name}")
    except Exception as e:
        logger.error(f"删除失败 {file_path.name}: {e}")

def batch_translate():
    """
    批量翻译文件，支持 txt、pdf、epub 三种文件类型
    """
    # 可以根据API限制和网络情况调整参数
    config = TranslateConfig(
        max_workers=9,       # 最大线程数，建议5-6个
        max_retries=6,        # 最大重试次数
        retry_delay=120,       # 重试延迟时间(秒)
        chunk_size=20000,      # 文本切割阈值（字符数），默认8000
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