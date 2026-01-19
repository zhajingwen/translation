#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档合并脚本（兼容入口）
"""

from translation_app.cli.logging_setup import setup_logging
from translation_app.services.merge_service import (
    natural_sort_key,
    scan_and_filter_files,
    merge_files,
    delete_original_files,
    merge_entrance
)

__all__ = [
    'natural_sort_key',
    'scan_and_filter_files',
    'merge_files',
    'delete_original_files',
    'merge_entrance',
]


if __name__ == "__main__":
    setup_logging()
    merge_entrance(
        files_dir="files",
        delete_originals=True,
        backup=True
    )
