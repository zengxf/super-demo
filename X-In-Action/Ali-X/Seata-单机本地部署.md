# Seata-单机本地部署

## 参考
- https://seata.apache.org/zh-cn/docs/user/quickstart


## 下载
- ~~https://github.com/apache/incubator-seata/releases~~
- https://seata.apache.org/zh-cn/download/seata-server
- https://seata.apache.org/zh-cn/release-history/seata-server
  - 下载 `seata-server-$version.zip` 包
- 如：https://www.apache.org/dyn/closer.lua/incubator/seata/2.6.0/apache-seata-2.6.0-incubating-bin.tar.gz?action=download
  - 下载后解压


## 改配置
- **改 `./conf/application.yml`**
```yaml
seata:
  store:
    # support: file 、 db 、 redis 、 raft
    mode: db
    db:
      datasource: hikari # 使用 hikari 连接池，不用 druid
      db-type: mysql
      driver-class-name: com.mysql.cj.jdbc.Driver # 使用 MySQL 8.0 连接
      url: jdbc:mysql://127.0.0.1:3306/seata?rewriteBatchedStatements=true&characterEncoding=utf8&connectTimeout=1000&socketTimeout=3000&autoReconnect=true&useUnicode=true&useSSL=false&serverTimezone=GMT%2B8
      user: root
      password: abcd
      ... # 同模板 application.example.yml
```


## 补驱动
- https://mvnrepository.com/artifact/com.mysql/mysql-connector-j/8.4.0
- **下载 jar** `mysql-connector-j-8.4.0.jar`
- 复制到 `./lib` 目录下


## MySQL
- 创建 `seata` 数据库
- 执行 `./script/server/db/mysql.sql` 脚本


## 启动
- 双击 `./bin/seata-server.bat`



## 配置 seata-namingserver
1. **改 `./conf/application.yml`**
```yml
console:
  user:
    username: zxf
    password: a
```

2. **改 `./bin/seata-namingserver.bat`**
```sh
# 在 
# if "%JAVACMD%"=="" set JAVACMD=java 
# 上面加下这 2 段代码
set PATH=%Java25%\bin;%PATH%
java --version
```

3. **启动**
- 双击 `./bin/seata-namingserver.bat`

4. **访问**
- http://localhost:8081/
- 登录账号默认为：`zxf / a`

5. **总结**
- ***需要 seata-server 连接才有数据，要不然一点意义也没有***



## 使用注册中心

### 使用 Eureka 注册
- **改 `./conf/application.yml`**
```yml
seata:
  registry:
    type: eureka
    eureka:
      service-url: http://localhost:8761/eureka
      application: seata-server # 设置应用名
      weight: 1
```

### 使用 Seata 注册 (seata-namingserver)
- **改 `./conf/application.yml`**
```yml
seata:
  registry:
    type: seata
    seata:
      server-addr: 127.0.0.1:8081
      cluster: default
      namespace: public
      heartbeat-period: 5000
      metadata-max-age-ms: 30000
      username: zxf
      password: a
      tokenValidityInMilliseconds: 1740000
```