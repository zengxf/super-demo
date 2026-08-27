
## 安装
- IDEA 搜索 `Kilo Code`


## 设置
- 点扳手图标，可设置语言为`中文`
- 设置模型提供商：提供商 -> API提供商 -> 可选 `DeepSeek, MiniMax, Z.ai`


## Kilo-MCP.json
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "D:/MyData/pri-project/tech-doc"
      ],
      "alwaysAllow": [
        "read_text_file",
        "list_allowed_directories",
        "directory_tree",
        "search_files"
      ]
    },
    "redis": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-redis",
        "redis://:my_pri@192.168.8.139:6379"
      ]
    },
    "my-spring-ai-server": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/inspector",
        "http://localhost:8026/sse"
      ]
    }
  }
}
```