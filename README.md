# Markdown Text Chunker Plugin

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/Biaoo/md-text-chunker)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Dify Plugin](https://img.shields.io/badge/Dify-Plugin-orange)](https://dify.ai)

[中文文档](#中文文档) | [English](#english)

---

## English

### Overview

An intelligent Markdown text chunking tool designed for RAG (Retrieval-Augmented Generation) systems. This plugin intelligently splits Markdown documents while preserving complete heading hierarchy and providing rich contextual metadata.

**GitHub Repository**: [https://github.com/Biaoo/md-text-chunker](https://github.com/Biaoo/md-text-chunker)

### Key Features

#### 1. **Intelligent Heading Hierarchy Preservation**
- Automatically extracts and maintains complete heading paths (e.g., `H1 > H2 > H3`)
- Each chunk includes its full heading context for better retrieval accuracy
- Supports configurable heading levels (H1-H6) for flexible chunking granularity

#### 2. **Hybrid Chunking Strategy**
- Combines semantic chunking (heading-based) with fixed-size chunking
- First splits at specified heading levels, then further divides oversized chunks
- Ensures chunks stay within size limits while respecting document structure

#### 3. **Optional LLM-Based Heading Enhancement**
- Uses LLM to analyze and correct heading hierarchy levels
- Particularly useful for documents with inconsistent heading structures
- Supports OpenAI-compatible API endpoints

#### 4. **Atomic Unit Protection**
- Preserves tables, mathematical formulas, and other atomic content units
- Prevents breaking critical content across chunks
- Ensures content integrity for technical and scientific documents

#### 5. **Rich Metadata Injection**
- Optional XML metadata with file title and heading paths
- Provides contextual information for downstream RAG systems
- Can be toggled on/off based on use case

#### 6. **Text Preprocessing**
- Converts literal `\n` to actual newlines
- Optional removal of extra whitespace
- Optional removal of URLs and email addresses

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `input_text` | string | Yes | - | The markdown text to chunk |
| `file_title` | string | No | - | Optional file title included in metadata |
| `heading_level` | number | No | 3 | Heading level for semantic chunking (1-6) |
| `add_metadata` | boolean | No | true | Whether to add XML metadata to chunks |
| `remove_extra_spaces` | boolean | No | false | Replace consecutive whitespace with single space |
| `remove_urls_emails` | boolean | No | false | Remove all URLs and email addresses |
| `enable_llm_enhancement` | boolean | No | false | Use LLM to correct heading hierarchy |
| `llm_api_base` | string | No | - | OpenAI-compatible API endpoint URL |
| `llm_api_key` | string | No | - | API key for LLM service |
| `llm_model` | string | No | gpt-3.5-turbo | Model name for heading enhancement |

### Output Format

#### With Metadata (default)

```markdown
<metadata>
<Title>Document Title</Title>
<Headings>Main Topic > Subsection > Detail</Headings>
</metadata>

[Chunk content here...]
```

#### Without Metadata

```markdown
[Chunk content here...]
```

### Use Cases

1. **RAG Knowledge Base Construction**
   - Split long documents while maintaining context
   - Rich metadata improves retrieval accuracy
   - Heading paths help users understand document structure

2. **Technical Documentation Processing**
   - Preserve tables and formulas
   - Maintain heading hierarchy for navigation
   - Support for complex document structures

3. **Scientific Paper Processing**
   - Handle mathematical formulas and tables
   - LLM enhancement corrects inconsistent heading levels
   - Configurable chunking for different paper sections

4. **Enterprise Document Management**
   - Consistent chunking across document types
   - Metadata for advanced search and filtering
   - Preprocessing options for clean text extraction

### Installation

1. Download the latest release from the repository
2. Install the plugin in your Dify instance
3. Configure the plugin parameters as needed

### Configuration Example

**Basic Usage:**

```yaml
input_text: "# Main Title\n## Subtitle\nContent here..."
heading_level: 3
add_metadata: true
```

**With LLM Enhancement:**

```yaml
input_text: "Your markdown content..."
heading_level: 2
enable_llm_enhancement: true
llm_api_base: "https://api.openai.com/v1/chat/completions"
llm_api_key: "your-api-key"
llm_model: "gpt-3.5-turbo"
```

### Technical Details

- **Max Chunk Size:** 2000 characters (fixed)
- **Chunk Overlap:** 0 (no overlap)
- **Chunking Strategy:** Hybrid (semantic + fixed-size)
- **Preserved Units:** Tables, mathematical formulas
- **Heading Levels:** 1-6 (H1-H6)

### Best Practices

1. **Heading Level Selection:**
   - Use H1 (level=1) for very long documents with clear top-level structure
   - Use H2-H3 (level=2-3) for most documents (recommended)
   - Use H4-H6 (level=4-6) for fine-grained chunking

2. **LLM Enhancement:**
   - Enable for documents with inconsistent heading structures
   - Particularly useful for converted PDFs or OCR documents
   - Adds processing time but improves quality

3. **Metadata Usage:**
   - Keep enabled for RAG systems (improves retrieval)
   - Disable for pure text processing or token count optimization
   - File title is optional but recommended for multi-document systems

### Troubleshooting

**Issue: Chunks are too large**
- Decrease `heading_level` to split at higher-level headings
- Check if document has proper heading hierarchy

**Issue: Heading paths are incomplete**
- Enable `enable_llm_enhancement` to correct heading levels
- Ensure input markdown uses proper heading syntax

**Issue: Tables or formulas are broken**
- This should not happen - atomic units are preserved by default
- Check if content is properly formatted as markdown table/formula

### License

MIT License

### Author

biaoo

---

## 中文文档

### 概述

专为 RAG（检索增强生成）系统设计的智能 Markdown 文本分块工具。该插件能够智能分割 Markdown 文档，同时保留完整的标题层级结构并提供丰富的上下文元数据。

**项目地址**: [https://github.com/Biaoo/md-text-chunker](https://github.com/Biaoo/md-text-chunker)

### 核心特性

#### 1. **智能标题层级保留**
- 自动提取并维护完整的标题路径（例如：`H1 > H2 > H3`）
- 每个分块都包含完整的标题上下文，提升检索准确性
- 支持可配置的标题层级（H1-H6），灵活控制分块粒度

#### 2. **混合分块策略**
- 结合语义分块（基于标题）和固定大小分块
- 首先在指定标题层级分割，然后进一步分割过大的块
- 在遵守文档结构的同时确保分块大小合理

#### 3. **可选的 LLM 标题增强**
- 使用 LLM 分析并修正标题层级结构
- 特别适用于标题结构不一致的文档
- 支持 OpenAI 兼容的 API 端点

#### 4. **原子单元保护**
- 保护表格、数学公式等原子内容单元
- 防止关键内容被分割到不同分块
- 确保技术和科学文档的内容完整性

#### 5. **丰富的元数据注入**
- 可选的 XML 元数据，包含文件标题和标题路径
- 为下游 RAG 系统提供上下文信息
- 可根据使用场景开启或关闭

#### 6. **文本预处理**
- 转换字面的 `\n` 为实际换行符
- 可选的多余空格移除
- 可选的 URL 和邮箱地址移除

### 参数说明

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `input_text` | string | 是 | - | 要分块的 Markdown 文本 |
| `file_title` | string | 否 | - | 可选的文件标题，包含在元数据中 |
| `heading_level` | number | 否 | 3 | 语义分块的标题层级（1-6） |
| `add_metadata` | boolean | 否 | true | 是否为分块添加 XML 元数据 |
| `remove_extra_spaces` | boolean | 否 | false | 将连续空格替换为单个空格 |
| `remove_urls_emails` | boolean | 否 | false | 移除所有 URL 和邮箱地址 |
| `enable_llm_enhancement` | boolean | 否 | false | 使用 LLM 修正标题层级 |
| `llm_api_base` | string | 否 | - | OpenAI 兼容的 API 端点 URL |
| `llm_api_key` | string | 否 | - | LLM 服务的 API 密钥 |
| `llm_model` | string | 否 | gpt-3.5-turbo | 用于标题增强的模型名称 |

### 输出格式

#### 带元数据（默认）

```markdown
<metadata>
<Title>文档标题</Title>
<Headings>主题 > 子章节 > 细节</Headings>
</metadata>

[分块内容...]
```

#### 不带元数据

```markdown
[分块内容...]
```

### 使用场景

1. **RAG 知识库构建**
   - 分割长文档的同时保持上下文
   - 丰富的元数据提升检索准确性
   - 标题路径帮助用户理解文档结构

2. **技术文档处理**
   - 保护表格和公式
   - 维护标题层级便于导航
   - 支持复杂的文档结构

3. **科学论文处理**
   - 处理数学公式和表格
   - LLM 增强修正不一致的标题层级
   - 可配置分块适应不同论文章节

4. **企业文档管理**
   - 跨文档类型的一致分块
   - 元数据支持高级搜索和过滤
   - 预处理选项提供干净的文本提取

### 安装方法

1. 从代码仓库下载最新版本
2. 在您的 Dify 实例中安装插件
3. 根据需要配置插件参数

### 配置示例

**基础使用：**

```yaml
input_text: "# 主标题\n## 副标题\n内容..."
heading_level: 3
add_metadata: true
```

**使用 LLM 增强：**

```yaml
input_text: "你的 Markdown 内容..."
heading_level: 2
enable_llm_enhancement: true
llm_api_base: "https://api.openai.com/v1/chat/completions"
llm_api_key: "your-api-key"
llm_model: "gpt-3.5-turbo"
```

### 技术细节

- **最大分块大小：** 2000 字符（固定）
- **分块重叠：** 0（无重叠）
- **分块策略：** 混合（语义 + 固定大小）
- **保护单元：** 表格、数学公式
- **标题层级：** 1-6（H1-H6）

### 最佳实践

1. **标题层级选择：**
   - 对于有清晰顶层结构的超长文档，使用 H1（level=1）
   - 对于大多数文档使用 H2-H3（level=2-3）（推荐）
   - 对于细粒度分块使用 H4-H6（level=4-6）

2. **LLM 增强：**
   - 对标题结构不一致的文档启用
   - 特别适用于转换的 PDF 或 OCR 文档
   - 会增加处理时间但提升质量

3. **元数据使用：**
   - RAG 系统建议保持启用（提升检索效果）
   - 纯文本处理或优化 token 数量时可禁用
   - 文件标题可选但建议在多文档系统中使用

### 常见问题

**问题：分块太大**
- 降低 `heading_level` 以在更高层级的标题处分割
- 检查文档是否有合适的标题层级结构

**问题：标题路径不完整**
- 启用 `enable_llm_enhancement` 修正标题层级
- 确保输入的 Markdown 使用正确的标题语法

**问题：表格或公式被分割**
- 这不应该发生 - 原子单元默认被保护
- 检查内容是否正确格式化为 Markdown 表格/公式

### 许可证

MIT License

### 作者

biaoo

---

## Change Log

### v1.0.0 (Current)
- Initial release
- Hybrid chunking with heading hierarchy preservation
- Optional LLM-based heading enhancement
- Configurable heading levels (default: H3)
- Metadata injection support (toggleable)
- Atomic unit protection for tables and formulas
- Text preprocessing options
