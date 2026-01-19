#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译核心模块

提供核心翻译功能：
- 多线程并行翻译
- 自动重试机制
- 进度跟踪
"""

import logging
import time
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import APITimeoutError, APIError

from translation_app.domain.extractors import get_extractor
from translation_app.domain.text_processor import TextProcessor
from translation_app.core.config import LogConfig, PathConfig
from translation_app.core.translate_config import TranslateConfig
from translation_app.core.path_utils import normalize_file_path, get_translated_path


logger = logging.getLogger('Translator')


class Translator:
    """翻译器类"""

    def __init__(self, source_file: str, config: TranslateConfig, work_dir: Optional[str] = None):
        """
        初始化翻译器

        Args:
            source_file: 需要翻译的文件名（支持相对路径，会自动处理 files/ 前缀）
            config: 翻译配置（TranslateConfig 实例）
            work_dir: 可选的工作目录覆盖（默认使用 PathConfig.WORK_DIR）
        """
        if config is None:
            raise ValueError("config 参数是必需的，必须传入 TranslateConfig 实例")

        self.config = config
        self.client = self._init_api_client()

        # 文件路径处理
        PathConfig.ensure_dirs()
        work_root = work_dir or str(PathConfig.WORK_DIR)
        self.file_path = normalize_file_path(source_file, work_root)
        self.output_txt = get_translated_path(self.file_path)

        # 文本处理器
        self.text_processor = TextProcessor(
            chunk_size=config.chunk_size,
            min_chunk_size=config.min_chunk_size
        )

        # 翻译结果
        self.text_list: List[Tuple[Optional[str], bool]] = []
        self.total_chunks = 0
        self.translate_start_time = 0
        self._last_progress_percent = 0

    def _init_api_client(self):
        """初始化 API 客户端"""
        if self.config.client_factory:
            return self.config.client_factory(self.config)

        from openai import OpenAI
        if not self.config.api_key:
            raise ValueError("api_key 参数不能为空")
        return OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base_url
        )

    def extract_text(self) -> Optional[List[str]]:
        """
        提取文本内容

        Returns:
            切割后的文本块列表，失败返回 None
        """
        try:
            # 获取对应的提取器
            extractor = get_extractor(str(self.file_path))

            # 提取原始内容
            content_list = extractor.extract_text()

            if not content_list:
                logger.error(f'[提取] 未能提取到任何内容: {self.file_path}')
                return None

            # 使用文本处理器切割内容
            chunks = self.text_processor.process_extracted_content(content_list)

            return chunks

        except Exception as e:
            logger.error(f'[提取] 提取文本失败: {e}')
            return None

    def translate(self, text_origin: str) -> Optional[str]:
        """
        调用 API 翻译文本

        Args:
            text_origin: 原始文本

        Returns:
            翻译结果，失败返回 None
        """
        try:
            # 仅在启用时打印内容预览（隐私保护）
            if LogConfig.LOG_SHOW_CONTENT:
                preview = text_origin[:100] + '...' if len(text_origin) > 100 else text_origin
                logger.debug(f'[翻译] 原文预览: {preview}')

            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "You are a translation assistant."},
                    {"role": "user", "content": f"将该文本翻译成中文: {text_origin}"}
                ],
                stream=False,
                timeout=self.config.api_timeout
            )
            return response.choices[0].message.content
        except ValueError as e:
            # API Key 配置错误
            logger.error(f'[翻译] 配置错误: {e}')
            raise  # 重新抛出，终止程序
        except APITimeoutError as e:
            logger.error(f'[翻译] API请求超时: {e}')
            return None
        except TimeoutError as e:
            logger.error(f'[翻译] API请求超时: {e}')
            return None
        except APIError as e:
            status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            if status_code:
                logger.error(f'[翻译] API错误 (状态码 {status_code}): {e}')
            else:
                logger.error(f'[翻译] API错误: {e}')
            return None
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f'[翻译] API异常 ({error_type}): {e}')
            return None

    def translate_chunk(self, chunk_data: Tuple[int, str]) -> Tuple[int, Optional[str], bool]:
        """
        翻译单个文本块

        Args:
            chunk_data: (chunk索引, chunk内容)

        Returns:
            (chunk索引, 翻译结果, 是否成功)
        """
        chunk_index, chunk_content = chunk_data
        total = self.total_chunks
        chunk_tag = f'[翻译][Chunk {chunk_index + 1}/{total}]'

        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    logger.warning(f'{chunk_tag} 重试 (第 {attempt + 1} 次)')
                    time.sleep(self.config.retry_delay)
                else:
                    logger.debug(f'{chunk_tag} 开始 ({len(chunk_content)} 字符)')

                chinese = self.translate(chunk_content)
                if chinese:
                    if LogConfig.LOG_SHOW_CONTENT:
                        result_preview = chinese[:100] + '...' if len(chinese) > 100 else chinese
                        logger.debug(f'{chunk_tag} 完成，译文预览: {result_preview}')
                    else:
                        logger.debug(f'{chunk_tag} 完成')
                    return chunk_index, chinese, True
                logger.warning(f'{chunk_tag} 失败 (第 {attempt + 1} 次)')

            except Exception as e:
                logger.error(f'{chunk_tag} 异常 (第 {attempt + 1} 次): {e}')

        # 翻译失败时，返回带标记的原文
        logger.error(f'{chunk_tag} 最终失败，已重试 {self.config.max_retries} 次')
        failed_content = f"\n[翻译失败 - Chunk {chunk_index + 1}]\n{chunk_content}\n[/翻译失败]\n"
        return chunk_index, failed_content, False

    def translate_chunks(self, chunks: List[str]) -> str:
        """
        多线程翻译所有文本块

        Args:
            chunks: 文本块列表

        Returns:
            合并后的翻译结果
        """
        self.total_chunks = len(chunks)
        self.translate_start_time = time.time()
        self._last_progress_percent = 0
        logger.info(f'[翻译] 开始任务，共 {self.total_chunks} 个chunk，线程数: {self.config.max_workers}')

        # 准备数据
        chunk_data_list = [(i, chunk) for i, chunk in enumerate(chunks)]

        # 初始化结果列表
        self.text_list = [(None, False)] * len(chunks)

        # 使用线程池进行翻译
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # 提交所有翻译任务
            future_to_chunk = {
                executor.submit(self.translate_chunk, chunk_data): chunk_data[0]
                for chunk_data in chunk_data_list
            }

            # 收集结果
            completed_count = 0
            failed_chunks = []

            for future in as_completed(future_to_chunk):
                try:
                    chunk_index, translated_text, success = future.result()
                    self.text_list[chunk_index] = (translated_text, success)
                    completed_count += 1

                    if not success:
                        failed_chunks.append(chunk_index + 1)

                    # 更新进度
                    self._update_progress(completed_count)

                except Exception as e:
                    logger.error(f'[翻译] 翻译任务异常: {e}')

        if failed_chunks:
            logger.warning(f'[翻译] 失败的chunk: {failed_chunks}')

        # 合并翻译结果
        merged_text = "\n\n".join([text for text, _ in self.text_list if text])
        return merged_text

    def _update_progress(self, completed_count: int):
        """更新进度显示"""
        progress_percent = int((completed_count / self.total_chunks) * 100)
        if progress_percent - self._last_progress_percent >= 5 or progress_percent == 100:
            elapsed = time.time() - self.translate_start_time
            logger.info(f'[翻译] 进度: {progress_percent}% | 已用时 {elapsed:.1f}s')
            self._last_progress_percent = progress_percent

    def save_result(self, result: str):
        """保存翻译结果到文件"""
        if not result:
            logger.error('[保存] 结果为空，跳过保存')
            return

        try:
            with open(self.output_txt, 'w', encoding='utf-8') as f:
                f.write(result)
            logger.info(f'[保存] 翻译结果已保存: {self.output_txt.name}')
        except Exception as e:
            logger.error(f'[保存] 保存失败: {e}')

    def run(self) -> bool:
        """
        执行完整翻译流程

        Returns:
            是否成功
        """
        # 提取文本
        chunks = self.extract_text()
        if not chunks:
            logger.error('[任务] 提取文本失败，终止任务')
            return False

        # 翻译文本
        translated_text = self.translate_chunks(chunks)
        if not translated_text:
            logger.error('[任务] 翻译失败，终止任务')
            return False

        # 保存结果
        self.save_result(translated_text)
        return True

