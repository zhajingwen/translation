#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量翻译工具

功能：批量翻译 files/ 目录下的所有文件

使用说明：
    python batch.py [--provider akashml|deepseek|hyperbolic]

处理流程：
1. 扫描 files/ 目录下的所有 .txt、.pdf、.epub 文件
2. 预处理筛选：
   - 跳过已翻译文件（文件名以 translated.txt 结尾）
   - 检测中文文件并重命名（中文字符占比 >= 30%）
   - 删除字符数 < 1000 的文件
   - 跳过已存在翻译结果的文件（删除原文件）
3. 依次翻译每个文件
4. 翻译成功后删除原文件
5. 自动调用合并脚本合并小型文件（< 10万字）
"""

import argparse
import logging
import sys
import time
from pathlib import Path

from translator import Translator, TranslateConfig
from providers import get_provider
from utils import (
    safe_delete, 
    safe_rename, 
    count_file_characters, 
    is_file_chinese,
    get_translated_path
)
from config import (
    LogConfig, 
    PathConfig, 
    CharLimits, 
    FileFormats,
    TranslationDefaults
)
from merge_translated_files import merge_entrance


# ================== 日志配置 ==================
logging.basicConfig(
    level=getattr(logging, LogConfig.LOG_LEVEL, logging.INFO),
    format=LogConfig.LOG_FORMAT,
    datefmt=LogConfig.LOG_DATE_FORMAT
)
logger = logging.getLogger('Batch')


def batch_translate(provider='akashml'):
    """
    批量翻译文件，支持 txt、pdf、epub 三种文件类型
    
    Args:
        provider: 服务商选择，可选值为 'akashml'、'deepseek' 或 'hyperbolic'，默认为 'akashml'
    """
    # 获取服务商配置
    provider_config = get_provider(provider)
    
    # 创建翻译配置
    config = TranslateConfig(
        max_workers=TranslationDefaults.BATCH_MAX_WORKERS,
        max_retries=TranslationDefaults.BATCH_MAX_RETRIES,
        retry_delay=TranslationDefaults.BATCH_RETRY_DELAY,
        chunk_size=TranslationDefaults.BATCH_CHUNK_SIZE,
        min_chunk_size=TranslationDefaults.BATCH_MIN_CHUNK_SIZE,
        api_timeout=TranslationDefaults.BATCH_API_TIMEOUT,
        api_base_url=provider_config.api_base_url,
        model=provider_config.model,
        api_key=provider_config.api_key
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
    
    skipped_pre_count = (skipped_already_translated + skipped_already_chinese + 
                        skipped_char_too_few + skipped_result_exists)
    
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
    logger.info(f'[任务] 配置: 线程数={config.max_workers}, 重试次数={config.max_retries}, '
                f'重试延迟={config.retry_delay}秒, chunk大小={config.chunk_size}, '
                f'最小chunk={config.min_chunk_size}, 超时={config.api_timeout}秒')
    
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
            logger.info(f'翻译成功：{file_name}')
            # 删除原始文件
            safe_delete(file_path)
            logger.info(f'删除成功：{file_name}')
            
            # 打印当前统计
            remaining = total_files - current_index
            logger.info(f'[统计] 成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}, 剩余: {remaining}')

        except Exception as e:
            failed_count += 1
            print(f"错误翻译 {file_name}: {e}", file=sys.stderr)
            logger.error(f"处理失败: {file_name} - {e}")
            # 打印当前统计
            remaining = total_files - current_index
            logger.info(f'[统计] 成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}, 剩余: {remaining}')
    
    # 计算总耗时
    end_time = time.time()
    total_duration = end_time - start_time
    
    # 打印最终统计
    logger.info('=' * 60)
    logger.info('[任务] 批量翻译任务完成')
    logger.info(f'[统计] 总耗时: {total_duration:.1f} 秒 ({total_duration/60:.1f} 分钟)')
    logger.info(f'[统计] 总文件数: {total_files}')
    logger.info(f'[统计] 成功: {success_count} ({success_count/total_files*100:.1f}%)')
    logger.info(f'[统计] 失败: {failed_count} ({failed_count/total_files*100:.1f}%)')
    if skipped_count > 0:
        logger.info(f'[统计] 预处理跳过: {skipped_count} 个文件')
        if skipped_already_translated > 0:
            logger.info(f'  - 跳过已翻译文件: {skipped_already_translated} 个')
        if skipped_already_chinese > 0:
            logger.info(f'  - 跳过中文文件: {skipped_already_chinese} 个（不删除）')
        if skipped_char_too_few > 0:
            logger.info(f'  - 删除字符数不足文件: {skipped_char_too_few} 个（字符数 < {CharLimits.MIN_FILE_CHARS}）')
        if skipped_result_exists > 0:
            logger.info(f'  - 删除已存在翻译结果的文件: {skipped_result_exists} 个')
    if success_count > 0:
        avg_time = total_duration / success_count
        logger.info(f'[统计] 平均处理时间: {avg_time:.1f} 秒/文件')
    logger.info('=' * 60)


def main():
    """主程序入口"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='批量翻译文件工具')
    parser.add_argument(
        '--provider', '-p',
        type=str,
        choices=['akashml', 'deepseek', 'hyperbolic'],
        default='akashml',
        help='选择服务商: akashml、deepseek 或 hyperbolic (默认: akashml)'
    )
    args = parser.parse_args()
    
    # 批量翻译文件
    batch_translate(provider=args.provider)
    
    # 合并翻译后的文件
    merge_entrance(
        files_dir=str(PathConfig.WORK_DIR),
        delete_originals=True,
        backup=False
    )


if __name__ == '__main__':
    main()
