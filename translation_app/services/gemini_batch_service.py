#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini Batch API 批处理服务

与 batch_service.py（多线程调用实时 chat.completions 接口）不同，
本模块对接 Gemini 官方异步批处理接口（Batch Mode）：
- submit：提取/切割 files/ 目录下的文件，打包提交一个批处理任务
- status：查询任务状态
- fetch：任务成功后拉取结果，按原文件重新拼接、保存、删除原文件
- run：submit + 轮询 + fetch 的一体化便捷入口

由于批处理任务是异步的（可能耗时数分钟到数小时），submit 与 fetch 被拆分为
独立步骤，任务清单（job 与文件的对应关系）持久化在
``files/.gemini_batch/`` 目录下，进程退出后仍可通过 job name 恢复。
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from google.genai.errors import APIError

from translation_app.core.config import (
    FileFormats,
    GeminiBatchDefaults,
    LogConfig,
    PathConfig,
)
from translation_app.core.file_ops import safe_delete
from translation_app.core.path_utils import get_translated_path
from translation_app.core.providers import get_provider
from translation_app.domain.extractors import get_extractor
from translation_app.domain.text_processor import TextProcessor
from translation_app.infra.gemini_batch_client import build_gemini_batch_client
from translation_app.services.file_preprocessor import FilePreprocessor
from translation_app.services.merge_service import merge_entrance


logger = logging.getLogger('GeminiBatchService')

SYSTEM_INSTRUCTION = "You are a translation assistant."
TRANSLATE_PROMPT_TEMPLATE = "将该文本翻译成简体中文（白话文）: {text}"

MANIFEST_DIR_NAME = '.gemini_batch'

TERMINAL_STATES = {
    'JOB_STATE_SUCCEEDED',
    'JOB_STATE_FAILED',
    'JOB_STATE_CANCELLED',
    'JOB_STATE_EXPIRED',
    'JOB_STATE_PARTIALLY_SUCCEEDED',
}
SUCCESS_STATES = {'JOB_STATE_SUCCEEDED', 'JOB_STATE_PARTIALLY_SUCCEEDED'}


# ================== 任务清单（manifest）持久化 ==================

def _manifest_dir() -> Path:
    d = PathConfig.WORK_DIR / MANIFEST_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def _manifest_path(job_name: str) -> Path:
    safe_name = job_name.replace('/', '_')
    return _manifest_dir() / f'{safe_name}.json'


