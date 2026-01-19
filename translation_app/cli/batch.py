#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量翻译 CLI
"""

import argparse
import sys

from translation_app.cli.logging_setup import setup_logging
from translation_app.services.batch_service import batch_translate


def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description='批量翻译工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--provider', '-p',
        type=str,
        choices=['akashml', 'deepseek', 'hyperbolic'],
        default='akashml',
        help='选择服务商: akashml、deepseek 或 hyperbolic (默认: akashml)'
    )
    args = parser.parse_args()

    batch_translate(args.provider)
    return 0


if __name__ == '__main__':
    sys.exit(main())

