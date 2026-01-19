#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务商配置模块（兼容入口）

此文件仅用于向后兼容，实际实现已移至 translation_app.core.providers
"""

from translation_app.core.providers import (
    ProviderConfig,
    Providers,
    get_provider,
)

__all__ = [
    'ProviderConfig',
    'Providers',
    'get_provider',
]
