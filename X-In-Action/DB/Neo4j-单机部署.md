# Neo4j-单机部署


## 下载社区版
- 版本：`2025.11.2` 示例
- 入口：https://neo4j.com/product/community-edition/
- 进入：https://neo4j.com/deployment-center/?gdb-selfmanaged&community
  - 选择 `版本` 和 `Windows`
  - 点击下载按钮 `Download Community`
- 最终：https://go.neo4j.com/download-thanks.html?edition=community&release=2025.11.2&flavour=winzip


## 启动
- 在 `/bin` 目录下
- 创建 `neo4j21.bat` (**指定 JDK-21 运行**)
```bat
@echo off
set JAVA_HOME=D:\Install\Java\JDK\jdk-21
set PATH=%JAVA_HOME%\bin;%PATH%
call neo4j console
```

- (添加 env 后) 直接运行
```shell
# 变量 neo4j = xx/neo4j/bin

cd /d %neo4j%

neo4j21
```


## Web UI
- 访问：http://localhost:7474/browser/
- 初始默认密码：`neo4j / neo4j`
- 初次要改新密码：`abcd1234`


## 忘记密码处理
- 改 `conf/neo4j.conf` 文件
```conf
dbms.security.auth_enabled=false
```

- 重启之后，重新进入
```shell
# 找到 neo4j$ 命令窗口，输入下面的命令：
ALTER USER neo4j SET PASSWORD 'abcd1234';
```