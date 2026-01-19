#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单文件翻译工具

功能：翻译单个 PDF/EPUB/TXT 文件

使用说明：
1. 命令行运行：
   python job.py <文件路径> [选项]
   
   位置参数：
     文件路径              要翻译的文件（支持 .txt, .pdf, .epub）
   
   可选参数：
     --provider, -p       选择服务商（akashml、deepseek 或 hyperbolic），默认为 akashml
   
   示例：
     python job.py myfile.txt
     python job.py files/document.pdf --provider deepseek
     python job.py book.epub -p hyperbolic

2. 环境变量配置：
   - AKASHML_API_KEY: AkashML 服务的 API 密钥
   - DEEPSEEK_API_KEY: DeepSeek 服务的 API 密钥
   - HYPERBOLIC_API_KEY: Hyperbolic 服务的 API 密钥

3. 作为模块使用时，通过 TranslateConfig 传入配置

注意事项：
- 根据所选服务商的并发限制调整线程数
- 网络不稳定时建议增加重试次数和延迟时间
- 翻译大文件时建议先测试小文件确认配置合适
"""

import argparse
import logging
import os

from translator import Translator, TranslateConfig
from providers import get_provider
from config import LogConfig, TranslationDefaults


# ================== 日志配置 ==================
logging.basicConfig(
    level=getattr(logging, LogConfig.LOG_LEVEL, logging.INFO),
    format=LogConfig.LOG_FORMAT,
    datefmt=LogConfig.LOG_DATE_FORMAT
)
logger = logging.getLogger('Job')

# 配置 OpenAI SDK 的日志
openai_logger = logging.getLogger('openai._base_client')
openai_logger.setLevel(logging.INFO)

# httpx 设置为 WARNING，只显示错误信息
httpx_logger = logging.getLogger('httpx')
httpx_logger.setLevel(logging.WARNING)


# ================== 向后兼容的导入 ==================
# 保留旧的导入方式以向后兼容
Translate = Translator


# ================== 主程序 ==================

def main():
    """主程序入口"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='单文件翻译工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法：
  python job.py myfile.txt
  python job.py files/document.pdf --provider deepseek
  python job.py book.epub -p hyperbolic
        """
    )
    parser.add_argument(
        'file',
        type=str,
        help='要翻译的文件路径（支持 .txt, .pdf, .epub）'
    )
    parser.add_argument(
        '--provider', '-p',
        type=str,
        choices=['akashml', 'deepseek', 'hyperbolic'],
        default='akashml',
        help='选择服务商: akashml、deepseek 或 hyperbolic (默认: akashml)'
    )
    args = parser.parse_args()
    
    # 获取服务商配置
    provider_config = get_provider(args.provider)
    
    # 从命令行参数获取文件路径
    source_origin_book_name = args.file
    
    # 验证文件是否存在
    from pathlib import Path
    file_path = Path(source_origin_book_name)
    if not file_path.exists():
        logger.error(f"文件不存在: {source_origin_book_name}")
        exit(1)
    
    # 验证文件格式
    supported_extensions = ['.txt', '.pdf', '.epub']
    if file_path.suffix.lower() not in supported_extensions:
        logger.error(f"不支持的文件格式: {file_path.suffix}")
        logger.error(f"支持的格式: {', '.join(supported_extensions)}")
        exit(1)
    
    logger.info(f"准备翻译文件: {source_origin_book_name}")
    logger.info(f"使用服务商: {provider_config.name}")
    
    # 创建翻译配置
    config = TranslateConfig(
        max_workers=TranslationDefaults.JOB_MAX_WORKERS,
        max_retries=TranslationDefaults.JOB_MAX_RETRIES,
        retry_delay=TranslationDefaults.JOB_RETRY_DELAY,
        chunk_size=TranslationDefaults.JOB_CHUNK_SIZE,
        min_chunk_size=TranslationDefaults.JOB_MIN_CHUNK_SIZE,
        api_timeout=TranslationDefaults.JOB_API_TIMEOUT,
        api_base_url=provider_config.api_base_url,
        model=provider_config.model,
        api_key=provider_config.api_key
    )
    
    # 启动翻译任务
    translator = Translator(source_origin_book_name, config)
    success = translator.run()
    
    if success:
        logger.info(f"翻译成功完成！")
    else:
        logger.error(f"翻译失败！")
        exit(1)


if __name__ == '__main__':
    main()
