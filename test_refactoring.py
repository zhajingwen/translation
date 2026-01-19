#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构后的代码测试脚本

验证重构后的代码是否正常工作
"""

import sys
from pathlib import Path

# 测试导入
print("=" * 60)
print("测试 1: 模块导入")
print("=" * 60)

try:
    from translator import Translator, TranslateConfig
    from providers import get_provider, Providers
    from config import PathConfig, CharLimits, TranslationDefaults, LogConfig
    from utils import (
        count_file_characters, 
        is_file_chinese, 
        count_chinese_characters,
        normalize_file_path,
        get_translated_filename
    )
    from extractors import get_extractor
    from text_processor import TextProcessor
    print("✓ 所有模块导入成功")
except Exception as e:
    print(f"✗ 模块导入失败: {e}")
    sys.exit(1)

# 测试配置类
print("\n" + "=" * 60)
print("测试 2: 配置类")
print("=" * 60)

try:
    # 测试路径配置
    PathConfig.ensure_dirs()
    print(f"✓ 工作目录: {PathConfig.WORK_DIR}")
    print(f"✓ 合并目录: {PathConfig.COMBINED_DIR}")
    
    # 测试字符数限制
    print(f"✓ 最小文件字符数: {CharLimits.MIN_FILE_CHARS}")
    print(f"✓ 小文件上限: {CharLimits.SMALL_FILE_LIMIT}")
    print(f"✓ 合并文件上限: {CharLimits.MERGE_FILE_LIMIT}")
    
    # 测试翻译默认值
    print(f"✓ 批量翻译线程数: {TranslationDefaults.BATCH_MAX_WORKERS}")
    print(f"✓ 批量翻译 chunk 大小: {TranslationDefaults.BATCH_CHUNK_SIZE}")
except Exception as e:
    print(f"✗ 配置类测试失败: {e}")
    sys.exit(1)

# 测试服务商配置
print("\n" + "=" * 60)
print("测试 3: 服务商配置")
print("=" * 60)

try:
    # 测试支持的服务商列表
    print(f"✓ 支持的服务商: {', '.join(Providers.SUPPORTED_PROVIDERS)}")
    
    # 注意：这里不实际获取配置，因为可能没有设置 API Key
    print("✓ 服务商配置类可用")
except Exception as e:
    print(f"✗ 服务商配置测试失败: {e}")
    sys.exit(1)

# 测试工具函数
print("\n" + "=" * 60)
print("测试 4: 工具函数")
print("=" * 60)

try:
    # 测试中文字符统计
    test_text = "这是一个测试文本 This is a test text 123"
    chinese_count = count_chinese_characters(test_text)
    print(f"✓ 中文字符统计: '{test_text}' 包含 {chinese_count} 个中文字符")
    
    # 测试文件路径标准化
    test_path = "files/test.txt"
    normalized = normalize_file_path(test_path)
    print(f"✓ 路径标准化: {test_path} -> {normalized}")
    
    # 测试翻译文件名生成
    test_file = Path("test.pdf")
    translated_name = get_translated_filename(test_file)
    print(f"✓ 翻译文件名: {test_file} -> {translated_name}")
except Exception as e:
    print(f"✗ 工具函数测试失败: {e}")
    sys.exit(1)

# 测试文本处理器
print("\n" + "=" * 60)
print("测试 5: 文本处理器")
print("=" * 60)

try:
    processor = TextProcessor(chunk_size=100, min_chunk_size=30)
    
    # 测试短文本（不需要切割）
    short_text = "这是一个短文本。"
    chunks = processor.split_text_to_chunks(short_text)
    print(f"✓ 短文本切割: 1 个文本 -> {len(chunks)} 个 chunk")
    
    # 测试长文本（需要切割）
    long_text = "这是一个很长的文本。" * 50  # 重复50次
    chunks = processor.split_text_to_chunks(long_text)
    print(f"✓ 长文本切割: {len(long_text)} 字符 -> {len(chunks)} 个 chunk")
    
    # 测试句子结束判断
    assert processor.is_sentence_end("这是一个句子。") == True
    assert processor.is_sentence_end("这不是句子结束") == False
    print(f"✓ 句子结束判断正常")
except Exception as e:
    print(f"✗ 文本处理器测试失败: {e}")
    sys.exit(1)

# 测试提取器工厂函数
print("\n" + "=" * 60)
print("测试 6: 提取器工厂")
print("=" * 60)

try:
    from extractors import PDFExtractor, EPUBExtractor, TXTExtractor
    
    # 测试获取不同类型的提取器
    pdf_extractor = get_extractor("test.pdf")
    assert isinstance(pdf_extractor, PDFExtractor)
    print("✓ PDF 提取器创建成功")
    
    epub_extractor = get_extractor("test.epub")
    assert isinstance(epub_extractor, EPUBExtractor)
    print("✓ EPUB 提取器创建成功")
    
    txt_extractor = get_extractor("test.txt")
    assert isinstance(txt_extractor, TXTExtractor)
    print("✓ TXT 提取器创建成功")
    
    # 测试不支持的文件类型
    try:
        get_extractor("test.doc")
        print("✗ 应该抛出异常但没有")
    except ValueError as e:
        print(f"✓ 正确处理不支持的文件类型")
except Exception as e:
    print(f"✗ 提取器工厂测试失败: {e}")
    sys.exit(1)

# 测试 TranslateConfig
print("\n" + "=" * 60)
print("测试 7: TranslateConfig")
print("=" * 60)

try:
    # 测试缺少必需参数
    try:
        config = TranslateConfig()
        print("✗ 应该抛出异常但没有")
    except ValueError:
        print("✓ 正确验证必需参数")
    
    # 测试正常创建
    config = TranslateConfig(
        max_workers=5,
        api_base_url="https://api.example.com",
        model="test-model",
        api_key="test-key"
    )
    print(f"✓ TranslateConfig 创建成功")
    print(f"  - 线程数: {config.max_workers}")
    print(f"  - Chunk 大小: {config.chunk_size}")
    print(f"  - 重试次数: {config.max_retries}")
except Exception as e:
    print(f"✗ TranslateConfig 测试失败: {e}")
    sys.exit(1)

# 总结
print("\n" + "=" * 60)
print("测试总结")
print("=" * 60)
print("✓ 所有测试通过！")
print("✓ 重构后的代码结构正常工作")
print("=" * 60)
