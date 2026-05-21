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
wsl --install Ubuntu-26.04

# 卸载 
wsl --unregister Ubuntu-24.04   # 用这个
wsl --uninstall  Ubuntu-26.04   # 不建议用这个 (要耐心等待下，10s 左右)

# 查看帮助
wsl --help

# 直接进入默认的 Ubuntu
wsl

# 进入相关
wsl -d Ubuntu-26.04             # 进入 (运行) 特定发行版
wsl -d Ubuntu-26.04 -u root     # 以特定用户身份进入
wsl --set-default Ubuntu-26.04  # 设置默认发行版

# 改 root 密码
wsl --user root     # 进入
passwd root         # 重置

# (进入之后)
# 查看 Linux 版本 和 内核版本
cat /etc/os-release
uname -a
```


## 配置
- 打开 Windows 用户文件夹，即 `C:\Users\xx`
  - 快捷方式 `%userprofile%`

- `.wslconfig`
```conf
[wsl2]
swapFile=D:\\_Data\\WSL\\wsl

# 开启 WSL 镜像网络模式
networkingMode=mirrored
dnsTunneling=true
firewall=true
autoProxy=true
```

- 重启 WSL 使其生效
```sh
wsl --shutdown
```


## 文件
- 在 Windows 对应目录栏输入 `cmd`
- 再输入 `wsl`，可以直接使用对应目录的文件
- **映射关系**
```sh
cmd

wsl

# C 盘 - 文件夹
c:/Users/admin8  ->  /mnt/c/Users/admin8

# D 盘 - 文件夹
d:/_Data/WSL     ->  /mnt/d/_Data/WSL
```

**WSL 下的 ~ 目录在 windows 下哪里**
- 在虚拟文件系统中
```js
// 资源管理器直接访问
\\wsl$

// 会看到类似：
\\wsl$\Ubuntu-26.04

// ~ 目录
\\wsl$\Ubuntu-26.04\home\zxf
```