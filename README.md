# 电子书翻译工具

- 一个基于大语言模型的电子书翻译工具，支持将PDF、EPUB和TXT格式的文档翻译成中文，并提供多种翻译方式选择。
- 需要翻译的文件最好不要是EPUB格式，可能会出现抽取文本不全的情况

## 功能特性

- 📚 支持PDF、EPUB、TXT格式的文档翻译
- 🚀 多种翻译方式：DeepSeek多线程（推荐）、OpenAI GPT-4o-mini、OpenAI批处理模式、本地Ollama模型
- 💰 成本优化：批处理模式可节省50%费用，DeepSeek最经济（每100页约2毛钱）
- 🔄 自动重试机制：提高翻译成功率，支持自定义重试次数和延迟
- ⚡ 多线程并行：DeepSeek版本支持多线程并发翻译，大幅提升速度
- 📄 多格式输出：同时生成TXT和PDF格式的翻译结果
- 🎨 中文排版：使用楷体字体，支持中文PDF生成

## 项目结构

```
translation/
├── deepseek.py            # DeepSeek 多线程翻译（推荐，最新）
├── chatgpt_translate.py   # OpenAI GPT-4o-mini 实时翻译
├── chatgpt_batch.py       # OpenAI 批处理翻译
├── ollama_local_qwen2.py  # 本地Ollama模型翻译
├── requirements.txt       # 项目依赖
├── pyproject.toml         # 项目配置
├── uv.lock               # 依赖锁定文件
├── kaiti.ttf             # 中文字体文件
├── kaiti.pkl             # 字体缓存文件
├── kaiti.cw127.pkl       # 字体缓存文件
├── files/                 # 翻译文件存储目录
│   ├── *.pdf             # 待翻译的文件
│   ├── *.epub            # 待翻译的文件
│   └── * translated.txt  # 翻译结果（TXT格式）
└── README.md             # 项目说明文档
```

## 安装依赖

### 方法一：使用 pip
```bash
pip install -r requirements.txt
```

### 方法二：使用 uv（推荐，更快）
```bash
uv sync
```

### 依赖包说明

- `openai>=1.0.0`: OpenAI API客户端
- `requests>=2.28.0`: HTTP请求库
- `retry>=0.9.2`: 重试机制
- `PyPDF2>=3.0.0`: PDF文件处理
- `fpdf2>=2.7.0`: PDF生成
- `ebooklib>=0.18`: EPUB文件处理
- `beautifulsoup4>=4.11.0`: HTML解析

## 使用方法

### 1. DeepSeek 多线程翻译（推荐）⭐

**优势：**
- ✅ 性价比最高（每100页约2毛钱，比OpenAI便宜80%）
- ⚡ 多线程并行翻译，大幅提升翻译速度
- 🔄 智能重试机制，自动处理网络波动和API限流
- 📊 实时进度跟踪，支持失败页面统计
- 📝 支持PDF、EPUB、TXT格式

**启动方式：**
```bash
python deepseek.py
```

**环境变量设置：**
```bash
export DEEPSEEK_API_KEY="your-api-key"
```

**配置说明：**
在 `deepseek.py` 文件中修改配置：

```python
# 1. 设置要翻译的文件
source_origin_book_name = "your_book.pdf"  # 或 .epub 或 .txt

# 2. 配置翻译参数
config = TranslateConfig(
    max_workers=10,      # 线程数，建议3-10个（太多可能导致API限流）
    max_retries=10,      # 最大重试次数
    retry_delay=10       # 重试延迟时间(秒)
)
```

**注意事项：**
- DeepSeek API有速率限制，建议线程数不超过10个
- 网络不稳定时建议增加重试次数和延迟时间
- 翻译大文件时建议先测试小文件确认配置合适

### 2. OpenAI 批处理翻译

**优势：**
- 💰 成本最低（比实时翻译便宜50%）
- 📦 适合大批量翻译
- 🔄 自动重试机制
- ⏱️ 最长24小时处理窗口

**使用方法：**
```python
# 修改 chatgpt_batch.py 中的文件路径
source_file = "your_book.pdf"  # 或 "your_book.epub"
batch_job_id = None  # 首次运行设为None，续传时填入任务ID
Translate(source_file).run(batch_job_id)
```

**环境变量设置：**
```bash
export OPENAI_API_KEY="your-api-key"
```

**流程说明：**
1. 首次运行：`batch_job_id = None`，系统会创建批处理任务并返回任务ID
2. 续传运行：将上次返回的任务ID填入，继续获取翻译结果

### 3. OpenAI 实时翻译

**优势：**
- ⚡ 实时反馈
- 🎯 适合小文件或测试
- 🔍 可以逐页查看翻译效果

**使用方法：**
```python
# 修改 chatgpt_translate.py 中的文件路径
source_origin_book_name = "your_book.pdf"  # 或 "your_book.epub"
Translate(source_origin_book_name).run()
```

**环境变量设置：**
```bash
export OPENAI_API_KEY="your-api-key"
```

### 4. 本地Ollama模型翻译

**优势：**
- 💸 完全免费
- 🔒 数据隐私保护
- 🌐 无需网络连接
- ⚙️ 完全本地化处理

**注意：** 当前版本默认翻译成越南语，如需翻译成中文，请修改代码中的翻译提示词。

**前置条件：**
1. 安装并启动Ollama
```bash
# macOS
brew install ollama
ollama serve

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
```

2. 下载qwen2:7b模型
```bash
ollama pull qwen2:7b
```

**使用方法：**
```python
# 修改 ollama_local_qwen2.py 中的文件路径和模型名称
source_origin_book_name = "your_book.pdf"  # 或 "your_book.epub"
MODEL_NAME = "qwen2:7b"  # 根据你的模型调整

# 如需翻译成中文，修改第163行的提示词：
# 将 "将以下文本翻译成中文" 替换为相应的翻译指令

Translate(source_origin_book_name).run()
```

