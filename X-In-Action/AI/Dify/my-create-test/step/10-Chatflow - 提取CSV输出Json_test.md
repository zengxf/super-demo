## 10-创建Chatflow - 提取CSV输出Json_test

**入口**
- 工作室 -> Chatflow -> 创建应用 -> 创建空白应用
  - -> Chatflow

**创建**
- 输入名称和描述、选择图标 -> 创建 -> 
  - -> "开始" 节点，点击 "+" 按钮 -> 弹出框 -> 节点 -> "**文档提取器**"
    - -> 设置 -> 输入变量 -> 选择 `开始 / {x} sys.files Array[File]`
  - -> "文档提取器"，点击 "+" 按钮 -> 弹出框 -> 节点 -> "**LLM**"
    - -> ***设置***：
    - -> 选择模型 -> 如 `deepseek-v3`
    - -> 设置 SYSTME -> *写入系统提示词*
    - -> 设置 USER -> 选择 `开始 / {x} sys.query` + `文档提取器 / {x} text`
    - -> 记忆 -> *可关闭*
  - -> "LLM"，点击 "+" 按钮 -> 弹出框 -> 节点 -> "**直接回复**"
    - -> 设置 -> 回复 -> 选择 `LLM / {x} text`
  - -> **发布 | 运行 | 访问 API** 即可

**节点**
- **可选择 "工具" (里面有 "工作流" 和 "MCP" 等)**

curl 'https://searxng.site/search?q=searxng&format=json'
curl 'http://localhost:8080/search?q=searxng&format=json'