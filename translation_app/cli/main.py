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
from translation_app.services.gemini_batch_service import (
    check_status as gemini_batch_check_status,
    fetch_results as gemini_batch_fetch_results,
    run_and_wait as gemini_batch_run_and_wait,
    submit_batch as gemini_batch_submit,
)


def main():
    setup_logging()

    parser = argparse.ArgumentParser(description='文档翻译工具 CLI')
    subparsers = parser.add_subparsers(dest='command', required=True)

    job_parser = subparsers.add_parser('job', help='单文件翻译')
    job_parser.add_argument('file', type=str, help='要翻译的文件路径')
    job_parser.add_argument(
        '--provider', '-p',
        type=str,
        choices=['akashml', 'deepseek', 'hyperbolic', 'aihubmix', 'openrouter', 'nvidia', 'gemini', 'bailian', 'bai', 'bonsai', 'ollama'],
        default='akashml',
        help='选择服务商 (默认: akashml)；bonsai 默认连 Bonsai-demo MLX :8081，可用环境变量改 llama :8080；ollama 默认连本地 :11434'
    )

    batch_parser = subparsers.add_parser('batch', help='批量翻译 files/ 目录')
    batch_parser.add_argument(
        '--provider', '-p',
        type=str,
        choices=['akashml', 'deepseek', 'hyperbolic', 'aihubmix', 'openrouter', 'nvidia', 'gemini', 'bailian', 'bai', 'bonsai', 'ollama'],
        default='akashml',
        help='选择服务商 (默认: akashml)'
    )
    batch_parser.add_argument(
        '--no-merge',
        action='store_true',
        default=False,
        help='翻译完成后不自动合并翻译结果（默认会自动合并）'
    )

    gemini_batch_parser = subparsers.add_parser(
        'gemini-batch',
        help='Gemini 官方异步批处理（Batch API），比实时接口更省钱但非实时返回'
    )
    gemini_batch_sub = gemini_batch_parser.add_subparsers(dest='gemini_batch_action', required=True)

    gb_submit = gemini_batch_sub.add_parser('submit', help='提取并切割 files/ 目录下的文件，提交批处理任务')
    gb_submit.add_argument('--model', type=str, default=None, help='覆盖使用的模型（默认: GEMINI_MODEL 或服务商默认模型）')
    gb_submit.add_argument('--display-name', type=str, default=None, help='任务显示名（默认按时间戳自动生成）')

    gb_status = gemini_batch_sub.add_parser('status', help='查询批处理任务状态')
    gb_status.add_argument('--job', type=str, default=None, help='任务名（如 batches/xxxxx），不传则使用最近一次提交的任务')

    gb_fetch = gemini_batch_sub.add_parser('fetch', help='拉取已完成任务的结果并保存')
    gb_fetch.add_argument('--job', type=str, default=None, help='任务名，不传则使用最近一次提交的任务')
    gb_fetch.add_argument('--no-merge', action='store_true', default=False, help='拉取完成后不自动合并翻译结果')

    gb_run = gemini_batch_sub.add_parser('run', help='提交任务后阻塞轮询，完成后自动拉取结果')
    gb_run.add_argument('--model', type=str, default=None, help='覆盖使用的模型')
    gb_run.add_argument('--display-name', type=str, default=None, help='任务显示名')
    gb_run.add_argument('--poll-interval', type=int, default=None, help='轮询间隔（秒），默认 30')
    gb_run.add_argument('--max-wait', type=int, default=None, help='最长等待时间（秒），默认不限')
    gb_run.add_argument('--no-merge', action='store_true', default=False, help='拉取完成后不自动合并翻译结果')

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
        batch_translate(args.provider, auto_merge=not args.no_merge)
        return 0
    if args.command == 'gemini-batch':
        if args.gemini_batch_action == 'submit':
            manifest = gemini_batch_submit(model=args.model, display_name=args.display_name)
            return 0 if manifest else 1
        if args.gemini_batch_action == 'status':
            state = gemini_batch_check_status(job_name=args.job)
            return 0 if state else 1
        if args.gemini_batch_action == 'fetch':
            ok = gemini_batch_fetch_results(job_name=args.job, auto_merge=not args.no_merge)
            return 0 if ok else 1
        if args.gemini_batch_action == 'run':
            ok = gemini_batch_run_and_wait(
                model=args.model,
                display_name=args.display_name,
                poll_interval=args.poll_interval,
                max_wait=args.max_wait,
                auto_merge=not args.no_merge
            )
            return 0 if ok else 1
        return 1
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

