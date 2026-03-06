# Python-安装


---
## 下载
- 下载最新
  - 下载页 https://www.python.org/downloads/
  - 点击 (`Download Python 3.13.2`) https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe
- 下载 (3.11)
  - 下载页 https://www.python.org/downloads/release/python-3110/
  - 点击 (`Windows installer (64-bit)`) https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe


---
## 安装
- 默认安装位置 `%LocalAppData%\Programs\Python`
- 将下面 3 个目录地址添加到 `Path` 里
```shell
# pip 命令
%LocalAppData%\Programs\Python\Python313\Scripts\
# python 命令
%LocalAppData%\Programs\Python\Python313\
# py 命令
# (可能在 C:\Windows 目录下)
%LocalAppData%\Programs\Python\Launcher\
```


---
## 查看
```shell
# -------------------------------
# 检查当前激活的虚拟环境 (.venv)

# cmd (Windows)
where python
where py

# powershell (Windows)
get-command python

# bash (Linux 或 Windows git bash)
which python

# -------------------------------
# 查看 Python 解释器路径

# python 命令
python -c "import sys; print(sys.executable)"
```


---
## Ubuntu (WSL) 安装
```bash
# 更新系统软件包
sudo apt update
sudo apt upgrade -y

# 检查自带的 Python (命令通常是 python3 而不是 python)
python3 --version

# 安装 pip (如果有就不用安装)
# sudo apt install python3-pip -y
pip3 --version

# 安装虚拟环境工具 (如果有就不用安装)
# sudo apt install python3-venv -y
python3 -m venv --help
```

- **使用**
```bash
# 创建项目文件夹并进入
mkdir my_fastapi_app && cd my_fastapi_app

# 创建并激活虚拟环境 (激活后，你的终端提示符前面会出现 `(venv)` 字样)
python3 -m venv venv
source venv/bin/activate

# --------------------
# 安装依赖

# 永久配置镜像源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install uv
uv pip install fastapi

# 指定镜像源
pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple
uv pip install fastapi -i https://pypi.tuna.tsinghua.edu.cn/simple
```