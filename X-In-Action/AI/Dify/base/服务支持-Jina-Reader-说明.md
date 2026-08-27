# 服务支持-Jina-Reader-说明


---
## 简介
- Jina Reader 是由 Jina AI 推出的一个将网页内容转化为 Markdown 格式的开源工具，专为 LLM（大语言模型）和 RAG（检索增强生成）应用设计。


---
## 访问
- [主页] https://r.jina.ai/
- [Usage 1] https://r.jina.ai/YOUR_URL
- [Usage 2] https://s.jina.ai/YOUR_SEARCH_QUERY
- [Homepage 使用测试] https://jina.ai/reader
  - 可以复制**专属密钥**


---
## 测试
```bash
curl "https://r.jina.ai/https://www.example.com"

curl "https://r.jina.ai/https://www.iana.org/help/example-domains"

curl "https://r.jina.ai/https://www.baidu.com/s?ie=utf-8&wd=test"
```


---
## 专属密钥
```js
my-***
```

- 可以配置到 Dify 插件里面去
  - 入口参考：[插件管理-数据来源-配置](./插件管理.md#数据来源---配置)


---
## 使用
- 假设用 https://www.51cto.com/ai 做内容源

- Dify -> 控制台 -> 知识库 -> 创建知识库 -> 同步自Web站点
  - -> 选择工具 -> Jina Reader
  - -> 输入 URL `https://www.51cto.com/ai` -> **运行**
  - -> 下一步 -> 保存并处理

- 具体的知识库
  - 可查看**内容列表**
  - 可进行**召回测试**
    - 应用调用也可在 **召回测试** 中查看记录