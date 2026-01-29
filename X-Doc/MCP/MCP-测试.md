# MCP-测试


---
## 命令测试

### 手动测试
- **cmd 中运行**
```bash
# 手动测试
npx -y @modelcontextprotocol/server-filesystem .
```

- **json 指令**
```json
/**
 * ------------------------
 * 命令 json 必需一行，避免换行符干扰解析
 * ------------------------
 */

// 列出所有方法
// {"jsonrpc":"2.0","id":1,"method":"list_tools","params":{}}  // 此命令不行就用下面的
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}

// 使用 read_file 命令查看文件内容
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"read_file","arguments":{"path":"other/mcp-test.js"}}}
```

### Inspector 界面测试
- **MCP Inspector (官方调试工具)**

- **cmd 中运行**
```bash
# 启动 inspector 界面 (比手动测试好多了)
npx -y @modelcontextprotocol/inspector npx -y @modelcontextprotocol/server-filesystem .
```

- **步骤**
```markdown
1. 点击左下 **Connect** 按钮
2. 点击右中 **List Tools** 按钮
3. 随后点击 **read_list** 选项
4. 随后右上在 `path *` 中输入 `other/mcp-test.js`
5. 下滑点击 **Run Tool** 按钮
6. ***结果功成***
```