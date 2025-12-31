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