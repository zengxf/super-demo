## 初步原理

**请求示例**
```json
{
  "model": "MiniMax-M2.5",
  ...,
  "tools": [
    ...,
    {
      "name": "Skill",
      "description": "Execute a skill within the main conversation
...

Example:
  User: \"run /commit\"
  Assistant: [Calls Skill tool with skill: \"commit\"]

How to invoke:
- Use this tool with the skill name and optional arguments
- Examples:
  - `skill: \"pdf\"` - invoke the pdf skill
  - `skill: \"commit\", args: \"-m 'Fix bug'\"` - invoke with arguments

...

Available skills:
...
- example-skills:docx: Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. When Claude needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks
...
- example-skills:pdf: Comprehensive PDF manipulation toolkit for extracting text and tables, creating new PDFs, merging/splitting documents, and handling forms. When Claude needs to fill in a PDF form or programmatically process, generate, or analyze PDF documents at scale.
...
- example-skills:pptx: Presentation creation, editing, and analysis. When Claude needs to work with presentations (.pptx files) for: (1) Creating new presentations, (2) Modifying or editing content, (3) Working with layouts, (4) Adding comments or speaker notes, or any other presentation tasks
- example-skills:xlsx: Comprehensive spreadsheet creation, editing, and analysis with support for formulas, formatting, data analysis, and visualization. When Claude needs to work with spreadsheets (.xlsx, .xlsm, .csv, .tsv, etc) for: (1) Creating new spreadsheets with formulas and formatting, (2) Reading or analyzing data, (3) Modify existing spreadsheets while preserving formulas, (4) Data analysis and visualization in spreadsheets, or (5) Recalculating formulas
...
",
      "input_schema": { ... }
    }
  ],
  "max_tokens": 32000,
  "stream": true
}
```
- `example-skills:pdf` 后面的描述就是 skill 描述

**SKILL.md**
- `C:\Users\my-pri\.claude\plugins\marketplaces\anthropic-agent-skills\skills\pdf\SKILL.md`
```md
---
name: pdf
description: Comprehensive PDF manipulation toolkit for extracting text and tables, creating new PDFs, merging/splitting documents, and handling forms. When Claude needs to fill in a PDF form or programmatically process, generate, or analyze PDF documents at scale.
---
<中文> **功能全面的 PDF 处理工具包，用于提取文本和表格、创建新的 PDF、合并/拆分文档以及处理表单。当 Claude 需要填写 PDF 表单或以编程方式大规模处理、生成或分析 PDF 文档时，此工具包将是您的理想之选。**
...
---

# PDF Processing Guide

## Overview

This guide covers essential PDF processing operations using Python libraries and command-line tools. For advanced features, JavaScript libraries, and detailed examples, see reference.md. If you need to fill out a PDF form, read forms.md and follow its instructions.

## Quick Start

