## 生成提示词
- **Qwen | Gemini**
```js
你是提示词专家，我要使用 claude code 查看源码原理，根据下面的需求，输出提示词

看当前 maven 项目源码，输出 spring-security-oauth2 与自己的类（如 SmsCodeTokenGranter）联动流程图，及解释下登录原理。
格式要求 markdown，流程图语法用 mermaid。
```
- **不过测试，直接用原需求做提示词，效果好些**


## 格式化 SSE 响应
- **ChatGPT**
```js
// <SSE 全部响应>

把响应消息的 thinking, tool_use 和 text 组装出来，保持对应的格式，不要其他解释
```