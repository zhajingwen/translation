# 文档翻译工具

一个功能强大的多线程文档翻译工具，支持 PDF、EPUB、TXT 格式的批量翻译，支持多个 LLM 服务商，具备智能文本切割、自动重试、进度跟踪等功能。

## 功能特性

### 核心功能

- ✅ **多格式支持**：支持 PDF、EPUB、TXT 三种文档格式
- ✅ **多线程并行翻译**：大幅提升翻译速度，可自定义线程数
- ✅ **智能文本切割**：根据句子边界智能切割文本，保持语义完整性
- ✅ **自动重试机制**：网络不稳定时自动重试，提高成功率
- ✅ **多服务商支持**：支持 AkashML、DeepSeek 和 Hyperbolic 三个 LLM 服务商（通过命令行参数选择）
- ✅ **批量处理**：自动扫描目录并批量翻译文件
- ✅ **文件合并**：自动合并小型翻译文件，便于管理
- ✅ **进度跟踪**：实时显示翻译进度和统计信息
- ✅ **智能文件检测**：自动检测中文文件并重命名，跳过已翻译文件

### 高级特性

- 智能空白页过滤（EPUB）
- 自然排序文件处理
- 翻译失败标记和保留原文
- 字符数统计和筛选
- 可选的备份和删除功能
- 自动跳过已存在翻译结果的文件
- 自动删除字符数不足的文件（< 1000 字符）

## 安装说明

### 环境要求

- Python >= 3.12

### 安装依赖

项目使用 `uv` 进行依赖管理：

```bash
# 如果还没有安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv sync
```

或者使用传统的 pip 安装：

```bash
pip install beautifulsoup4 ebooklib fpdf2 openai pypdf2 requests retry
```

### 环境变量配置

在使用前，需要设置相应服务商的 API Key：

```bash
# AkashML 服务
export AKASHML_API_KEY="your_akashml_api_key"

# DeepSeek 服务
export DEEPSEEK_API_KEY="your_deepseek_api_key"

# Hyperbolic 服务
export HYPERBOLIC_API_KEY="your_hyperbolic_api_key"
```

## 使用方法

### 1. 单文件翻译（job.py）

直接运行 `job.py` 进行单文件翻译：

```bash
# 使用 AkashML（默认）
python job.py

# 或指定服务商
python job.py --provider akashml
python job.py --provider deepseek
python job.py --provider hyperbolic
```

**重要提示**：
- 需要在 `job.py` 的 `__main__` 部分（第 905 行）修改 `source_origin_book_name` 变量来指定要翻译的文件
- 文件路径可以是相对路径，会自动处理 `files/` 前缀
- 翻译结果保存为 `原文件名 translated.txt` 格式

**作为模块使用**：

```python
from job import Translate, TranslateConfig

config = TranslateConfig(
    max_workers=5,           # 线程数
    max_retries=3,           # 重试次数
    retry_delay=1,           # 重试延迟（秒）
    chunk_size=8000,         # 文本切割阈值
    min_chunk_size=500,      # 最小切割长度
    api_timeout=60,          # API 超时时间
    api_base_url="https://api.akashml.com/v1",
    model="Qwen/Qwen3-30B-A3B",
    api_key=os.environ.get('AKASHML_API_KEY')
)

translator = Translate("your_file.pdf", config)
translator.run()
```

### 2. 批量翻译（batch.py）

批量翻译 `files/` 目录下的所有文件：

```bash
# 使用默认服务商（AkashML）
python batch.py

# 指定服务商
python batch.py --provider akashml
python batch.py --provider deepseek
python batch.py --provider hyperbolic
```

**批量翻译的自动化流程**：

1. 扫描 `files/` 目录下的所有 `.txt`、`.pdf`、`.epub` 文件
2. 自动跳过已翻译的文件（文件名以 `translated.txt` 结尾）
3. 检测中文文件（中文字符占比 >= 30%），自动重命名为 `原文件名 translated.txt` 格式
4. 删除字符数 < 1000 的文件
5. 跳过已存在翻译结果的文件（如果已存在 `原文件名 translated.txt`，则删除原文件）
6. 依次翻译剩余文件
7. 翻译成功后删除原文件
8. 自动调用合并脚本合并小型文件（< 10万字）

### 3. 文件合并（merge_translated_files.py）

合并小型翻译文件：

```bash
python merge_translated_files.py
```

**合并规则**：

- 筛选出中文字数 < 10万字的 `*translated.txt` 文件
- 按文件名自然排序
- 合并成不超过 20万字的文件
- 保存到 `files/combined/` 目录
- 可选：删除原文件并备份

**作为模块使用**：