...
```


## 测试
```md
使用 pdf skill 读取 D:\Data\0-test\test.pdf 里面的内容
```


## 1 rq
```json
{
  "model": "MiniMax-M2.5",
  "messages": [
    {
      "role": "user",
      "content": [
        ...,
        {
          "type": "text",
          "text": "使用 pdf skill 读取 D:\\Data\\0-test\\test.pdf 里面的内容",
          "cache_control": {
            "type": "ephemeral"
          }
        }
      ]
    }
  ],
  "system": [ ... ],
  "tools": [ ... ],
  "stream": true
}
```

## 1 rs
```json
{
  "thinking": "用户想要使用 pdf skill 来读取 PDF 文件的内容。我需要使用 Skill 工具来调用 pdf skill。",
  "tool_use": {
    "id": "call_function_un2pr9hwn2oi_1",
    "name": "Skill",
    "input": {
      "args": "读取 D:\\Data\\0-test\\test.pdf 里面的内容",
      "skill": "pdf"
    }
  },
  "text": ""
}
```


## 2 rq
```json
{
  "model": "MiniMax-M2.5",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "使用 pdf skill 读取 D:\\Data\\0-test\\test.pdf 里面的内容"
        }
      ]
    },
    {
      "role": "assistant",
      "content": [
        {
          "type": "thinking",
          "thinking": "用户想要使用 pdf skill 来读取 PDF 文件的内容。我需要使用 Skill 工具来调用 pdf skill。",
          "signature": "2b1252aae037f654304363df7150813c2717cf1d5940f2ca122b6e0e8cc6aa65"
        },
        {
          "type": "tool_use",
          "id": "call_function_un2pr9hwn2oi_1",
          "name": "Skill",
          "input": {
            "args": "读取 D:\\Data\\0-test\\test.pdf 里面的内容",
            "skill": "pdf"
          },
          "cache_control": {
            "type": "ephemeral"
          }
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "tool_result",
          "tool_use_id": "call_function_un2pr9hwn2oi_1",
          "content": "Launching skill: pdf"
        },
        {
          "type": "text",
          "text": "Base directory for this skill: C:\\Users\\my-pri\\.claude\\plugins\\cache\\anthropic-agent-skills\\example-skills\\69c0b1a06741\\skills\\pdf

... <SKILL.md> <start>

# PDF Processing Guide

## Overview

This guide covers essential PDF processing operations using Python libraries and command-line tools. For advanced features, JavaScript libraries, and detailed examples, see reference.md. If you need to fill out a PDF form, read forms.md and follow its instructions.

## Quick Start

...

## Next Steps

- For advanced pypdmy-prim2 usage, see reference.md
- For JavaScript libraries (pdf-lib), see reference.md
- If you need to fill out a PDF form, follow the instructions in forms.md
- For troubleshooting guides, see reference.md

... <SKILL.md> <end>

ARGUMENTS: 读取 D:\\Data\\0-test\\test.pdf 里面的内容",
          "cache_control": {
            "type": "ephemeral"
          }
        }
      ]
    }
  ],
  "stream": true
}
```

## 2 rs
```json
{
  "thinking": "用户想要使用 PDF skill 来读取 D:\\Data\\0-test\\test.pdf 文件的内容。根据 skill 指南，我需要使用 Python 的 pypdf 或 pdfplumber 来读取 PDF 内容。

让我编写一个 Python 脚本来读取 PDF 内容。",
  "text": "我来使用 Python 读取这个 PDF 文件的内容。\n",
  "tool_use": {
    "id": "call_function_o458n2x7xvfu_1",
    "name": "Bash",
    "input": {
      "command": "python -c \"
from pypdf import PdfReader
import sys

reader = PdfReader('D:/Data/0-test/test.pdf')
print(f'总页数: {len(reader.pages)}')
print('=' * 50)

for i, page in enumerate(reader.pages):
    text = page.extract_text()
    print(f'--- 第 {i+1} 页 ---')
    print(text if text else '(无文本内容)')
    print()
\"",
      "description": "读取 PDF 文件内容"
    }
  }
}
```


## 3 rq
```json
{
  "model": "MiniMax-M2.5",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "使用 pdf skill 读取 D:\\Data\\0-test\\test.pdf 里面的内容"
        }
      ]
    },
    {
      "role": "assistant",
      "content": [
        {
          "type": "thinking",
          "thinking": "用户想要使用 pdf skill 来读取 PDF 文件的内容。我需要使用 Skill 工具来调用 pdf skill。",
          "signature": "2b1252aae037f654304363df7150813c2717cf1d5940f2ca122b6e0e8cc6aa65"
        },
        {
          "type": "tool_use",
          "id": "call_function_un2pr9hwn2oi_1",
          "name": "Skill",
          "input": {
            "args": "读取 D:\\Data\\0-test\\test.pdf 里面的内容",
            "skill": "pdf"
          }
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "tool_result",
          "tool_use_id": "call_function_un2pr9hwn2oi_1",
          "content": "Launching skill: pdf"
        },
        {
          "type": "text",
          "text": "Base directory for this skill: C:\\Users\\my-pri\\.claude\\plugins\\cache\\anthropic-agent-skills\\example-skills ..."
        }
      ]
    },
    {
      "role": "assistant",
      "content": [
        {
          "type": "thinking",
          "thinking": "用户想要使用 PDF skill 来读取 D:\\Data\\0-test\\test.pdf 文件的内容。根据 skill 指南，我需要使用 Python ... 读取 PDF 内容。",
        },
        {
          "type": "text",
          "text": "我来使用 Python 读取这个 PDF 文件的内容。\n"
        },
        {
          "type": "tool_use",
          "id": "call_function_o458n2x7xvfu_1",
          "name": "Bash",
          "input": {
            "command": "python -c \"\nfrom pypdf import PdfReader\nimport sys ... \"",
            "description": "读取 PDF 文件内容"
          },
          "cache_control": {
            "type": "ephemeral"
          }
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "tool_result",
          "content": "Exit code 1
Traceback (most recent call last):\r
  File \"<string>\", line 12, in <module>\r
UnicodeEncodeError: 'gbk' codec can't encode character '\\uf0b7' in position 65: illegal multibyte sequence\r

��ҳ��: 1\r
==================================================\r
--- �� 1 ҳ ---",
          "is_error": true,
          "tool_use_id": "call_function_o458n2x7xvfu_1",
          "cache_control": {
            "type": "ephemeral"
          }
        }
      ]
    }
  ],
  "stream": true
}
```


## 3 rs
```json
{
  "thinking": "看起来有编码问题。让我尝试用不同的方式来处理输出，或者先检查文件是否存在。",
  "text": "编码问题，让我尝试另一种方式读取。\n",
  "tool_use": {
    "id": "call_function_gsu6xqg2nfhh_1",
    "name": "Bash",
    "input": {
      "command": "python -c \"
from pypdf import PdfReader

reader = PdfReader('D:/Data/0-test/test.pdf')
print(f'总页数: {len(reader.pages)}')
print('=' * 50)

for i, page in enumerate(reader.pages):
    text = page.extract_text()
    print(f'--- 第 {i+1} 页 ---')
    if text:
        # 写入文件避免编码问题
        with open('D:/Data/0-test/pdf_output.txt', 'a', encoding='utf-8') as f:
            f.write(f'--- 第 {i+1} 页 ---\\\
')
            f.write(text)
            f.write('\\\
\\\
')
    else:
        print('(无文本内容)')
        with open('D:/Data/0-test/pdf_output.txt', 'a', encoding='utf-8') as f:
            f.write(f'--- 第 {i+1} 页 ---\\\
')
            f.write('(无文本内容)\\\
\\\
')
\"",
      "description": "读取 PDF 内容并保存到文件"
    }
  }
}
```

## ...