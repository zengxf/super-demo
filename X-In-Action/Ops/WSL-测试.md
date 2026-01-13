# WSL
- 全称是 Windows Subsystem for Linux，中文是“**适用于 Linux 的 Windows 子系统**”


## 使用
```bash
# 查看 WSL 版本 (简写)
wsl --version
wsl -v

# 升级内核
wsl --update

# 查看 Linux 发行版对应的 WSL 版本 (1 或 2)
wsl --list --verbose
wsl -l -v

# 查看可供下载和安装的 Linux 发行版列表
wsl --list --online
wsl -l -o

# 安装 (默认安装 Ubuntu 最新版)
wsl --install
wsl --install Ubuntu-22.04

# 卸载 
wsl --uninstall Ubuntu-22.04    # 这个不行 (好像把 wsl 内核版本都给降低了)
wsl --unregister Ubuntu-22.04   # 这个可以

# 查看帮助
wsl --help

# 直接进入默认的 Ubuntu
wsl

# 进入相关
wsl -d Ubuntu-22.04             # 进入 (运行) 特定发行版
wsl -d Ubuntu-22.04 -u root     # 以特定用户身份进入
wsl --set-default Ubuntu-22.04  # 设置默认发行版

# 改 root 密码
wsl --user root     # 进入
passwd root         # 重置

# (进入之后) 查看 Linux 版本
cat /etc/os-release
```