# Milvus-单机部署


## 安装
- ref: https://milvus.io/docs/zh/install_standalone-windows.md
- **需要 Docker 环境**
- 下载 bat
```bash
# 跳转到保存 bat 的目录
cd D:/Install/DB/milvus

# 用 curl 下载
curl https://raw.githubusercontent.com/milvus-io/milvus/refs/heads/master/scripts/standalone_embed.bat -o standalone.bat
```
- 相当于在 Windows 下运行，不是在 WSL 下运行


## 启停测试
```bash
# 跳转
cd D:/Install/DB/milvus

# 启动 (Docker 容器)
# 默认会将相关文件卷映射到当前目录存储 (D:/Install/DB/milvus)
standalone.bat start

# 停止 (Docker 容器)
standalone.bat stop

# 删除 (Docker 容器)
standalone.bat delete

# 查看 Docker 镜像
docker images
# 输出如下：
# IMAGE                    ID             DISK USAGE   CONTENT SIZE   EXTRA
# milvusdb/milvus:v2.6.8   fde3d7f4467b       3.76GB         1.08GB    U

# 查看容器
docker ps
# CONTAINER ID   IMAGE                    COMMAND                  CREATED          STATUS                    PORTS         NAMES
# 12dd50762b25   milvusdb/milvus:v2.6.8   "/tini -- milvus run…"   32 minutes ago   Up 27 minutes (healthy)   0.0.0.0:2379->2379/tcp, 0.0.0.0:9091->9091/tcp, 0.0.0.0:19530->19530/tcp         milvus-standalone
```


## CURL 测试
```bash
# 列出所有的集合
curl --request POST \
    --url "http://localhost:19530/v2/vectordb/collections/list" \
    --header "Authorization: Bearer xx" \
    --header "Content-Type: application/json" \
    -d '{}'

# 获取 Collection 的详细信息
curl --request POST \
    --url "http://localhost:19530/v2/vectordb/collections/describe" \
    --header "Authorization: Bearer xx" \
    --header "Content-Type: application/json" \
    -d '{
        "collectionName": "customized_setup_1"
    }' > ci-test.json
```


## Attu (Web 管理工具)
- ref: https://github.com/zilliztech/attu
```bash
# 先查看主机 ip
ipconfig

# 输出
# 以太网适配器 以太网:
#
#    连接特定的 DNS 后缀 . . . . . . . :
#    本地链接 IPv6 地址. . . . . . . . : fe80::33f5:309f:3d67:a76a%3
#    IPv4 地址 . . . . . . . . . . . . : 192.168.3.181
#    子网掩码  . . . . . . . . . . . . : 255.255.255.0
#    默认网关. . . . . . . . . . . . . : 192.168.3.2

# 使用上面 IPv4 地址 -> 192.168.3.181
docker run -d --name milvus-web -p 8000:3000 -e MILVUS_URL=192.168.3.181:19530 zilliz/attu:v2.6
```
- view: http://localhost:8000
  - 可手动调整用主机 IP 连接，如：`192.168.3.181:19530`