# 示例脚本

本目录包含各种 API 测试和使用示例。

## 文件说明

### akash_llm.py
AkashML API 的基本使用示例，展示如何调用 AkashML 的聊天完成接口。

### hyperbolic.py
Hyperbolic API 的基本使用示例，展示如何使用 Hyperbolic 进行文本翻译。

### ollama_local_qwen2.py
使用本地 Ollama 模型进行翻译的完整示例。

**特点**：
- 零成本翻译（使用本地模型）
- 支持 PDF 和 EPUB 格式
- 包含 PDF 生成功能
- 支持中断恢复

**使用前提**：
1. 本地安装并运行 Ollama
2. 下载 qwen2:7b 模型（或修改 MODEL_NAME）
3. 准备中文字体文件 kaiti.ttf（用于 PDF 生成）

**使用方法**：
```bash
# 修改脚本中的 source_origin_book_name 变量
python examples/ollama_local_qwen2.py
```

## 注意事项

这些脚本仅供参考和测试使用，实际项目应使用 `translation_app` 包中的模块。

如需进行生产环境的翻译任务，请使用：
- `python job.py <file>` - 单文件翻译
- `python batch.py` - 批量翻译
