# Nacos-单机本地部署

## 参考
- https://nacos.io/zh-cn/docs/quick-start.html


## 下载 (2.3.1)
- 入口：https://github.com/alibaba/nacos/releases/tag/2.3.1
- 点击 `nacos-server-2.3.1.zip`
- 最终：https://github.com/alibaba/nacos/releases/download/2.3.1/nacos-server-2.3.1.zip
  - 下载后解压

- **新版测试**：
  - [V2.4.3](#v243)
  - [V3.1.0](#v310)


## 改配置
- 改 `./bin/startup.cmd`
```js
rem set MODE="cluster" // 相当于注释掉
set MODE="standalone"  // 设置为单机模式
```

- 改 `./conf/application.properties`
```shell
# 只需打开注释
spring.datasource.platform=mysql
spring.sql.init.platform=mysql
db.num=1

# 改下 URL 和用户名密码
db.url.0=jdbc:mysql://127.0.0.1:3306/nacos?characterEncoding=utf8&connectTimeout=1000&socketTimeout=3000&autoReconnect=true&useUnicode=true&useSSL=false&serverTimezone=GMT%2B8
db.user=root
db.password=abcd
```


## MySQL
- 创建 `nacos` 数据库
- 执行 `./conf/mysql-schema.sql` 脚本


## 启动
- 双击 `./bin/startup.cmd`


## 访问
- http://127.0.0.1:8848/nacos/
  - 单机不需要密码


---
---
## 新版测试
### V2.4.3
#### GitHub
- 入口：https://github.com/alibaba/nacos/releases/tag/2.4.3
- 点击 `nacos-server-2.4.3.zip`
- 最终：https://github.com/alibaba/nacos/releases/download/2.4.3/nacos-server-2.4.3.zip

#### 官网
- 入口：https://nacos.io/download/release-history/
- 查找 `2.4.3` (**Nacos 2.x** 下面)
- 点击 `2.4.3`
- 最终：https://.../nacos-server-2.4.3.zip

#### 配置&启动
- 跟上面一样


### V3.1.0
#### 官网
- 入口：https://nacos.io/download/release-history/
- 查找 `3.1.0` (**Nacos 3.x** 下面)
- 点击 `3.1.0`
- 最终：https://.../nacos-server-3.1.0.zip

#### 配置&启动
- 除了 `` 没有
```shell
# spring.datasource.platform=mysql 这个没有了

# 需打开注释
nacos.core.auth.plugin.nacos.token.secret.key=xx

# Web 端口可改
nacos.console.port=8080
```
- 其他跟上面一样

#### 访问
- http://127.0.0.1:8080/
  - 没有 /nacos 后缀