```python
from merge_translated_files import merge_entrance

merge_entrance(
    files_dir="files",          # 输入文件目录
    delete_originals=True,      # 是否删除原文件
    backup=True                 # 是否备份原文件
)
```

### 4. 本地 Ollama 测试（test/ollama_local_qwen2.py）

使用本地 Ollama 模型进行翻译（零成本）：

```bash
# 确保本地运行了 Ollama 服务
# 默认地址：http://localhost:11434

python test/ollama_local_qwen2.py
```

**注意**：需要在脚本中修改 `MODEL_NAME` 和 `source_origin_book_name` 变量。

## 配置说明

### TranslateConfig 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_workers` | int | 5 | 最大线程数，建议 3-10 个 |
| `max_retries` | int | 3 | 最大重试次数 |
| `retry_delay` | int | 1 | 重试延迟时间（秒） |
| `chunk_size` | int | 8000 | 文本切割阈值（字符数） |
| `min_chunk_size` | int | 500 | 最小切割长度（字符数） |
| `api_timeout` | int | 60 | API 超时时间（秒） |
| `api_base_url` | str | 必需 | API 基础 URL |
| `model` | str | 必需 | 模型名称 |
| `api_key` | str | 必需 | API 密钥 |

**注意**：`job.py` 和 `batch.py` 中的默认配置可能不同，请根据实际使用情况调整。

### 服务商配置

#### AkashML

```python
LLM_API_BASE_URL = 'https://api.akashml.com/v1'
LLM_MODEL = 'Qwen/Qwen3-30B-A3B'
LLM_API_KEY = os.environ.get('AKASHML_API_KEY')
```

#### DeepSeek

```python
LLM_API_BASE_URL = 'https://api.deepseek.com'
LLM_MODEL = 'deepseek-chat'
LLM_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
```

#### Hyperbolic

```python
LLM_API_BASE_URL = 'https://api.hyperbolic.xyz/v1'
LLM_MODEL = 'openai/gpt-oss-20b'
LLM_API_KEY = os.environ.get('HYPERBOLIC_API_KEY')
```

### 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `AKASHML_API_KEY` | AkashML API 密钥 | 使用 AkashML 时必需 |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 使用 DeepSeek 时必需 |
| `HYPERBOLIC_API_KEY` | Hyperbolic API 密钥 | 使用 Hyperbolic 时必需 |
| `LOG_LEVEL` | 日志级别（DEBUG/INFO/WARNING/ERROR） | 可选，默认 INFO |
| `LOG_SHOW_CONTENT` | 是否在日志中显示翻译内容预览（true/false） | 可选，默认 true |

## 项目结构

```
translation/
├── job.py                      # 核心翻译模块
├── batch.py                    # 批量翻译脚本
├── merge_translated_files.py   # 文件合并脚本
├── pyproject.toml              # 项目依赖配置
├── kaiti.ttf                   # 中文字体文件（保留，当前版本不生成PDF）
├── files/                      # 文件目录
│   ├── combined/              # 合并后的文件目录
│   └── ...                    # 待翻译和已翻译的文件
└── test/                       # 测试脚本
    ├── ollama_local_qwen2.py  # 本地 Ollama 翻译测试
    └── akash_llm.py           # AkashML API 测试
```

## 工作流程

### 单文件翻译流程

1. 读取源文件（PDF/EPUB/TXT）
2. 提取文本内容
3. 智能切割文本（保持句子完整性）
4. 多线程并行翻译各个文本块
5. 自动重试失败的翻译
6. 合并翻译结果
7. 保存为 TXT 文件

### 批量翻译流程

1. 扫描 `files/` 目录下的所有 `.txt`、`.pdf`、`.epub` 文件
2. 预处理筛选：
   - 跳过已翻译文件（文件名以 `translated.txt` 结尾）
   - 检测中文文件并重命名（中文字符占比 >= 30%）
   - 删除字符数 < 1000 的文件
   - 跳过已存在翻译结果的文件（删除原文件）
3. 依次翻译每个文件
4. 翻译成功后删除原文件
5. 自动调用合并脚本合并小型文件（< 10万字）

### 文件合并流程

1. 扫描所有 `*translated.txt` 文件
2. 统计每个文件的中文字符数
3. 筛选出 < 10万字的文件
4. 按文件名自然排序
5. 合并成不超过 20万字的文件
6. 保存到 `files/combined/` 目录
7. 可选：备份并删除原文件

## 注意事项

### 性能优化

- **线程数设置**：根据 API 服务商的并发限制调整，建议不超过 10 个线程
  - `batch.py` 默认使用 8 个线程
  - `job.py` 默认使用 1 个线程（可在代码中修改）
