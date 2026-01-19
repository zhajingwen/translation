#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档合并服务

提供文件扫描、合并、删除的编排逻辑
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Optional

from translation_app.core.config import CharLimits, PathConfig
from translation_app.core.file_analyzer import count_chinese_characters
from translation_app.domain.file_merger import FileMerger, MergeGroup


logger = logging.getLogger('MergeService')


def read_file_content(file_path: Path) -> Optional[str]:
    """
    读取文件内容，自动尝试多种编码
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件内容，读取失败返回 None
    """
    for encoding in ['utf-8', 'gbk', 'gb2312']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    return None


def scan_and_filter_files(
    files_dir: Path,
    char_limit: int = None
) -> List[Tuple[Path, int]]:
    """
    扫描目录，筛选符合条件的文件
    
    Args:
        files_dir: 目录路径
        char_limit: 字符数上限
    
    Returns:
        [(文件路径, 中文字符数), ...] 列表
    """
    if char_limit is None:
        char_limit = CharLimits.SMALL_FILE_LIMIT

    logger.info(f"扫描目录: {files_dir}")

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
            content = read_file_content(file_path)
            if content is None:
                logger.warning(f"无法读取文件（编码错误）: {file_path.name}")
                continue

            char_count = count_chinese_characters(content)
            file_char_counts.append((file_path, char_count))
            logger.debug(f"{file_path.name}: {char_count} 个中文字符")

        except Exception as e:
            logger.error(f"读取文件失败 {file_path.name}: {e}")
            continue

    # 使用 FileMerger 进行筛选和排序
    merger = FileMerger(merge_limit=CharLimits.MERGE_FILE_LIMIT)
    filtered_files = merger.filter_by_char_limit(file_char_counts, char_limit)
    filtered_files = merger.sort_files(filtered_files)

    logger.info(f"筛选后: {len(filtered_files)} 个文件 (< {char_limit} 字)")
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
    
    Args:
        file_list: [(文件路径, 字符数), ...] 列表
        output_dir: 输出目录
        merge_limit: 合并字数限制
    
    Returns:
        生成的合并文件路径列表
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

    # 使用 FileMerger 进行分组
    merger = FileMerger(merge_limit=merge_limit)
    groups = merger.group_files(file_list)

    # 写入合并文件
    merged_files = []
    for index, group in enumerate(groups, start=1):
        output_file = output_dir / f"combined_{index}.txt"
        
        try:
            # 读取组内所有文件内容
            contents = []
            for file_path, _ in group.files:
                content = read_file_content(file_path)
                if content is not None:
                    contents.append(content)
                else:
                    logger.warning(f"无法读取文件（跳过）: {file_path.name}")
            
            # 写入合并文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(contents))

            logger.info(
                f"生成: {output_file.name} "
                f"({group.total_chars:,} 字, 包含 {group.file_count} 个文件)"
            )
            logger.info(f"  包含文件: {', '.join(group.file_names)}")

            merged_files.append(output_file)

        except Exception as e:
            logger.error(f"保存合并文件失败 {output_file}: {e}")
            continue

    return merged_files


def delete_original_files(
    file_list: List[Tuple[Path, int]],
    backup: bool = True
) -> Dict[str, bool]:
    """
    安全删除原始文件
    
    Args:
        file_list: [(文件路径, 字符数), ...] 列表
        backup: 是否备份
    
    Returns:
        {文件名: 是否删除成功} 字典
    """
    if not file_list:
        logger.info("没有文件需要删除")
        return {}

    logger.info(f"准备删除 {len(file_list)} 个原始文件")

    # 备份文件
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = PathConfig.BACKUP_DIR / timestamp

        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"备份目录: {backup_dir}")

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

    success_count = sum(1 for v in delete_results.values() if v)
    logger.info(f"删除完成: 成功 {success_count}/{len(file_list)}")

    return delete_results


def merge_entrance(
    files_dir: str = "files",
    delete_originals: bool = True,
    backup: bool = False
):
    """
    合并服务入口：扫描 → 筛选 → 合并 → 删除（可选）
    
    Args:
        files_dir: 文件目录
        delete_originals: 是否删除原文件
        backup: 是否备份原文件
    """
    logger.info("=" * 80)
    logger.info("文档合并服务启动")
    logger.info("=" * 80)

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
        delete_original_files(file_list=filtered_files, backup=backup)
    else:
        logger.info("\n步骤 4/4: 跳过删除原文件（保留了源文件）")

    logger.info("\n" + "=" * 80)
    logger.info("文档合并服务完成")
    logger.info("=" * 80)
