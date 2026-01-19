#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单文件翻译工具

功能：翻译单个 PDF/EPUB/TXT 文件

使用说明：
1. 命令行运行：
   python job.py [--provider akashml|deepseek|hyperbolic]
   - --provider 或 -p: 选择服务商（akashml、deepseek 或 hyperbolic），默认为 akashml
   - 需要设置对应的环境变量：AKASHML_API_KEY、DEEPSEEK_API_KEY 或 HYPERBOLIC_API_KEY

2. 作为模块使用时，通过 TranslateConfig 传入配置

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

# 保留旧的 PDF 类（虽然不再使用，但为了兼容性保留）
from fpdf import FPDF
import os


class PDF(FPDF):
    """保留用于向后兼容（当前版本不生成PDF）"""
    def __init__(self):
        super().__init__()
        self.font_loaded = False
        try:
            font_paths = [
                './kaiti.ttf',
                os.path.join(os.path.dirname(__file__), 'kaiti.ttf'),
                '/usr/share/fonts/truetype/kaiti.ttf',
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    self.add_font('kaiti', '', font_path)
                    self.font_loaded = True
                    break
        except Exception as e:
            logger.warning(f"字体加载失败: {e}")

    def footer(self):
        self.set_y(-15)
        if self.font_loaded:
            self.set_font('kaiti', '', 8)
            self.cell(0, 10, f'第 {self.page_no()} 页', 0, new_x='LMARGIN', new_y='NEXT', align='C')
        else:
            self.set_font('Helvetica', '', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, new_x='LMARGIN', new_y='NEXT', align='C')


# ================== 主程序 ==================

def main():
    """主程序入口"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='单文件翻译工具')
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
    
    # 配置文件名（需要手动修改）
    source_origin_book_name = "files/070 - Hey Tech, Come to Healthcare.txt"
    
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
