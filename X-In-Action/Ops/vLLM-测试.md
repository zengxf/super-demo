# vLLM-测试


---
## 安装

### 使用 Docker
#### 参考
- https://vllm.hyper.ai/docs/getting-started/installation/cpu#使用-docker-安装
- https://gallery.ecr.aws/q9t5s3a7/vllm-cpu-release-repo

#### 1. Docker 设置代理
**通过 Docker Desktop 图形界面配置（推荐）**

这是最简单、最有效的方法，直接影响 `docker pull` 的网络环境。

1. 打开 **Docker Desktop**。
2. 点击右上角的 **设置 (齿轮图标)**。
3. 在左侧菜单选择 **Resources** -> **Proxies**。
4. 将 **Manual proxy configuration** 开关打开。
5. 填写你的代理地址（假设你的代理软件运行在本地 7890 端口）：
    * **Web Server (HTTP)**: `http://127.0.0.1:7890`
    * **Secure Web Server (HTTPS)**: `http://127.0.0.1:7890`
    * **Bypass proxy settings**: `localhost,127.0.0.1,hub-mirror.c.163.com` (这些地址不走代理)
6. 点击 **Apply**。Docker 会自动应用配置。

#### 2. Docker 运行
```bash
# 拉镜像
docker pull public.ecr.aws/q9t5s3a7/vllm-cpu-release-repo:v0.14.0

# 改镜像名
docker image tag public.ecr.aws/q9t5s3a7/vllm-cpu-release-repo:v0.14.0 vllm-cpu:v0.14

# 删除旧名称
docker rmi public.ecr.aws/q9t5s3a7/vllm-cpu-release-repo:v0.14.0

# 启动
# 正式运行
# docker run -d ^
# 测试性运行
docker run -it --rm ^
    --name vllm-cpu-server ^
    -p 8108:8000 ^
    -v D:/Data/llm:/root/.cache/huggingface ^
    -e HF_ENDPOINT="https://hf-mirror.com" ^
    -e VLLM_CPU_KVCACHE_SPACE=8 ^
    -e VLLM_CPU_OMP_THREADS_BIND=0-7 ^
    vllm-cpu:v0.14 ^
    --device cpu ^
    -e VLLM_CPU_DISABLE_AVX512=true ^
    --dtype float16 ^
    --model Qwen/Qwen3-0.6B ^
    --served-model-name My/Qwen3-0.6B

# 持续追踪输出日志（类似 Linux 的 tail -f）
docker logs -f vllm-cpu-server
```

#### 3. 结果
- ***在 AMD Ryzen 7 5700G 台式机上有问题***


### 用 WSL
```bash
# 1. 进入 WSL2 (Ubuntu)
wsl

# 2. 安装 Python 环境（在 WSL 内）
sudo apt update
sudo apt install python3-pip python3-venv -y

# 3. 创建并激活虚拟环境
python3 -m venv ~/vllm_env
source ~/vllm_env/bin/activate

# 4. 执行安装命令
# -- 在 windows conda 环境下面没用
pip install vllm-cpu --extra-index-url https://download.pytorch.org/whl/cpu
# 降级版本
pip install vllm-cpu==0.8.5 --extra-index-url https://download.pytorch.org/whl/cpu

export HF_ENDPOINT=https://hf-mirror.com
export VLLM_USE_V1=0
export VLLM_CPU_KVCACHE_SPACE=4
export ONEDNN_MAX_CPU_ISA=AVX2
export VLLM_CPU_DISABLE_AVX512=true
python3 -m vllm.entrypoints.openai.api_server \
    --dtype float32 \
    --port 8108 \
    --model Qwen/Qwen3-0.6B \
    --served-model-name My/Qwen3-0.6B
```
- ***有问题，启动不成功***


### 用源码
```bash
git clone https://github.com/vllm-project/vllm.git vllm_source
cd vllm_source


# requirements/cpu.txt 要改下依赖版本
# --
# setuptools==80.9.0

uv pip install --upgrade pip
uv pip install "cmake>=3.26" wheel packaging ninja "setuptools-scm>=8" numpy
uv pip install -v -r requirements/cpu.txt --extra-index-url https://download.pytorch.org/whl/cpu

set VLLM_TARGET_DEVICE=cpu
python setup.py install
```
- TODO