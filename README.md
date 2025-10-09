# 电子书翻译工具

一个基于大语言模型的电子书翻译工具，支持将PDF和EPUB格式的电子书翻译成中文，并提供多种翻译方式选择。

## 功能特性

- 📚 支持PDF和EPUB格式的电子书翻译
- 🤖 多种翻译方式：OpenAI GPT-4o-mini、本地Ollama模型
- 💰 成本优化：批处理模式可节省50%费用
- 🔄 断点续传：支持翻译中断后从指定页面继续
- 📄 多格式输出：同时生成TXT和PDF格式的翻译结果
- 🎨 中文排版：使用楷体字体，支持中文PDF生成

## 项目结构

```
translation/
├── deepseek.py            # DeepSeek 多线程翻译（推荐）
├── chatgpt_translate.py   # OpenAI GPT-4o-mini 实时翻译
├── chatgpt_batch.py       # OpenAI 批处理翻译
├── ollama_local_qwen2.py  # 本地Ollama模型翻译
├── requirements.txt       # 项目依赖
├── pyproject.toml         # 项目配置
├── uv.lock               # 依赖锁定文件
├── kaiti.ttf             # 中文字体文件
├── kaiti.pkl             # 字体缓存文件
├── kaiti.cw127.pkl       # 字体缓存文件
├── files/                 # 翻译文件存储目录（批处理模式）
└── README.md             # 项目说明文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

### 依赖包说明

- `beautifulsoup4`: HTML解析
- `fpdf2`: PDF生成
- `ebooklib`: EPUB文件处理
- `PyPDF2`: PDF文件读取
- `openai`: OpenAI API调用
- `retry`: 重试机制

## 使用方法

### 1. DeepSeek 多线程翻译（推荐）

**优势：**
- 多线程并行翻译，大幅提升翻译速度
- 成本低廉（每100页约2毛钱）
- 支持PDF、EPUB、TXT格式
- 自动重试机制，提高翻译成功率

**启动方式：**
```bash
python deepseek.py
```

**环境变量设置：**
```bash
export DEEPSEEK_API_KEY="your-api-key"
```

**配置说明：**
- 修改 `deepseek.py` 中的 `source_origin_book_name` 为要翻译的文件名
- 根据需要调整 `TranslateConfig` 参数：
  - `max_workers`: 线程数，建议3-10个（太多可能导致API限流）
  - `max_retries`: 重试次数，默认3次
  - `retry_delay`: 重试延迟，默认1秒

### 2. OpenAI 批处理翻译

**优势：**
- 成本最低（比实时翻译便宜50%）
- 适合大批量翻译
- 自动重试机制

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

### 2. OpenAI 实时翻译

**优势：**
- 实时反馈
- 适合小文件或测试

```python
# 修改 chatgpt_translate.py 中的文件路径
source_origin_book_name = "your_book.pdf"  # 或 "your_book.epub"
Translate(source_origin_book_name).run()
```

### 3. 本地Ollama模型翻译

**优势：**
- 完全免费
- 数据隐私保护
- 无需网络连接

**注意：** 当前版本默认翻译成越南语，如需翻译成中文，请修改代码中的翻译提示词。

**前置条件：**
1. 安装并启动Ollama
2. 下载qwen2:7b模型：`ollama pull qwen2:7b`

```python
# 修改 ollama_local_qwen2.py 中的文件路径和模型名称
source_origin_book_name = "your_book.pdf"  # 或 "your_book.epub"
MODEL_NAME = "qwen2:7b"  # 根据你的模型调整
# 注意：如需翻译成中文，请修改第163行的提示词
Translate(source_origin_book_name).run()
```

## 成本对比

| 翻译方式 | 成本（833页英文文档） | 目标语言 | 特点 |
|---------|-------------------|---------|------|
| DeepSeek多线程 | ~¥1.6 | 中文 | 多线程加速，性价比高 |
| OpenAI批处理 | ~¥1.4 | 中文 | 最便宜，适合大批量 |
| OpenAI实时 | ~¥3 | 中文 | 实时反馈，适合小文件 |
| 本地Ollama | ¥0 | 越南语 | 完全免费，需要本地部署 |

## 断点续传

如果翻译过程中断，可以指定从特定页面继续：

```python
# 从第50页开始继续翻译
text = translate.extract_text_from_pdf_translate(interupt=50)
```

## 输出文件

翻译完成后会生成以下文件：

### OpenAI 实时翻译和本地Ollama翻译：
- `output_translated.txt`: 翻译后的文本文件
- `output_translated.pdf`: 翻译后的PDF文件（使用楷体字体）

### OpenAI 批处理翻译：
- `files/{原文件名}.txt`: 翻译后的文本文件
- `files/{原文件名}.pdf`: 翻译后的PDF文件（使用楷体字体）
- `files/batch_input.jsonl`: 批处理输入文件
- `files/batch_output.jsonl`: 批处理输出结果文件

## 注意事项

1. **文件格式**：目前支持PDF和EPUB格式
2. **字体支持**：PDF输出使用楷体字体，确保中文字符正确显示
3. **API限制**：OpenAI API有速率限制，大批量翻译建议使用批处理模式
4. **本地模型**：使用Ollama需要足够的本地计算资源
5. **文件大小**：建议单次翻译的文档不要过大，避免内存溢出
6. **翻译语言**：本地Ollama模型默认翻译成越南语，如需中文请修改代码中的提示词

## 故障排除

### OpenAI API相关
- 确保API密钥正确设置
- 检查API额度是否充足
- 网络连接是否正常

### 本地Ollama相关
- 确保Ollama服务正在运行：`ollama serve`
- 检查模型是否正确下载：`ollama list`
- 确认模型名称与代码中的一致

### 文件处理相关
- 确保PDF/EPUB文件没有损坏
- 检查文件路径是否正确
- 确认有足够的磁盘空间存储输出文件

## 开发说明

### 核心类说明

- `Translate`: 主要翻译类，处理文件解析和翻译逻辑
- `PDF`: PDF生成类，支持中文字体
- `Topdf`: PDF转换工具类

### 扩展开发

如需添加新的翻译服务或文件格式支持，可以：

1. 继承`Translate`类
2. 实现`translate()`方法
3. 添加相应的文件解析方法

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 更新日志

- v1.0.0: 初始版本，支持PDF/EPUB翻译
- 添加OpenAI批处理模式（chatgpt_batch.py）
- 添加本地Ollama支持（ollama_local_qwen2.py，默认翻译成越南语）
- 优化中文PDF生成
- 重构文件结构，统一命名规范