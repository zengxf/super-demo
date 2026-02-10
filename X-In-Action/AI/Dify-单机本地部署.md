# Dify-单机本地部署
- ref: https://docs.dify.ai/zh/self-host/quick-start/docker-compose


## 部署
### 1. 克隆 Dify
```bash
# git bash 运行

# 重定向目录
cd /d/Install/AI/Dify

# 手动查看最新版 (搜索 tag_name)
# "tag_name": "1.12.1"
https://api.github.com/repos/langgenius/dify/releases/latest

# 下载指定版本
# https://github.com/langgenius/dify/releases/tag/1.12.1
# https://github.com/langgenius/dify/releases/tag/1.8.1
git clone --branch "1.12.1" https://github.com/langgenius/dify.git
git clone --branch "1.8.1" https://github.com/langgenius/dify.git
```

- 当前用的版本是 **1.8.1** 进行测试


### 2. 启动 Dify
```bash
# 导航到 Dify 源代码中的 docker 目录
cd dify/docker

# 复制示例环境配置文件
cp .env.example .env

# 查看 docker compose 版本
docker compose version
# 输出：
#   Docker Compose version v5.0.0-desktop.1

# 改完 .env 文件后 (单机可以不改 .env)
# 启动容器
docker compose up -d
```

### 3. 验证
```bash
cd dify/docker

# 验证所有容器是否成功运行
docker compose ps
```

### 4. 重启
```bash
cd dify/docker

docker compose down
docker compose up -d
```


## 改配置
```conf
# 改 Web 端口
NGINX_PORT=80
NGINX_SSL_PORT=443
```


## 访问 Dify
1. **打开管理员初始化页面以设置管理员账户**
    - http://localhost/install

2. **完成管理员账户设置后，在以下地址登录 Dify**
    - http://localhost  


## 问题
1. Docker 引擎没运行
```bash
docker compose up -d
# err:
#   unable to get image 'langgenius/dify-api:1.8.1': error during connect: 
#   Get "http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/v1.51/images/langgenius/dify-api:1.8.1/json": 
#   open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```