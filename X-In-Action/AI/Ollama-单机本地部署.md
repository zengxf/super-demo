# Ollama-单机本地部署
- 功能: **本部部署 AI 大模型**
- 参考: https://www.cnblogs.com/jyzhao/p/18700202/shou-ba-shou-jiao-ni-bu-shu-deepseek-ben-de-mo-xin
- 参考: https://www.sysgeek.cn/ollama-on-windows/


---
## 下载
1. 访问:
  - https://ollama.com/download
2. 点击 `Download for Windows` 按钮
  - 下载 `OllamaSetup.exe`
  - 双击安装
3. 测试 `ollama -h`


---
## 访问
- http://localhost:11434


---
## 运行
### 运行 DeepSeek-R1
1. 进入: 
  - https://ollama.com/library/deepseek-r1

2. 选择 Tag （如: `1.5b`）, 复制命令: 
```shell
ollama run deepseek-r1:1.5b

# 从魔塔社区 (https://modelscope.cn) 下载模型的格式
# 速度快很多 (6Mb/s)
ollama run modelscope.cn/{username}/{model}
# 示例：
ollama run modelscope.cn/Qwen/Qwen2.5-3B-Instruct-GGUF:Q3_K_M
```

- 模型名称即为: `deepseek-r1:1.5b`
- **这种方式，下载慢，易中断，不推荐**


---
## 手动创建
- 参考: 
  - https://blog.csdn.net/yuuuuuuuk/article/details/140143975

1. 下载: 
  - https://huggingface.co/models?library=gguf

2. 搜索: 
  - `deepseek-r1 1.5b`
  - 选择 `unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF`
  - 点击 **Files and versions**
  - 下载 `DeepSeek-R1-Distill-Qwen-1.5B-Q6_K.gguf` (选择自己想要的模型)

3. 本地处理:
  1. 新增一个文件夹 `ds-r1`
  2. 创建文件 `ds-r1-1_5b.modelfile`
    - 内容：
      - `FROM ./DeepSeek-R1-Distill-Qwen-1.5B-Q6_K.gguf`
  3. 构造 
    - 命令行定位到 `ds-r1` 文件夹再执行:
      - `ollama create ds-r1-1_5b -f ds-r1-1_5b.modelfile`
  4. 测试
    - `ollama run ds-r1-1_5b "hi who are u?"`

4. 后续运行
```shell
ollama run ds-r1-1_5b
```

- 模型名称即为: `ds-r1-1_5b:latest`


---
## 命令总结
- **跟 Docker 命令很类似**
```shell
# 1. 运行模型 (Ctrl + d 可退出交互，但继续运行)
ollama run ds-r1-1_5b

# 2. 查看运行中的模型
ollama ps

# 3. 停止运行中的模型
ollama stop ds-r1-1_5b


# -----------------------

# 1. 拉模型 (拉胯)
ollama pull xx

# 2. 查看所有安装的模型
ollama list


# -----------------------

# 1. 创建模型 (下载到本地的)
ollama create model_name -f model_xx.modelfile

# 2. 查看模型信息
ollama show ds-r1-1_5b

# 3. 删除模型
ollama rm model_name


# -----------------------

# 1. 启动服务
ollama serve

# 2. 查看帮助
ollama -h

# 2. 查看版本
ollama -v
```