#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量翻译工具（兼容入口）
"""

import sys

from translation_app.cli.batch import main


if __name__ == '__main__':
    sys.exit(main())
