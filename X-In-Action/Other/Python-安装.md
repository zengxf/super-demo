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
%LocalAppData%\Programs\Python\Launcher\
```


---
## 查看
```shell
# -------------------------------
# 检查当前激活的虚拟环境 (.venv)

# cmd (Windows)
where python

# powershell (Windows)
get-command python

# bash (Linux 或 Windows git bash)
which python


# -------------------------------
# 查看相关环境变量

# cmd (Windows)
echo %VIRTUAL_ENV%      # 使用 .venv
echo %CONDA_PREFIX%     # 使用 Conda

# bash (Linux 或 Windows git bash)
echo $VIRTUAL_ENV
echo $CONDA_PREFIX


# -------------------------------
# 查看 Python 解释器路径

# python 命令
python -c "import sys; print(sys.executable)"
```


## 路径变量
```shell
echo %UserProfile%
echo %HomePath%
echo %HomeDrive%
echo %AppData%
echo %LocalAppData%


# -------------------------------

(.venv) D:\MyData\test> echo %UserProfile%
C:\Users\xx

(.venv) D:\MyData\test> echo %HomePath%
\Users\xx

(.venv) D:\MyData\test> echo %HomeDrive%
C:

(.venv) D:\MyData\test> echo %AppData%
C:\Users\xx\AppData\Roaming

(.venv) D:\MyData\test> echo %LocalAppData%
C:\Users\xx\AppData\Local
```