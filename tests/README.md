# 测试说明

## 测试结构

```
tests/
├── __init__.py
├── conftest.py              # pytest 配置和 fixtures
├── unit/                    # 单元测试
│   ├── __init__.py
│   ├── test_config.py       # 配置模块测试
│   ├── test_utils.py        # 工具函数测试
│   └── test_text_processor.py  # 文本处理器测试
├── integration/             # 集成测试
│   └── __init__.py
└── fixtures/                # 测试数据（待添加）
```

## 运行测试

### 安装测试依赖

```bash
pip install pytest pytest-cov
```

### 运行所有测试

```bash
pytest
```

### 运行特定测试

```bash
# 运行单元测试
pytest tests/unit/

# 运行特定文件
pytest tests/unit/test_config.py

# 运行特定测试类
pytest tests/unit/test_config.py::TestPathConfig

# 运行特定测试方法
pytest tests/unit/test_config.py::TestPathConfig::test_work_dir
```

### 查看测试覆盖率

```bash
pytest --cov=translation_app --cov-report=html
```

然后打开 `htmlcov/index.html` 查看详细的覆盖率报告。

## 测试分类

### 单元测试 (unit/)
测试单个函数或类的功能，不依赖外部资源。

### 集成测试 (integration/)
测试多个模块协作的功能，可能需要文件系统、网络等外部资源。

## 编写测试指南

1. **命名规范**：测试文件以 `test_` 开头，测试函数以 `test_` 开头
2. **使用 fixtures**：在 `conftest.py` 中定义可复用的测试数据和配置
3. **Mock 外部依赖**：使用 `pytest-mock` 或 `unittest.mock` mock API 调用
4. **测试覆盖**：确保核心逻辑有足够的测试覆盖
5. **测试隔离**：每个测试应该独立运行，不依赖其他测试的状态

## TODO

- [ ] 添加 extractor 测试（需要测试文件 fixtures）
- [ ] 添加 translator 测试（需要 mock OpenAI API）
- [ ] 添加集成测试
- [ ] 提高测试覆盖率到 80%+
