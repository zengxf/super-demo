# Ollama-单机本地部署
- 参考: https://www.cnblogs.com/jyzhao/p/18700202/shou-ba-shou-jiao-ni-bu-shu-deepseek-ben-de-mo-xin
- 参考: https://www.sysgeek.cn/ollama-on-windows/
- 功能：**本部部署 AI 大模型**


## 下载
- 访问: https://ollama.com/download
- 点击 `Download for Windows` 按钮
  - 下载 `OllamaSetup.exe`
  - 双击安装
- 测试 `ollama -h`


## 访问
- http://localhost:11434


## 运行
### 运行 DeepSeek-R1
- 进入: https://ollama.com/library/deepseek-r1
- 选择 Tag （如: `1.5b`）, 复制命令：
```shell
ollama run deepseek-r1:1.5b
```