## 成本对比

| 翻译方式 | 成本（100页英文文档） | 目标语言 | 速度 | 特点 |
|---------|-------------------|---------|------|------|
| DeepSeek多线程 ⭐ | ~¥0.2 | 中文 | 快（多线程） | 性价比最高，推荐使用 |
| OpenAI批处理 | ~¥0.17 | 中文 | 慢（异步） | 最便宜，需24小时 |
| OpenAI实时 | ~¥0.36 | 中文 | 中 | 实时反馈 |
| 本地Ollama | ¥0 | 需修改 | 很慢 | 完全免费，需本地资源 |

*注：成本基于实际使用经验估算，实际费用可能因文档复杂度而异。*

## 断点续传

如果翻译过程中断，可以指定从特定页面继续：

### DeepSeek版本
自动完成断点续传，失败的页面会跳过，支持部分失败场景。

### 其他版本
```python
# 从第50页开始继续翻译
text = translate.extract_text_from_pdf_translate(interupt=50)
```

## 输出文件

翻译完成后会生成以下文件：

### DeepSeek多线程、OpenAI实时翻译和本地Ollama翻译：
- `files/{原文件名} translated.txt`: 翻译后的文本文件
- `files/{原文件名} translated.pdf`: 翻译后的PDF文件（使用楷体字体）

### OpenAI批处理翻译：
- `files/{原文件名}.txt`: 翻译后的文本文件
- `files/{原文件名}.pdf`: 翻译后的PDF文件（使用楷体字体）
- `files/batch_input.jsonl`: 批处理输入文件
- `files/batch_output.jsonl`: 批处理输出结果文件

## 高级配置

### DeepSeek多线程高级配置

```python
# 自定义配置示例
config = TranslateConfig(
    max_workers=5,       # 线程数（根据API限制调整）
    max_retries=5,       # 重试次数
    retry_delay=5        # 重试延迟（秒）
)
```

### 空白页过滤

DeepSeek版本已内置空白页过滤功能，会自动跳过：
- 空页面
- 只包含空白字符的页面
- 只包含控制字符的页面
- 纯标点符号页面

## 注意事项

1. **文件格式**：目前支持PDF、EPUB和TXT格式
2. **字体支持**：PDF输出使用楷体字体（kaiti.ttf），确保中文字符正确显示
3. **API限制**：
   - OpenAI API有速率限制，大批量翻译建议使用批处理模式
   - DeepSeek API也有限制，建议线程数3-10个
4. **本地模型**：使用Ollama需要足够的本地计算资源（推荐8GB+内存）
5. **文件大小**：建议单次翻译的文档不要过大，避免内存溢出
6. **翻译语言**：DeepSeek和OpenAI版本默认翻译成中文；本地Ollama版本需修改提示词
7. **网络稳定性**：建议在网络稳定的环境下使用，避免翻译中断

## 故障排除

### DeepSeek API相关
- 确保API密钥正确设置：`export DEEPSEEK_API_KEY="your-key"`
- 检查API额度是否充足
- 如果遇到限流，减少`max_workers`线程数
- 增加`max_retries`和`retry_delay`提高成功率

### OpenAI API相关
- 确保API密钥正确设置：`export OPENAI_API_KEY="your-key"`
- 检查API额度是否充足
- 检查网络连接是否正常
- 批处理模式需要等待最多24小时

### 本地Ollama相关
- 确保Ollama服务正在运行：`ollama serve`
- 检查模型是否正确下载：`ollama list`
- 确认模型名称与代码中的一致
- 检查本地资源是否充足

### 文件处理相关
- 确保PDF/EPUB文件没有损坏
- 检查文件路径是否正确
- 确认有足够的磁盘空间存储输出文件
- 某些加密的PDF可能无法提取文本

### 字体相关问题
- 确保`kaiti.ttf`文件存在于项目根目录
- 如果字体加载失败，会使用系统默认字体

## 性能优化建议

1. **选择合适的翻译方式**
   - 大批量文档：使用DeepSeek多线程或OpenAI批处理
   - 小文件测试：使用DeepSeek多线程或OpenAI实时
   - 隐私要求高：使用本地Ollama

2. **调整线程数**
   - DeepSeek API稳定：`max_workers=10`
   - 遇到限流：`max_workers=3-5`
   - 网络不稳定：`max_workers=5, max_retries=10`

3. **成本优化**
   - 优先选择DeepSeek（最便宜）
   - 大批量使用批处理模式
   - 测试时使用本地模型

## 开发说明

### 核心类说明

- `Translate`: 主要翻译类，处理文件解析和翻译逻辑
- `PDF`: PDF生成类，支持中文字体
- `Topdf`: PDF转换工具类
- `TranslateConfig`: 翻译配置类（DeepSeek版本）

### 扩展开发

如需添加新的翻译服务或文件格式支持，可以：

1. 继承`Translate`类
2. 实现`translate()`方法
3. 添加相应的文件解析方法

## 许可证

本项目采用MIT许可证。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 更新日志

### v2.0.0 (最新)
- ✨ 新增DeepSeek多线程翻译支持
- 🚀 支持TXT格式文档翻译
- ⚡ 多线程并行翻译大幅提升速度
- 🔄 智能重试机制和错误处理
- 📊 实时进度跟踪和失败统计
- 🎯 空白页自动过滤功能

### v1.1.0
- 添加OpenAI批处理模式支持
- 添加本地Ollama支持（默认越南语）
- 优化中文PDF生成

### v1.0.0
- 初始版本
- 支持PDF/EPUB翻译
- 支持OpenAI实时翻译
