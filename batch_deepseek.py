import logging
import sys
from pathlib import Path

# ================== 日志配置 ==================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Translation Batch')

from deepseek_nopdf import TranslateConfig, Translate

def safe_delete(file_path: Path):
    """安全删除文件，捕获异常并记录"""
    try:
        file_path.unlink()
        logger.info(f"已删除: {file_path.name}")
    except Exception as e:
        logger.error(f"删除失败 {file_path.name}: {e}")

def batch_translate():
    """
    
    """
    # 可以根据API限制和网络情况调整参数
    config = TranslateConfig(
        max_workers=10,      # 最大线程数，建议3-10个
        max_retries=10,      # 最大重试次数
        retry_delay=10       # 重试延迟时间(秒)
    )
    
    current_dir = Path("./files")
    txt_files = sorted(current_dir.glob("*.txt"))
    
    if not txt_files:
        print("等待翻译的txt文件，退出。")
        return
    
    processed = 0
    for txt_path in txt_files:
        # 如果文件本身是以 translated.txt 结尾，则跳过
        if txt_path.name.endswith("translated.txt"):
            logger.info(f"跳过已翻译文件: {txt_path.name}")
            continue
        
        # 如果原文件是 file.txt，检查 file translated.txt（中间有空格）
        txt_translated_path = txt_path.parent / f"{txt_path.stem} translated.txt"

        # 如果有翻译结果了，那么就跳过
        if txt_translated_path.exists():
            print(f"跳过: {txt_path.name} 已存在")
            # 删除原始txt文件
            safe_delete(txt_path)
            logger.info(f'删除成功：{txt_path.name}')
            continue
        
        try:
            # 启动翻译任务
            logger.info(f'开始翻译：{txt_path.name}')
            result = Translate(txt_path.name, config).run()
            if not result:
                print(f"翻译失败: {txt_path.name}")
                continue
            processed += 1
            logger.info(f'翻译成功：{txt_path.name}')
            # 删除原始txt文件
            safe_delete(txt_path)
            logger.info(f'删除成功：{txt_path.name}')
            logger.info(f'翻译成功结束：{txt_path.name}')

        except Exception as e:
            print(f"错误翻译 {txt_path.name}: {e}", file=sys.stderr)
            logger.error(f"处理失败: {txt_path.name} - {e}")


if __name__ == '__main__':
    batch_translate()