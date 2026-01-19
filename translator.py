#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译核心模块（兼容入口）
"""

from translation_app.domain.translator import TranslateConfig, Translator

Translate = Translator

__all__ = [
    'TranslateConfig',
    'Translator',
    'Translate',
]

