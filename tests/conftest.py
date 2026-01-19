#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest 配置文件
"""

import pytest
from pathlib import Path


@pytest.fixture
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_text():
    """示例文本"""
    return """这是一段示例文本。包含多个句子。
    这是第二段文本，用于测试文本处理功能。
    
    第三段包含更多内容，用来验证切割逻辑是否正确。"""
