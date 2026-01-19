#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量翻译服务
"""

import logging
import time

from translation_app.domain.translator import Translator, TranslateConfig
from translation_app.infra.openai_client import build_openai_client
from translation_app.services.merge_service import merge_entrance
from translation_app.core.providers import get_provider
from translation_app.core.utils import (
    safe_delete,
    safe_rename,
    count_file_characters,
    is_file_chinese,
    get_translated_path
)
from translation_app.core.config import (
    LogConfig,
    PathConfig,
    CharLimits,
    FileFormats,
    TranslationDefaults
)


logger = logging.getLogger('BatchService')


def batch_translate(provider: str = 'akashml'):
    """
    批量翻译文件，支持 txt、pdf、epub 三种文件类型

    Args:
        provider: 服务商选择，可选值为 'akashml'、'deepseek' 或 'hyperbolic'
    """
    provider_config = get_provider(provider)

    config = TranslateConfig(
        max_workers=TranslationDefaults.BATCH_MAX_WORKERS,
        max_retries=TranslationDefaults.BATCH_MAX_RETRIES,
        retry_delay=TranslationDefaults.BATCH_RETRY_DELAY,
        chunk_size=TranslationDefaults.BATCH_CHUNK_SIZE,
        min_chunk_size=TranslationDefaults.BATCH_MIN_CHUNK_SIZE,
        api_timeout=TranslationDefaults.BATCH_API_TIMEOUT,
        api_base_url=provider_config.api_base_url,
        model=provider_config.model,
        api_key=provider_config.api_key,
        client_factory=build_openai_client
    )

    # 确保工作目录存在
    PathConfig.ensure_dirs()
    current_dir = PathConfig.WORK_DIR

    # 收集所有支持的文件
    all_files = []
    for ext in FileFormats.SUPPORTED_EXTENSIONS:
        all_files.extend(sorted(current_dir.glob(f"*{ext}")))

    if not all_files:
        print("未找到待翻译的文件（txt/pdf/epub），退出。")
        return

    # 预处理：筛选出需要处理的文件
    files_to_process = []
    skipped_already_translated = 0
    skipped_already_chinese = 0
    skipped_char_too_few = 0
    skipped_result_exists = 0

    for file_path in all_files:
        file_name = file_path.name

        # 跳过已翻译文件
        if file_name.endswith("translated.txt"):
            skipped_already_translated += 1
            logger.debug(f"[预处理] 跳过已翻译文件: {file_name}")
            continue

        # 检测中文文件并重命名（仅针对 .txt 文件）
        if file_path.suffix.lower() == '.txt' and is_file_chinese(file_path):
            skipped_already_chinese += 1
            new_name = f"{file_path.stem}{FileFormats.TRANSLATED_SUFFIX}"
            if safe_rename(file_path, new_name):
                logger.info(f"[预处理] 跳过中文文件并重命名: {file_name} -> {new_name}")
            else:
                logger.info(f"[预处理] 跳过中文文件（重命名失败）: {file_name}")
            continue

        # 检查文件字符数，小于阈值则删除
        char_count = count_file_characters(file_path)
        if char_count >= 0 and char_count < CharLimits.MIN_FILE_CHARS:
            skipped_char_too_few += 1
            logger.info(f"[预处理] 删除文件（字符数 {char_count} < {CharLimits.MIN_FILE_CHARS}）: {file_name}")
            safe_delete(file_path)
            continue

        # 检查翻译结果文件是否存在
        translated_path = get_translated_path(file_path)

        if translated_path.exists():
            skipped_result_exists += 1
            logger.info(f"[预处理] 删除文件（已存在翻译结果）: {file_name}")
            safe_delete(file_path)
            continue

        files_to_process.append(file_path)

    skipped_pre_count = (
        skipped_already_translated
        + skipped_already_chinese
        + skipped_char_too_few
        + skipped_result_exists
    )

    if not files_to_process:
        logger.info(f"没有需要处理的文件（预处理跳过 {skipped_pre_count} 个文件）")
        return

    # 初始化进度统计变量
    total_files = len(files_to_process)
    current_index = 0
    success_count = 0
    failed_count = 0
    skipped_count = skipped_pre_count
    start_time = time.time()

    # 记录任务开始信息
    logger.info('=' * 60)
    logger.info('[任务] 批量翻译任务开始')
    logger.info(f'[任务] 总文件数: {total_files}')
    logger.info(
        '[任务] 配置: 线程数=%s, 重试次数=%s, 重试延迟=%s秒, chunk大小=%s, '
        '最小chunk=%s, 超时=%s秒',
        config.max_workers,
        config.max_retries,
        config.retry_delay,
        config.chunk_size,
        config.min_chunk_size,
        config.api_timeout
    )

    if skipped_pre_count > 0:
        logger.info(f'[任务] 预处理统计:')
        if skipped_already_translated > 0:
            logger.info(f'  - 跳过已翻译文件: {skipped_already_translated} 个')
        if skipped_already_chinese > 0:
            logger.info(f'  - 跳过中文文件: {skipped_already_chinese} 个（不删除）')
        if skipped_char_too_few > 0:
            logger.info(f'  - 删除字符数不足文件: {skipped_char_too_few} 个（字符数 < {CharLimits.MIN_FILE_CHARS}）')
        if skipped_result_exists > 0:
            logger.info(f'  - 删除已存在翻译结果的文件: {skipped_result_exists} 个')
        logger.info(f'  - 预处理跳过总计: {skipped_pre_count} 个文件')
    logger.info('=' * 60)

    # 处理每个文件
    for file_path in files_to_process:
        current_index += 1
        file_ext = file_path.suffix.lower()
        file_name = file_path.name

        # 计算进度百分比
        progress_percent = (current_index / total_files) * 100

        # 打印当前进度
        logger.info(f'[进度] 处理第 {current_index}/{total_files} 个文件 ({progress_percent:.1f}%)：{file_name}')

        try:
            # 启动翻译任务
            logger.info(f'开始翻译：{file_name} (类型: {file_ext})')
            translator = Translator(file_name, config)
            result = translator.run()

            if not result:
                failed_count += 1
                logger.error(f"翻译失败: {file_name}")
                # 打印当前统计
                remaining = total_files - current_index
                logger.info(f'[统计] 成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}, 剩余: {remaining}')
                continue

            success_count += 1

            # 翻译成功后删除原文件
            safe_delete(file_path)

            # 打印当前统计
            remaining = total_files - current_index
            logger.info(f'[统计] 成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}, 剩余: {remaining}')

        except Exception as e:
            failed_count += 1
            logger.error(f"处理文件时发生异常: {file_name}, 错误: {e}")
            remaining = total_files - current_index
            logger.info(f'[统计] 成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}, 剩余: {remaining}')

    # 任务结束统计
    total_time = time.time() - start_time
    logger.info('=' * 60)
    logger.info('[任务] 批量翻译任务结束')
    logger.info(f'[统计] 总计处理: {total_files} 个文件')
    logger.info(f'[统计] 成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}')
    logger.info(f'[统计] 总耗时: {total_time:.1f} 秒')
    logger.info('=' * 60)

    # 调用合并脚本
    if LogConfig.LOG_SHOW_CONTENT:
        logger.info('[任务] 启动文件合并流程')
    merge_entrance(
        files_dir=str(PathConfig.WORK_DIR),
        delete_originals=False,
        backup=True
    )

