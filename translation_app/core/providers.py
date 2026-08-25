#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务商配置模块

统一管理所有 LLM 服务商的配置信息：
- AkashML
- DeepSeek
- Hyperbolic
- AIHubMix
- OpenRouter
- Bonsai（本地 Bonsai-demo；默认对接 MLX server :8081，可改环境变量使用 llama-server :8080）
"""

import os
from dataclasses import dataclass
from pathlib import Path
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
    SUPPORTED_PROVIDERS = ['akashml', 'deepseek', 'hyperbolic', 'aihubmix', 'openrouter', 'bonsai']
    
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
            model='deepseek-v4-flash',
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

    @staticmethod
    def get_aihubmix_config() -> ProviderConfig:
        """
        获取 AIHubMix 配置

        AIHubMix（https://aihubmix.com）聚合了 OpenAI、Claude、Gemini、DeepSeek、Qwen 等
        500+ 模型，提供统一的 OpenAI 兼容接口。

        环境变量：
        - AIHUBMIX_API_KEY：必需，AIHubMix 的 API Key
        - AIHUBMIX_API_BASE_URL：可选，默认 ``https://aihubmix.com/v1``；
          若默认线路不可用，可改用备用线路 ``https://api.aihubmix.com/v1``
        - AIHUBMIX_MODEL：可选，默认 ``ox-alpha``；也可填写 AIHubMix 支持的任意其他模型 id
          （如 ``auto`` 交给路由器自动选模型）以固定使用某个模型
        """
        base = os.environ.get('AIHUBMIX_API_BASE_URL', 'https://aihubmix.com/v1').rstrip('/')
        model = os.environ.get('AIHUBMIX_MODEL', 'ox-alpha')
        return ProviderConfig(
            name='AIHubMix',
            api_base_url=base,
            model=model,
            api_key=os.environ.get('AIHUBMIX_API_KEY')
        )

    @staticmethod
    def get_openrouter_config() -> ProviderConfig:
        """
        获取 OpenRouter 配置

        OpenRouter（https://openrouter.ai）聚合了多家厂商的模型，提供统一的
        OpenAI 兼容接口。

        环境变量：
        - OPENROUTER_API_KEY：必需，OpenRouter 的 API Key
        - OPENROUTER_API_BASE_URL：可选，默认 ``https://openrouter.ai/api/v1``
        - OPENROUTER_MODEL：可选，默认 ``stealth/ox-alpha``；也可填写 OpenRouter
          支持的任意其他模型 id 以固定使用某个模型
        """
        base = os.environ.get('OPENROUTER_API_BASE_URL', 'https://openrouter.ai/api/v1').rstrip('/')
        model = os.environ.get('OPENROUTER_MODEL', 'stealth/ox-alpha')
        return ProviderConfig(
            name='OpenRouter',
            api_base_url=base,
            model=model,
            api_key=os.environ.get('OPENROUTER_API_KEY')
        )

    @staticmethod
    def get_bonsai_config() -> ProviderConfig:
        """
        本地 Bonsai（github.com/PrismML-Eng/Bonsai-demo）OpenAI 兼容端点。

        默认对接 ``./scripts/start_mlx_server.sh``（Apple Silicon，端口 8081）。
        若使用 llama-server（``./scripts/start_llama_server.sh``），请设置::

            export BONSAI_API_BASE_URL=http://127.0.0.1:8080/v1

        环境变量：
        - BONSAI_API_BASE_URL：API 根路径（须含 ``/v1``），默认 ``http://127.0.0.1:8081/v1``
        - BONSAI_API_MODEL：请求里的 ``model`` 字段；不设置则按下面规则生成。
        - BONSAI_DEMO_DIR：Bonsai-demo 仓库根目录的绝对路径。若设置，默认 ``model`` 为
          ``{BONSAI_DEMO_DIR}/models/Bonsai-{BONSAI_MODEL}-mlx``，与 ``curl .../v1/models`` 返回的 ``id`` 一致。
        - BONSAI_MODEL：与 demo 相同，``8B``（默认）、``4B``、``1.7B``；在未设置 ``BONSAI_API_MODEL`` 时使用。
        - BONSAI_API_KEY：可选；本地服务无鉴权时可不设（使用占位值）

        若未设置 ``BONSAI_DEMO_DIR`` 与 ``BONSAI_API_MODEL``，则 ``model`` 为相对路径 ``models/Bonsai-8B-mlx``（依赖服务端工作目录，易不匹配）；
        **推荐**设置 ``BONSAI_DEMO_DIR`` 或直接把 ``curl http://127.0.0.1:8081/v1/models`` 的 ``id`` 写入 ``BONSAI_API_MODEL``。

        注意：勿使用 ``gpt-3.5-turbo`` 等占位名，``mlx_lm`` 会当作 HuggingFace 仓库拉取并报错。
        """
        base = os.environ.get('BONSAI_API_BASE_URL', 'http://127.0.0.1:8081/v1').rstrip('/')
        if not base.endswith('/v1'):
            base = f'{base}/v1'
        model = os.environ.get('BONSAI_API_MODEL')
        if not model:
            size = os.environ.get('BONSAI_MODEL', '8B')
            rel = f'models/Bonsai-{size}-mlx'
            demo_dir = os.environ.get('BONSAI_DEMO_DIR', '').strip()
            if demo_dir:
                model = str((Path(demo_dir).expanduser().resolve() / rel))
            else:
                model = rel
        api_key = os.environ.get('BONSAI_API_KEY', 'local')
        return ProviderConfig(
            name='Bonsai (local)',
            api_base_url=base,
            model=model,
            api_key=api_key,
        )
    
    @classmethod
    def get_provider_config(cls, provider: str) -> ProviderConfig:
        """
        根据服务商名称获取配置
        
        Args:
            provider: 服务商名称 ('akashml', 'deepseek', 'hyperbolic', 'aihubmix', 'openrouter', 'bonsai')
        
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
        elif provider_lower == 'aihubmix':
            return cls.get_aihubmix_config()
        elif provider_lower == 'openrouter':
            return cls.get_openrouter_config()
        elif provider_lower == 'bonsai':
            return cls.get_bonsai_config()
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
