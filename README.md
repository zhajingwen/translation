# 电子书翻译工具

- 一个基于大语言模型的电子书翻译工具，支持将PDF、EPUB和TXT格式的文档翻译成中文，并提供多种翻译方式选择。
- 需要翻译的文件最好不要是EPUB格式，可能会出现抽取文本不全的情况

## 🚀 快速上手

### 5分钟快速开始

**第一步：安装依赖**
```bash
# 方法一：使用 pip（推荐新手）
pip install -r requirements.txt

# 方法二：使用 uv（更快，推荐）
uv sync
```

**第二步：设置API密钥**

**获取API密钥：**
- **DeepSeek API**（推荐）：访问 [DeepSeek平台](https://platform.deepseek.com) 注册账号并获取API密钥
- **OpenAI API**：访问 [OpenAI平台](https://platform.openai.com) 注册账号并获取API密钥

**设置环境变量：**
```bash
# DeepSeek API（推荐，性价比最高）
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# 或使用 OpenAI API
export OPENAI_API_KEY="your-openai-api-key"
```

**提示：** 如果不想每次设置环境变量，可以将密钥添加到 `~/.bashrc` 或 `~/.zshrc` 文件中（macOS/Linux），或使用 `.env` 文件（需要额外配置）。

**第三步：准备文件**
将待翻译的文件（PDF/EPUB/TXT）放入 `files/` 目录

**第四步：开始翻译**
```bash
# 单文件翻译（生成PDF+TXT）
python deepseek.py

# 或单文件翻译（仅生成TXT，更快）
python deepseek_nopdf.py

# 或批量翻译（自动处理files目录下所有txt文件）
python batch_deepseek.py
```

**第五步：查看结果**
翻译完成后，在 `files/` 目录下找到 `{原文件名} translated.txt` 和 `{原文件名} translated.pdf` 文件

### 首次使用必读

1. **选择翻译方式**：
   - 🏆 **推荐**：DeepSeek多线程（性价比最高，每100页约2毛钱）
   - 💰 **省钱**：OpenAI批处理（最便宜，但需等待24小时）
   - ⚡ **快速**：DeepSeek多线程（实时反馈，速度快）
   - 🔒 **隐私**：本地Ollama（完全免费，但需要本地资源）

2. **配置参数**：
   - 打开对应的Python文件（如 `deepseek.py`）
   - 修改 `source_origin_book_name` 为你的文件名
   - 根据需要调整 `TranslateConfig` 参数

3. **常见问题**：
   - 如果遇到API限流，减少 `max_workers` 线程数（建议3-5个）
   - 网络不稳定时，增加 `max_retries` 和 `retry_delay`
   - 翻译大文件前，建议先用小文件测试

## 功能特性

- 📚 支持PDF、EPUB、TXT格式的文档翻译
- 🚀 多种翻译方式：DeepSeek多线程（推荐）、DeepSeek批量翻译、OpenAI GPT-4o-mini、OpenAI批处理模式、本地Ollama模型
- 💰 成本优化：批处理模式可节省50%费用，DeepSeek最经济（每100页约2毛钱）
- 🔄 自动重试机制：提高翻译成功率，支持自定义重试次数和延迟
- ⚡ 多线程并行：DeepSeek版本支持多线程并发翻译，大幅提升速度
- 📦 批量处理：支持自动批量翻译files目录下的所有txt文件，翻译完成后自动清理
- 📄 多格式输出：同时生成TXT和PDF格式的翻译结果（deepseek_nopdf.py仅生成TXT）
- 🎨 中文排版：使用楷体字体，支持中文PDF生成

## 项目结构

```
translation/
├── deepseek.py            # DeepSeek 多线程翻译（生成PDF+TXT）
├── deepseek_nopdf.py     # DeepSeek 多线程翻译（仅生成TXT，不生成PDF）
├── batch_deepseek.py     # DeepSeek 批量翻译脚本（自动处理files目录下所有txt文件）
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
│   ├── *.txt             # 待翻译的文件
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
- 🎯 自动过滤空白页，提高翻译效率

**版本说明：**
- `deepseek.py`: 生成PDF和TXT两种格式的翻译结果（推荐需要PDF的场景）
- `deepseek_nopdf.py`: 仅生成TXT格式，不生成PDF（速度更快，适合只需要文本的场景）
- `batch_deepseek.py`: 批量翻译脚本，自动处理files目录下所有txt文件

**快速开始：**

**单文件翻译（生成PDF+TXT）：**
1. 打开 `deepseek.py` 文件
2. 修改第706行的文件名：
   ```python
   source_origin_book_name = "your_book.pdf"  # 或 .epub 或 .txt
   ```
3. 根据需要调整配置（第712-716行）：
   ```python
   config = TranslateConfig(
       max_workers=10,      # 线程数，建议3-10个（太多可能导致API限流）
       max_retries=10,      # 最大重试次数
       retry_delay=10       # 重试延迟时间(秒)
   )
   ```
4. 运行：
   ```bash
   python deepseek.py
   ```

**单文件翻译（仅生成TXT）：**
1. 打开 `deepseek_nopdf.py` 文件
2. 修改第569行的文件名：
   ```python
   source_origin_book_name = "your_book.txt"
   ```
3. 调整配置（第572-576行）
4. 运行：
   ```bash
   python deepseek_nopdf.py
   ```

**批量翻译（自动处理files目录下所有txt文件）：**
1. 将需要翻译的txt文件放入 `files/` 目录
2. 打开 `batch_deepseek.py` 文件，调整配置（第27-31行）
3. 运行：
   ```bash
   python batch_deepseek.py
   ```

**环境变量设置：**
```bash
# macOS/Linux
export DEEPSEEK_API_KEY="your-api-key"

# Windows PowerShell
$env:DEEPSEEK_API_KEY="your-api-key"

# Windows CMD
set DEEPSEEK_API_KEY=your-api-key
```

**配置参数说明：**

| 参数 | 说明 | 推荐值 | 注意事项 |
|------|------|--------|----------|
| `max_workers` | 线程数 | 3-10 | 太多可能导致API限流，建议从5开始测试 |
| `max_retries` | 最大重试次数 | 5-10 | 网络不稳定时建议增加到10 |
| `retry_delay` | 重试延迟(秒) | 5-10 | API限流时建议增加到10秒以上 |

**批量翻译功能说明：**
- ✅ 自动扫描 `files/` 目录下的所有 `.txt` 文件
- ✅ 跳过已翻译的文件（文件名以 `translated.txt` 结尾或已存在对应的翻译文件）
- ✅ 翻译完成后自动删除原始txt文件（请确保已备份）
- ✅ 支持日志记录，方便追踪翻译进度
- ✅ 失败时继续处理其他文件，不会中断整个批量任务

**注意事项：**
- ⚠️ DeepSeek API有速率限制，建议线程数不超过10个
- ⚠️ 网络不稳定时建议增加重试次数和延迟时间
- ⚠️ 翻译大文件时建议先测试小文件确认配置合适
- ⚠️ 批量翻译会自动删除原始文件，请确保已备份重要文件
- ⚠️ 如果翻译过程中有页面失败，程序会询问是否继续处理成功的页面

### 2. OpenAI 批处理翻译

**优势：**
- 💰 成本最低（比实时翻译便宜50%）
- 📦 适合大批量翻译
- 🔄 自动重试机制
- ⏱️ 最长24小时处理窗口

**使用方法：**
1. 打开 `chatgpt_batch.py` 文件
2. 修改文件路径和批处理任务ID：
   ```python
   source_file = "your_book.pdf"  # 或 "your_book.epub"
   batch_job_id = None  # 首次运行设为None，续传时填入任务ID
   ```
3. 运行：
   ```bash
   python chatgpt_batch.py
   ```

**环境变量设置：**
```bash
export OPENAI_API_KEY="your-api-key"
```

**流程说明：**
1. 首次运行：`batch_job_id = None`，系统会创建批处理任务并返回任务ID
2. 续传运行：将上次返回的任务ID填入，继续获取翻译结果
3. ⏱️ 批处理任务可能需要最多24小时完成，请耐心等待

### 3. OpenAI 实时翻译

**优势：**
- ⚡ 实时反馈，立即看到翻译结果
- 🎯 适合小文件或测试
- 🔍 可以逐页查看翻译效果

**使用方法：**
1. 打开 `chatgpt_translate.py` 文件
2. 修改文件路径：
   ```python
   source_origin_book_name = "your_book.pdf"  # 或 "your_book.epub"
   ```
3. 运行：
   ```bash
   python chatgpt_translate.py
   ```

**环境变量设置：**
```bash
export OPENAI_API_KEY="your-api-key"
```

### 4. 本地Ollama模型翻译

**优势：**
- 💸 完全免费，无需API费用
- 🔒 数据隐私保护，所有处理在本地完成
- 🌐 无需网络连接（下载模型后）
- ⚙️ 完全本地化处理

**注意：** 当前版本默认翻译成越南语，如需翻译成中文，请修改代码中的翻译提示词。

**前置条件：**

1. **安装Ollama**
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows
   # 访问 https://ollama.ai/download 下载安装包
   ```

2. **启动Ollama服务**
   ```bash
   ollama serve
   ```

3. **下载模型**
   ```bash
   ollama pull qwen2:7b
   # 或其他中文模型，如：
   # ollama pull qwen2.5:7b
   # ollama pull llama3.2:3b
   ```

**使用方法：**
1. 打开 `ollama_local_qwen2.py` 文件
2. 修改文件路径和模型名称：
   ```python
   source_origin_book_name = "your_book.pdf"  # 或 "your_book.epub"
   MODEL_NAME = "qwen2:7b"  # 根据你的模型调整
   ```
3. **如需翻译成中文**，找到翻译提示词部分（通常在 `translate` 方法中），修改为：
   ```python
   "将该文本翻译成中文: {text_origin}"
   ```
4. 运行：
   ```bash
   python ollama_local_qwen2.py
   ```

**性能建议：**
- 推荐使用至少8GB内存
- 使用GPU可以大幅提升速度
- 对于大文件，建议使用DeepSeek API（更快更便宜）

## 成本对比

| 翻译方式 | 成本（100页英文文档） | 目标语言 | 速度 | 特点 |
|---------|-------------------|---------|------|------|
| DeepSeek多线程 ⭐ | ~¥0.2 | 中文 | 快（多线程） | 性价比最高，推荐使用 |
| DeepSeek批量翻译 ⭐⭐ | ~¥0.2 | 中文 | 快（多线程+批量） | 自动批量处理，适合大量文件 |
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

### DeepSeek多线程翻译（deepseek.py）：
- `files/{原文件名} translated.txt`: 翻译后的文本文件
- `files/{原文件名} translated.pdf`: 翻译后的PDF文件（使用楷体字体）

### DeepSeek多线程翻译（deepseek_nopdf.py）：
- `files/{原文件名} translated.txt`: 翻译后的文本文件（不生成PDF）

### DeepSeek批量翻译（batch_deepseek.py）：
- `files/{原文件名} translated.txt`: 翻译后的文本文件（不生成PDF）
- 翻译完成后自动删除原始txt文件

### OpenAI实时翻译和本地Ollama翻译：
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

## 常见问题解答 (FAQ)

### Q1: 如何选择最适合的翻译方式？

**A:** 根据你的需求选择：
- **需要快速翻译，预算有限** → DeepSeek多线程（推荐）
- **需要批量处理大量文件** → DeepSeek批量翻译或OpenAI批处理
- **需要实时反馈，文件较小** → DeepSeek多线程或OpenAI实时
- **数据敏感，需要隐私保护** → 本地Ollama
- **预算充足，需要高质量** → OpenAI实时

### Q2: 翻译过程中断怎么办？

**A:** 
- **DeepSeek版本**：自动支持断点续传，失败的页面会跳过，可以重新运行继续翻译
- **OpenAI批处理**：保存返回的`batch_job_id`，下次运行时填入即可续传
- **其他版本**：可以使用`interupt`参数从指定页面继续

### Q3: 遇到API限流错误怎么办？

**A:** 
1. 减少`max_workers`线程数（建议降到3-5个）
2. 增加`retry_delay`延迟时间（建议10秒以上）
3. 增加`max_retries`重试次数（建议10次）
4. 等待一段时间后再试

### Q4: 翻译质量不满意怎么办？

**A:**
- 检查原始文件质量（OCR识别的PDF可能质量较差）
- 尝试调整翻译提示词
- 对于专业术语较多的文档，可以考虑使用GPT-4（成本更高）

### Q5: 批量翻译时如何跳过某些文件？

**A:**
- 将文件重命名，不以`.txt`结尾
- 或创建对应的`{文件名} translated.txt`文件
- 批量脚本会自动跳过已翻译的文件

### Q6: 如何修改翻译语言？

**A:**
- **DeepSeek/OpenAI版本**：修改`translate`方法中的提示词，将"翻译成中文"改为目标语言
- **Ollama版本**：同样修改提示词，并确保使用的模型支持目标语言

### Q7: 为什么EPUB文件翻译不全？

**A:**
- EPUB格式复杂，某些文件可能包含特殊结构
- 建议优先使用PDF或TXT格式
- 如果必须使用EPUB，可以先用工具转换为PDF

### Q8: 翻译后的PDF中文显示异常？

**A:**
- 确保`kaiti.ttf`字体文件存在于项目根目录
- 检查字体文件是否损坏
- 如果字体加载失败，程序会使用系统默认字体

## 故障排除

### DeepSeek API相关

**问题：API密钥错误**
```bash
# 检查环境变量是否正确设置
echo $DEEPSEEK_API_KEY

# 重新设置（macOS/Linux）
export DEEPSEEK_API_KEY="your-key"

# Windows PowerShell
$env:DEEPSEEK_API_KEY="your-key"
```

**问题：API限流**
- ✅ 减少`max_workers`到3-5个
- ✅ 增加`retry_delay`到10秒以上
- ✅ 增加`max_retries`到10次
- ✅ 等待一段时间后重试

**问题：API额度不足**
- 登录 [DeepSeek平台](https://platform.deepseek.com) 检查余额
- 充值后重新运行

### OpenAI API相关

**问题：API密钥错误**
```bash
# 检查环境变量
echo $OPENAI_API_KEY

# 重新设置
export OPENAI_API_KEY="your-key"
```

**问题：批处理任务长时间无响应**
- 批处理任务可能需要最多24小时
- 使用返回的`batch_job_id`定期检查状态
- 确保网络连接正常

**问题：实时翻译速度慢**
- 考虑使用DeepSeek API（更快更便宜）
- 或使用批处理模式（成本更低）

### 本地Ollama相关

**问题：Ollama服务未启动**
```bash
# 检查服务状态
curl http://localhost:11434/api/tags

# 启动服务
ollama serve
```

**问题：模型未找到**
```bash
# 查看已安装的模型
ollama list

# 下载模型
ollama pull qwen2:7b
```

**问题：翻译速度很慢**
- 使用GPU加速（如果支持）
- 使用更小的模型（如3B版本）
- 对于大文件，建议使用API服务

### 文件处理相关

**问题：PDF无法提取文本**
- 检查PDF是否为扫描版（图片格式）
- 某些加密的PDF需要先解密
- 尝试使用OCR工具先转换

**问题：文件路径错误**
- 确保文件在`files/`目录下
- 文件名不要包含特殊字符
- 使用相对路径，如`"your_file.pdf"`而不是`"files/your_file.pdf"`

**问题：磁盘空间不足**
- 清理不需要的文件
- 翻译大文件前检查磁盘空间
- 考虑只生成TXT格式（使用`deepseek_nopdf.py`）

### 字体相关问题

**问题：PDF中文显示为方块**
- 确保`kaiti.ttf`文件存在于项目根目录
- 重新下载字体文件
- 检查字体文件权限

**问题：字体加载失败**
- 程序会自动使用系统默认字体
- 可以手动指定其他中文字体路径

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

### v2.2.0 (最新)
- 📚 完善README文档，添加快手上手指引
- 📖 新增详细的使用说明和常见问题解答
- 🔧 优化配置说明，添加参数表格
- 🐛 改进错误处理和故障排除指南
- 📝 更新所有翻译方式的使用说明

### v2.1.0
- ✨ 新增DeepSeek批量翻译脚本（batch_deepseek.py）
- 📦 支持自动批量处理files目录下的所有txt文件
- 🗑️ 批量翻译完成后自动删除原始文件
- 📝 新增deepseek_nopdf.py版本（仅生成TXT，不生成PDF）
- 📊 增强日志记录功能
- 🔄 改进批量翻译的错误处理，失败时继续处理其他文件

### v2.0.0
- ✨ 新增DeepSeek多线程翻译支持
- 🚀 支持TXT格式文档翻译
- ⚡ 多线程并行翻译大幅提升速度
- 🔄 智能重试机制和错误处理
- 📊 实时进度跟踪和失败统计
- 🎯 空白页自动过滤功能
- 🛡️ 改进EPUB文件解析，支持多种MIME类型
- 🔧 优化PDF文本清理，提高生成质量

### v1.1.0
- 添加OpenAI批处理模式支持
- 添加本地Ollama支持（默认越南语）
- 优化中文PDF生成
- 改进字体加载错误处理

### v1.0.0
- 初始版本
- 支持PDF/EPUB翻译
- 支持OpenAI实时翻译
- 基础的中文PDF生成功能