def _save_manifest(manifest: dict):
    with open(_manifest_path(manifest['job_name']), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def _load_manifest(job_name: str) -> Optional[dict]:
    path = _manifest_path(job_name)
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _latest_manifest() -> Optional[dict]:
    files = sorted(_manifest_dir().glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return None
    with open(files[0], 'r', encoding='utf-8') as f:
        return json.load(f)


def _resolve_manifest(job_name: Optional[str]) -> Optional[dict]:
    manifest = _load_manifest(job_name) if job_name else _latest_manifest()
    if manifest is None:
        logger.error(f'[任务] 未找到任务清单: {job_name or "(最近一次提交的任务)"}')
    return manifest


def _delete_manifest(job_name: str):
    path = _manifest_path(job_name)
    if path.exists():
        path.unlink()


def _state_name(state) -> str:
    return getattr(state, 'name', str(state))


# ================== 提取 & 切割 ==================

def _collect_requests(files_to_process: List[Path]) -> (List[dict], List[dict]):
    """
    提取并切割文件，构造 Gemini Batch 内联请求列表

    Returns:
        (requests, file_infos)
        requests: 提交给 client.batches.create 的内联请求列表
        file_infos: [{"name": 文件名, "total_chunks": chunk数}, ...]
    """
    processor = TextProcessor(
        chunk_size=GeminiBatchDefaults.CHUNK_SIZE,
        min_chunk_size=GeminiBatchDefaults.MIN_CHUNK_SIZE
    )

    requests: List[dict] = []
    file_infos: List[dict] = []

    for file_path in files_to_process:
        try:
            extractor = get_extractor(str(file_path))
            content_list = extractor.extract_text()
            if not content_list:
                logger.warning(f'[提取] 未能提取到任何内容，跳过: {file_path.name}')
                continue
            chunks = processor.process_extracted_content(content_list)
            if not chunks:
                logger.warning(f'[提取] 切割结果为空，跳过: {file_path.name}')
                continue
        except Exception as e:
            logger.error(f'[提取] 提取文本失败，跳过 {file_path.name}: {e}')
            continue

        for i, chunk in enumerate(chunks):
            requests.append({
                'contents': [{'role': 'user', 'parts': [{'text': TRANSLATE_PROMPT_TEMPLATE.format(text=chunk)}]}],
                'config': {'system_instruction': SYSTEM_INSTRUCTION},
                'metadata': {'file': file_path.name, 'index': str(i)},
            })

        file_infos.append({'name': file_path.name, 'total_chunks': len(chunks)})
        logger.info(f'[提取] {file_path.name}: 切割成 {len(chunks)} 个 chunk')

    return requests, file_infos


# ================== 提交 ==================

def submit_batch(model: Optional[str] = None, display_name: Optional[str] = None) -> Optional[dict]:
    """
    提交一个 Gemini Batch 翻译任务

    Args:
        model: 覆盖使用的模型（默认使用 GEMINI_MODEL / 服务商默认模型）
        display_name: 任务显示名（默认按时间戳自动生成）

    Returns:
        任务清单 dict，失败或无文件可处理时返回 None
    """
    provider_config = get_provider('gemini')
    batch_model = model or provider_config.model

    PathConfig.ensure_dirs()
    current_dir = PathConfig.WORK_DIR

    all_files = []
    for ext in FileFormats.SUPPORTED_EXTENSIONS:
        all_files.extend(sorted(current_dir.glob(f"*{ext}")))

    if not all_files:
        logger.info('[任务] 未找到待翻译的文件（txt/pdf/epub），退出。')
        return None

    preprocessor = FilePreprocessor()
    files_to_process, preprocess_stats = preprocessor.preprocess_files(all_files)
    if preprocess_stats.total_skipped > 0:
        preprocessor.log_stats()

    if not files_to_process:
        logger.info('[任务] 没有需要处理的文件，退出。')
        return None

    requests, file_infos = _collect_requests(files_to_process)
    if not requests:
        logger.error('[任务] 未能生成任何翻译请求，终止提交')
        return None

    total_requests = len(requests)
    logger.info(f'[任务] 共 {len(file_infos)} 个文件，{total_requests} 个翻译请求，准备提交 Gemini Batch 任务')
    if total_requests > GeminiBatchDefaults.MAX_INLINE_REQUESTS:
        logger.warning(
            f'[任务] 请求数 ({total_requests}) 超过建议的内联批处理上限 '
            f'({GeminiBatchDefaults.MAX_INLINE_REQUESTS})，服务端可能会拒绝该任务'
        )

    client = build_gemini_batch_client(provider_config.api_key)
    job_display_name = display_name or f"translation-batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    try:
        batch_job = client.batches.create(
            model=batch_model,
            src=requests,
            config={'display_name': job_display_name}
        )
    except APIError as e:
        if e.status == 'FAILED_PRECONDITION':
            logger.error(
                '[任务] 提交失败 (400 FAILED_PRECONDITION)：该 API Key 所在的 Google 项目'
                '很可能未开通结算（billing）。Batch API 官方定价页明确标注 Free Tier '
                '不支持 Batch 模式，需要在 Google AI Studio / Cloud Console 为该项目'
                '启用付费结算后才能提交批处理任务。'
            )
        else:
            logger.error(f'[任务] 提交失败 ({e.status}): {e.message}')
        return None

    manifest = {
        'job_name': batch_job.name,
        'display_name': job_display_name,
        'model': batch_model,
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'total_requests': total_requests,
        'files': file_infos,
    }
    _save_manifest(manifest)

    logger.info(f'[任务] Gemini Batch 任务已提交: {batch_job.name}')
    logger.info(f'[任务] 当前状态: {_state_name(batch_job.state)}')
    logger.info('[任务] 稍后可用以下命令查询/拉取结果:')
    logger.info(f'  translate gemini-batch status --job {batch_job.name}')
    logger.info(f'  translate gemini-batch fetch --job {batch_job.name}')

    return manifest


# ================== 查询状态 ==================

def check_status(job_name: Optional[str] = None) -> Optional[str]:
    """
    查询批处理任务状态

    Args:
        job_name: 任务名（如 "batches/xxxxx"），不传则使用最近一次提交的任务

    Returns:
        任务状态名（如 "JOB_STATE_SUCCEEDED"），失败返回 None
    """
    manifest = _resolve_manifest(job_name)
    if manifest is None:
        return None
    job_name = manifest['job_name']

    provider_config = get_provider('gemini')
    client = build_gemini_batch_client(provider_config.api_key)

    job = client.batches.get(name=job_name)
    state_name = _state_name(job.state)
    logger.info(f'[查询] 任务 {job_name} 状态: {state_name}')

    stats = getattr(job, 'completion_stats', None)
    if stats:
        logger.info(
            f'[查询] 成功: {getattr(stats, "successful_count", "?")}, '
            f'失败: {getattr(stats, "failed_count", "?")}, '
            f'未完成: {getattr(stats, "incomplete_count", "?")}'
        )

    if job.error:
        logger.error(f'[查询] 任务错误: {job.error}')

    return state_name


# ================== 拉取结果 ==================

def fetch_results(job_name: Optional[str] = None, auto_merge: bool = True) -> bool:
    """
    拉取已完成批处理任务的结果，按原文件重新拼接、保存并删除原文件

    Args:
        job_name: 任务名，不传则使用最近一次提交的任务
        auto_merge: 是否在拉取完成后自动调用合并流程

    Returns:
        是否成功拉取并处理
    """
    manifest = _resolve_manifest(job_name)
    if manifest is None:
        return False
    job_name = manifest['job_name']

    provider_config = get_provider('gemini')
    client = build_gemini_batch_client(provider_config.api_key)

    job = client.batches.get(name=job_name)
    state_name = _state_name(job.state)

    if state_name not in SUCCESS_STATES:
        logger.warning(f'[拉取] 任务尚未成功完成，当前状态: {state_name}')
        return False

    dest = job.dest
    if dest is None or not dest.inlined_responses:
        logger.error('[拉取] 未找到内联响应结果（当前仅支持内联提交的批处理任务）')
        return False

    # 按文件名分组，index -> 译文
    grouped: Dict[str, Dict[int, str]] = {}
    failed_counts: Dict[str, int] = {}

    for item in dest.inlined_responses:
        meta = item.metadata or {}
        file_name = meta.get('file')
        index_str = meta.get('index')
        if file_name is None or index_str is None:
            logger.warning('[拉取] 响应缺少 metadata，已跳过')
            continue
        index = int(index_str)

        text = None
        if item.error is None and item.response is not None:
            text = item.response.text

        if not text:
            failed_counts[file_name] = failed_counts.get(file_name, 0) + 1
            text = f"\n[翻译失败 - Chunk {index + 1}]\n[/翻译失败]\n"

        grouped.setdefault(file_name, {})[index] = text

    success_files = 0
    for file_info in manifest['files']:
        file_name = file_info['name']
        total_chunks = file_info['total_chunks']
        chunk_map = grouped.get(file_name)

        if not chunk_map:
            logger.error(f'[拉取] 未找到文件的翻译结果: {file_name}')
            continue

        ordered_texts = [
            chunk_map.get(i, f"\n[翻译失败 - Chunk {i + 1}]\n[/翻译失败]\n")
            for i in range(total_chunks)
        ]
        merged_text = "\n\n".join(t for t in ordered_texts if t)

        source_path = PathConfig.WORK_DIR / file_name
        output_path = get_translated_path(source_path)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(merged_text)
            logger.info(f'[拉取] 已保存翻译结果: {output_path.name}')
        except Exception as e:
            logger.error(f'[拉取] 保存失败 {file_name}: {e}')
            continue

        if file_name in failed_counts:
            logger.warning(f'[拉取] {file_name} 有 {failed_counts[file_name]}/{total_chunks} 个 chunk 翻译失败')

        if source_path.exists():
            safe_delete(source_path)

        success_files += 1

    logger.info(f'[拉取] 完成，共处理 {success_files}/{len(manifest["files"])} 个文件')

    _delete_manifest(job_name)

    if auto_merge:
        if LogConfig.LOG_SHOW_CONTENT:
            logger.info('[任务] 启动文件合并流程')
        merge_entrance(files_dir=str(PathConfig.WORK_DIR), delete_originals=True, backup=False)

    return success_files > 0


# ================== 一体化：提交 + 轮询 + 拉取 ==================

def run_and_wait(
    model: Optional[str] = None,
    display_name: Optional[str] = None,
    poll_interval: Optional[int] = None,
    max_wait: Optional[int] = None,
    auto_merge: bool = True,
) -> bool:
    """
    提交任务后阻塞轮询，完成后自动拉取结果（阶段性打印进度）

    Args:
        model: 覆盖使用的模型
        display_name: 任务显示名
        poll_interval: 轮询间隔（秒），默认 GeminiBatchDefaults.POLL_INTERVAL
        max_wait: 最长等待时间（秒），None 表示无限等待
        auto_merge: 拉取完成后是否自动合并

    Returns:
        是否成功完成（提交/轮询/拉取全部成功）
    """
    poll_interval = poll_interval or GeminiBatchDefaults.POLL_INTERVAL

    manifest = submit_batch(model=model, display_name=display_name)
    if manifest is None:
        return False

    job_name = manifest['job_name']
    provider_config = get_provider('gemini')
    client = build_gemini_batch_client(provider_config.api_key)

    start_time = time.time()
    state_name = None

    while True:
        job = client.batches.get(name=job_name)
        state_name = _state_name(job.state)
        elapsed = time.time() - start_time
        logger.info(f'[等待] 任务 {job_name} 状态: {state_name} | 已等待 {elapsed:.0f}s')

        if state_name in TERMINAL_STATES:
            break

        if max_wait is not None and elapsed > max_wait:
            logger.warning(
                f'[等待] 超过最大等待时间 ({max_wait}s)，停止等待。'
                f'任务仍在后台运行，可稍后执行: translate gemini-batch fetch --job {job_name}'
            )
            return False

        time.sleep(poll_interval)

    if state_name not in SUCCESS_STATES:
        logger.error(f'[等待] 任务未成功完成，最终状态: {state_name}')
        return False

    return fetch_results(job_name=job_name, auto_merge=auto_merge)
