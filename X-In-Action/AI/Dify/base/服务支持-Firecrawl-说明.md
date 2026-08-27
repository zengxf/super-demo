# 服务支持-Firecrawl-说明


---
## 简介
- Firecrawl 是一款专为 AI 时代设计的 AI 网页数据采集平台。它能将复杂的网页内容自动转化成大语言模型（LLM）最容易理解的 Markdown 或 结构化数据 (JSON)。


---
## 专属密钥
- https://www.firecrawl.dev/app/api-keys

```js
fc-my-***
```

- 可以配置到 Dify 插件里面去
  - 入口参考：[插件管理-数据来源-配置](./插件管理.md#数据来源---配置)


---
## 使用
- **与 Jina-Reader 差不多**
- **API URL** 填写 `https://api.firecrawl.dev`


---
## 🤖 注
- 不能直接用作流程图里的工具使用，返回的 `json` 字段，下游节点提取不了