- **文本切割**：`chunk_size` 应根据模型的最大上下文长度调整
  - AkashML Qwen/Qwen3-30B-A3B：上下文限制 32K，`batch.py` 默认 `chunk_size=3000`
  - `job.py` 默认 `chunk_size=50000`，`min_chunk_size=30000`（适合大文件）
- **重试策略**：网络不稳定时建议增加重试次数和延迟时间
  - `batch.py` 默认 `max_retries=6`，`retry_delay=120` 秒
  - `job.py` 默认 `max_retries=6`，`retry_delay=120` 秒

### 错误处理

- 翻译失败的文本块会被标记为 `[翻译失败 - Chunk N]` 并保留原文
- 如果所有 chunk 翻译失败，不会保存文件
- 批量翻译时会记录失败的文件，不会中断整个流程

### 文件管理

- 翻译后的文件命名格式：`原文件名 translated.txt`
- 批量翻译会自动删除原文件（翻译成功后）
- 批量翻译会自动检测中文文件（中文字符占比 >= 30%），并重命名为 `原文件名 translated.txt` 格式
- 批量翻译会自动删除字符数 < 1000 的文件
- 批量翻译会自动跳过已存在翻译结果的文件（删除原文件）
- 合并脚本支持备份功能，删除前会先备份到 `files/.backup/` 目录（带时间戳）

### 格式支持

- **PDF**：使用 PyPDF2 提取文本，可能无法完美处理扫描版 PDF
- **EPUB**：自动过滤空白页和样式文件，只提取正文内容，支持多种 MIME 类型
- **TXT**：支持 UTF-8、GBK、GB2312 编码

**输出格式**：当前版本只生成 TXT 文件（`原文件名 translated.txt`），不生成 PDF 文件。

## 日志说明

项目使用 Python 标准 logging 模块，日志格式：

```
2025-01-01 12:00:00 [INFO] Translator: [任务] 开始翻译
```

日志级别可通过 `LOG_LEVEL` 环境变量控制：

```bash
export LOG_LEVEL=DEBUG  # 显示详细调试信息
export LOG_LEVEL=INFO   # 显示一般信息（默认）
export LOG_LEVEL=WARNING  # 只显示警告和错误
```

控制是否在日志中显示翻译内容预览（隐私保护）：

```bash
export LOG_SHOW_CONTENT=false  # 不显示翻译内容预览（默认 true）
```

## 示例

### 示例 1：翻译单个 PDF 文件

```python
from job import Translate, TranslateConfig
import os

config = TranslateConfig(
    max_workers=5,
    max_retries=3,
    retry_delay=2,
    chunk_size=8000,
    api_base_url="https://api.akashml.com/v1",
    model="Qwen/Qwen3-30B-A3B",
    api_key=os.environ.get('AKASHML_API_KEY')
)

translator = Translate("document.pdf", config)
translator.run()
```

### 示例 2：批量翻译并自动合并

```bash
# 将所有待翻译文件放入 files/ 目录
python batch.py --provider akashml

# 脚本会自动：
# 1. 翻译所有文件
# 2. 删除原文件
# 3. 合并小型翻译文件
```

## 常见问题

**Q: 翻译速度慢怎么办？**  
A: 可以适当增加 `max_workers` 线程数，但要注意 API 服务商的并发限制。

**Q: 某些文本块翻译失败？**  
A: 失败的内容会被标记并保留原文，可以检查日志查看失败原因，通常是网络问题或文本过长。

**Q: 如何调整文本切割大小？**  
A: 根据使用的模型上下文限制调整 `chunk_size` 和 `min_chunk_size` 参数。注意 `job.py` 和 `batch.py` 的默认配置不同，可根据需要修改。

**Q: 翻译后的文件在哪里？**  
A: 翻译结果保存在 `files/` 目录下，文件名格式为 `原文件名 translated.txt`。合并后的文件在 `files/combined/` 目录。

**Q: 批量翻译时为什么有些文件被跳过了？**  
A: 批量翻译会自动跳过以下文件：
- 文件名以 `translated.txt` 结尾的文件（已翻译）
- 中文字符占比 >= 30% 的 `.txt` 文件（会被重命名为 `translated.txt` 格式）
- 字符数 < 1000 的文件（会被删除）
- 已存在翻译结果的文件（原文件会被删除）

**Q: 如何选择不同的 LLM 服务商？**  
A: 使用 `--provider` 或 `-p` 参数：
```bash
python job.py --provider akashml    # 或 deepseek、hyperbolic
python batch.py --provider deepseek
```

## 许可证

本项目未指定许可证，请根据实际使用情况自行判断。

## 贡献

欢迎提交 Issue 和 Pull Request！
