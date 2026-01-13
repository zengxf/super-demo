
## 安装
- ref: https://docs.docker.com/desktop/setup/install/windows-install/
- 下载： https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
- 安装之后重启

### WSL 里面可以直接使用
```bash
# 原理：调用 docker CLI（是 /usr/bin/docker 的软链接，直接指向 /mnt/wsl/docker-cli）

fa@DESKTOP:/mnt/c/Users/zxf$ type docker
docker is hashed (/usr/bin/docker)

fa@DESKTOP:/mnt/c/Users/zxf$ ll /usr/bin/docker
lrwxrwxrwx 1 root root 48 Jan 13 15:20 /usr/bin/docker -> /mnt/wsl/docker-desktop/cli-tools/usr/bin/docker*
```


## 测试
```bash
# 查看版本
docker -v

# 查看环境详细信息
docker info

# 查看容器
docker ps
```


## GUI
- 可方便查看镜像和容器 (日志、配置、文件卷挂载、命令执行、文件、资源使用信息)


## docker-compose
- 安装 Desktop 之后，`docker-compose` 命令自动可用