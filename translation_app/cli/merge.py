#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件合并 CLI
"""

import argparse
import sys

from translation_app.cli.logging_setup import setup_logging
from translation_app.services.merge_service import merge_entrance


def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description='翻译文件合并工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--files-dir',
        type=str,
        default='files',
        help='输入文件目录（默认: files）'
    )
    parser.add_argument(
        '--keep-originals',
        action='store_true',
        default=False,
        help='保留原文件（默认会删除原文件）'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        default=False,
        help='删除原文件时创建备份'
    )
    args = parser.parse_args()

    delete_originals = not args.keep_originals
    backup = args.backup

    merge_entrance(
        files_dir=args.files_dir,
        delete_originals=delete_originals,
        backup=backup
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())

