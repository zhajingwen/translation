#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一 CLI 入口
"""

import argparse
import sys

from translation_app.cli.logging_setup import setup_logging
from translation_app.services.batch_service import batch_translate
from translation_app.services.job_service import run_single_file
from translation_app.services.merge_service import merge_entrance


def main():
    setup_logging()

    parser = argparse.ArgumentParser(description='文档翻译工具 CLI')
    subparsers = parser.add_subparsers(dest='command', required=True)

    job_parser = subparsers.add_parser('job', help='单文件翻译')
    job_parser.add_argument('file', type=str, help='要翻译的文件路径')
    job_parser.add_argument(
        '--provider', '-p',
        type=str,
        choices=['akashml', 'deepseek', 'hyperbolic'],
        default='akashml',
        help='选择服务商 (默认: akashml)'
    )

    batch_parser = subparsers.add_parser('batch', help='批量翻译 files/ 目录')
    batch_parser.add_argument(
        '--provider', '-p',
        type=str,
        choices=['akashml', 'deepseek', 'hyperbolic'],
        default='akashml',
        help='选择服务商 (默认: akashml)'
    )

    merge_parser = subparsers.add_parser('merge', help='合并翻译后的文件')
    merge_parser.add_argument(
        '--files-dir',
        type=str,
        default='files',
        help='输入文件目录（默认: files）'
    )
    merge_parser.add_argument(
        '--keep-originals',
        action='store_true',
        default=False,
        help='保留原文件（默认会删除原文件）'
    )
    merge_parser.add_argument(
        '--backup',
        action='store_true',
        default=False,
        help='删除原文件时创建备份'
    )

    args = parser.parse_args()

    if args.command == 'job':
        success = run_single_file(args.file, args.provider)
        return 0 if success else 1
    if args.command == 'batch':
        batch_translate(args.provider)
        return 0
    if args.command == 'merge':
        merge_entrance(
            files_dir=args.files_dir,
            delete_originals=not args.keep_originals,
            backup=args.backup
        )
        return 0

    return 1


if __name__ == '__main__':
    sys.exit(main())

