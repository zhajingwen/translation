#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单文件翻译 CLI
"""

import argparse
import logging
import sys

from translation_app.cli.logging_setup import setup_logging
from translation_app.services.job_service import run_single_file


logger = logging.getLogger('Job')


def main():
    setup_logging()

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

    success = run_single_file(args.file, args.provider)
    if success:
        logger.info("翻译成功完成！")
        return 0
    logger.error("翻译失败！")
    return 1


if __name__ == '__main__':
    sys.exit(main())

