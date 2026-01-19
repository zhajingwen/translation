#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单文件翻译工具（兼容入口）
"""

import sys

from translation_app.cli.job import main


if __name__ == '__main__':
    sys.exit(main())
