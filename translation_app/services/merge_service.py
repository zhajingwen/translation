#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档合并服务 - 合并小型翻译文件
"""

import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict

from translation_app.core.config import CharLimits, PathConfig
from translation_app.core.utils import count_chinese_characters


logger = logging.getLogger('FileMerge')


def natural_sort_key(path: Path) -> list:
    """
    自然排序键函数，支持数字前缀的正确排序
    """
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r'(\d+)', path.name)
    ]


def scan_and_filter_files(
    files_dir: Path,
    char_limit: int = None
) -> List[Tuple[Path, int]]:
    """
    扫描目录，筛选符合条件的文件
    """
    if char_limit is None:
        char_limit = CharLimits.SMALL_FILE_LIMIT

    logger.info(f"扫描目录: {files_dir}")

    # 检查目录是否存在
    if not files_dir.exists():
        logger.error(f"目录不存在: {files_dir}")
        return []

    # 查找所有 *translated.txt 文件
    pattern = "*translated.txt"
    all_files = list(files_dir.glob(pattern))
    logger.info(f"找到 {len(all_files)} 个 translated.txt 文件")

    if not all_files:
        logger.warning("未找到任何 translated.txt 文件")
        return []

    # 统计每个文件的中文字符数
    file_char_counts = []
    for file_path in all_files:
        try:
            # 尝试多种编码读取文件
            content = None
            for encoding in ['utf-8', 'gbk', 'gb2312']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                logger.warning(f"无法读取文件（编码错误）: {file_path.name}")
                continue

            # 统计中文字符数
            char_count = count_chinese_characters(content)
            file_char_counts.append((file_path, char_count))
            logger.debug(f"{file_path.name}: {char_count} 个中文字符")

        except Exception as e:
            logger.error(f"读取文件失败 {file_path.name}: {e}")
            continue

    # 筛选出中文字数 < char_limit 的文件
    filtered_files = [
        (path, count) for path, count in file_char_counts
        if count < char_limit
    ]

    # 按文件名自然排序
    filtered_files.sort(key=lambda x: natural_sort_key(x[0]))

    logger.info(f"筛选后: {len(filtered_files)} 个文件 (< {char_limit} 字)")

    # 显示筛选出的文件
    for path, count in filtered_files:
        logger.info(f"  - {path.name}: {count:,} 字")

    return filtered_files


def merge_files(
    file_list: List[Tuple[Path, int]],
    output_dir: Path,
    merge_limit: int = None
) -> List[Path]:
    """
    按中文字数限制合并文件
    """
    if merge_limit is None:
        merge_limit = CharLimits.MERGE_FILE_LIMIT

    logger.info(f"开始合并文件，限制: {merge_limit:,} 字")

    if not file_list:
        logger.warning("没有文件需要合并")
        return []

    # 创建输出目录
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"输出目录: {output_dir}")
    except Exception as e:
        logger.error(f"创建输出目录失败: {e}")
        return []

    merged_files = []
    combined_index = 1
    current_content = []
    current_chars = 0
    current_file_names = []

    for file_path, char_count in file_list:
        # 如果添加当前文件后会超过限制
        if current_chars > 0 and current_chars + char_count > merge_limit:
            # 保存当前合并文件
            output_file = output_dir / f"combined_{combined_index}.txt"
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n\n'.join(current_content))

                logger.info(
                    f"生成: {output_file.name} "
                    f"({current_chars:,} 字, 包含 {len(current_file_names)} 个文件)"
                )
                logger.info(f"  包含文件: {', '.join(current_file_names)}")

                merged_files.append(output_file)

                # 重置状态，开始新的合并文件
                combined_index += 1
                current_content = []
                current_chars = 0
                current_file_names = []

            except Exception as e:
                logger.error(f"保存合并文件失败 {output_file}: {e}")
                return merged_files

        # 读取文件内容并添加到当前合并集合
        try:
            # 尝试多种编码读取
            content = None
            for encoding in ['utf-8', 'gbk', 'gb2312']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                logger.warning(f"无法读取文件（跳过）: {file_path.name}")
                continue

            # 直接添加文件内容
            current_content.append(content)
            current_chars += char_count
            current_file_names.append(file_path.name)

        except Exception as e:
            logger.error(f"读取文件失败 {file_path.name}: {e}")
            continue

    # 保存最后一个合并文件
    if current_content:
        output_file = output_dir / f"combined_{combined_index}.txt"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(current_content))

            logger.info(
                f"生成: {output_file.name} "
                f"({current_chars:,} 字, 包含 {len(current_file_names)} 个文件)"
            )
            logger.info(f"  包含文件: {', '.join(current_file_names)}")

            merged_files.append(output_file)

        except Exception as e:
            logger.error(f"保存合并文件失败 {output_file}: {e}")

    return merged_files


def delete_original_files(
    file_list: List[Tuple[Path, int]],
    backup: bool = True
) -> Dict[str, bool]:
    """
    安全删除原始文件
    """
    if not file_list:
        logger.info("没有文件需要删除")
        return {}

    logger.info(f"准备删除 {len(file_list)} 个原始文件")

    # 备份文件
    backup_dir = None
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = PathConfig.BACKUP_DIR / timestamp

        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"备份目录: {backup_dir}")

            # 备份所有文件
            for file_path, _ in file_list:
                try:
                    shutil.copy2(file_path, backup_dir / file_path.name)
                    logger.debug(f"已备份: {file_path.name}")
                except Exception as e:
                    logger.error(f"备份失败 {file_path.name}: {e}")

            logger.info(f"已备份 {len(file_list)} 个文件到 {backup_dir}")

        except Exception as e:
            logger.error(f"创建备份目录失败: {e}")
            logger.warning("备份失败，取消删除操作")
            return {}

    # 删除文件
    delete_results = {}
    for file_path, _ in file_list:
        try:
            file_path.unlink()
            delete_results[file_path.name] = True
            logger.info(f"已删除: {file_path.name}")
        except Exception as e:
            delete_results[file_path.name] = False
            logger.error(f"删除失败 {file_path.name}: {e}")

    # 统计结果
    success_count = sum(1 for v in delete_results.values() if v)
    logger.info(f"删除完成: 成功 {success_count}/{len(file_list)}")

    return delete_results


def merge_entrance(
    files_dir: str = "files",
    delete_originals: bool = True,
    backup: bool = False
):
    """
    主流程：扫描 → 筛选 → 合并 → 删除（可选）
    """
    logger.info("=" * 80)
    logger.info("文档合并脚本启动")
    logger.info("=" * 80)

    # 转换为 Path 对象
    files_path = Path(files_dir)
    output_path = files_path / "combined"

    # 步骤1：扫描并筛选文件
    logger.info("\n步骤 1/4: 扫描并筛选文件")
    filtered_files = scan_and_filter_files(
        files_dir=files_path,
        char_limit=CharLimits.SMALL_FILE_LIMIT
    )

    if not filtered_files:
        logger.info("没有符合条件的文件，程序结束")
        return

    # 步骤2：合并文件
    logger.info("\n步骤 2/4: 合并文件")
    merged_files = merge_files(
        file_list=filtered_files,
        output_dir=output_path,
        merge_limit=CharLimits.MERGE_FILE_LIMIT
    )

    if not merged_files:
        logger.error("文件合并失败，程序结束")
        return

    # 步骤3：统计结果
    logger.info("\n步骤 3/4: 统计结果")
    total_chars = sum(count for _, count in filtered_files)
    logger.info(f"合并完成，生成 {len(merged_files)} 个文件")
    logger.info(f"总中文字数: {total_chars:,} 字")
    logger.info("生成的文件:")
    for merged_file in merged_files:
        logger.info(f"  - {merged_file}")

    # 步骤4：删除原文件（可选）
    if delete_originals:
        logger.info("\n步骤 4/4: 删除原文件")
        delete_original_files(
            file_list=filtered_files,
            backup=backup
        )
    else:
        logger.info("\n步骤 4/4: 跳过删除原文件（保留了源文件）")

    logger.info("\n" + "=" * 80)
    logger.info("文档合并脚本完成")
    logger.info("=" * 80)

