#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务商配置模块

统一管理所有 LLM 服务商的配置信息：
- AkashML
- DeepSeek
- Hyperbolic
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderConfig:
    """服务商配置类"""
    
    name: str
    api_base_url: str
    model: str
    api_key: Optional[str] = None
    
    def __post_init__(self):
        """验证配置"""
        if not self.api_key:
            raise ValueError(f"{self.name} API Key 未设置，请设置环境变量")


class Providers:
    """服务商配置管理"""
    
    # 支持的服务商列表
    SUPPORTED_PROVIDERS = ['akashml', 'deepseek', 'hyperbolic']
    
    @staticmethod
    def get_akashml_config() -> ProviderConfig:
        """获取 AkashML 配置"""
        return ProviderConfig(
            name='AkashML',
            api_base_url='https://api.akashml.com/v1',
            model='Qwen/Qwen3-30B-A3B',
            api_key=os.environ.get('AKASHML_API_KEY')
        )
    
    @staticmethod
    def get_deepseek_config() -> ProviderConfig:
        """获取 DeepSeek 配置"""
        return ProviderConfig(
            name='DeepSeek',
            api_base_url='https://api.deepseek.com',
            model='deepseek-chat',
            api_key=os.environ.get('DEEPSEEK_API_KEY')
        )
    
    @staticmethod
    def get_hyperbolic_config() -> ProviderConfig:
        """获取 Hyperbolic 配置"""
        return ProviderConfig(
            name='Hyperbolic',
            api_base_url='https://api.hyperbolic.xyz/v1',
            model='openai/gpt-oss-20b',
            api_key=os.environ.get('HYPERBOLIC_API_KEY')
        )
    
    @classmethod
    def get_provider_config(cls, provider: str) -> ProviderConfig:
        """
        根据服务商名称获取配置
        
        Args:
            provider: 服务商名称 ('akashml', 'deepseek', 'hyperbolic')
        
        Returns:
            ProviderConfig: 服务商配置对象
        
        Raises:
            ValueError: 不支持的服务商或 API Key 未设置
        """
        provider_lower = provider.lower()
        
        if provider_lower not in cls.SUPPORTED_PROVIDERS:
            raise ValueError(
                f"不支持的服务商: {provider}，"
                f"请选择: {', '.join(cls.SUPPORTED_PROVIDERS)}"
            )
        
        if provider_lower == 'akashml':
            return cls.get_akashml_config()
        elif provider_lower == 'deepseek':
            return cls.get_deepseek_config()
        elif provider_lower == 'hyperbolic':
            return cls.get_hyperbolic_config()
        else:
            raise ValueError(f"未实现的服务商: {provider}")


def get_provider(provider: str = 'akashml') -> ProviderConfig:
    """
    便捷函数：获取服务商配置
    
    Args:
        provider: 服务商名称，默认 'akashml'
    
    Returns:
        ProviderConfig: 服务商配置对象
    """
    return Providers.get_provider_config(provider)
