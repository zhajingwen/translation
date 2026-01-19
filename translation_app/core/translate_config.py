#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译配置模块

定义翻译相关的配置类，采用组合模式分离不同职责
"""

from dataclasses import dataclass
from typing import Optional, Callable, Any


@dataclass
class ChunkingConfig:
    """
    文本切割配置
    
    参数:
        chunk_size: 文本切割阈值（字符数），默认8000
        min_chunk_size: 最小切割长度（字符数），默认500
    """
    chunk_size: int = 8000
    min_chunk_size: int = 500


@dataclass
class RetryConfig:
    """
    重试策略配置
    
    参数:
        max_retries: 最大重试次数，默认3
        retry_delay: 重试延迟时间（秒），默认1
    """
    max_retries: int = 3
    retry_delay: int = 1


@dataclass
class ApiConfig:
    """
    API 配置
    
    参数:
        api_base_url: API基础URL
        model: 模型名称
        api_key: API密钥
        timeout: API超时时间（秒），默认60
    """
    api_base_url: str
    model: str
    api_key: str
    timeout: int = 60


@dataclass
class TranslateConfig:
    """
    翻译总配置（组合配置）
    
    参数:
        max_workers: 最大线程数，默认5
        chunking: 文本切割配置
        retry: 重试策略配置
        api: API 配置
        client_factory: 可选的客户端工厂，用于替换默认 OpenAI 客户端
    """
    max_workers: int
    chunking: ChunkingConfig
    retry: RetryConfig
    api: ApiConfig
    client_factory: Optional[Callable[['TranslateConfig'], Any]] = None
    
    # 为了向后兼容，保留直接访问属性的接口
    @property
    def chunk_size(self) -> int:
        """文本切割阈值"""
        return self.chunking.chunk_size
    
    @property
    def min_chunk_size(self) -> int:
        """最小切割长度"""
        return self.chunking.min_chunk_size
    
    @property
    def max_retries(self) -> int:
        """最大重试次数"""
        return self.retry.max_retries
    
    @property
    def retry_delay(self) -> int:
        """重试延迟时间"""
        return self.retry.retry_delay
    
    @property
    def api_base_url(self) -> str:
        """API基础URL"""
        return self.api.api_base_url
    
    @property
    def model(self) -> str:
        """模型名称"""
        return self.api.model
    
    @property
    def api_key(self) -> str:
        """API密钥"""
        return self.api.api_key
    
    @property
    def api_timeout(self) -> int:
        """API超时时间"""
        return self.api.timeout


def create_translate_config(
    max_workers: int = 5,
    max_retries: int = 3,
    retry_delay: int = 1,
    chunk_size: int = 8000,
    min_chunk_size: int = 500,
    api_timeout: int = 60,
    api_base_url: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    client_factory: Optional[Callable[[TranslateConfig], Any]] = None
) -> TranslateConfig:
    """
    便捷函数：创建 TranslateConfig（向后兼容旧的扁平化参数）
    
    Args:
        max_workers: 最大线程数，默认5
        max_retries: 最大重试次数，默认3
        retry_delay: 重试延迟时间（秒），默认1
        chunk_size: 文本切割阈值（字符数），默认8000
        min_chunk_size: 最小切割长度（字符数），默认500
        api_timeout: API超时时间（秒），默认60
        api_base_url: API基础URL（必需）
        model: 模型名称（必需）
        api_key: API密钥（必需）
        client_factory: 可选的客户端工厂
    
    Returns:
        TranslateConfig: 翻译配置对象
    
    Raises:
        ValueError: API配置缺失
    """
    if api_key is None and client_factory is None:
        raise ValueError("api_key 参数是必需的，必须通过 TranslateConfig 传入")
    
    if api_base_url is None or model is None:
        raise ValueError("api_base_url 和 model 参数是必需的")
    
    return TranslateConfig(
        max_workers=max_workers,
        chunking=ChunkingConfig(chunk_size=chunk_size, min_chunk_size=min_chunk_size),
        retry=RetryConfig(max_retries=max_retries, retry_delay=retry_delay),
        api=ApiConfig(
            api_base_url=api_base_url,
            model=model,
            api_key=api_key or "",
            timeout=api_timeout
        ),
        client_factory=client_factory
    )
