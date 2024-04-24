# Seata-单机本地部署

## 参考
- https://seata.apache.org/zh-cn/unversioned/download/seata-server
- https://www.youlai.tech/pages/0bzvi/


## 下载
- https://github.com/apache/incubator-seata/releases
  - 下载 `seata-server-$version.zip` 包
- 如：https://github.com/apache/incubator-seata/releases/download/v2.0.0/seata-server-2.0.0.zip
  - 下载后解压


## 改配置
- 改 `./conf/application.yml`
```yaml
seata:
  store:
    # support: file 、 db 、 redis 、 raft
    mode: db
    db:
      datasource: hikari # druid # 使用 hikari 连接池，不用 druid
      db-type: mysql
      driver-class-name: com.mysql.cj.jdbc.Driver # 使用 MySQL 8.0 连接
      url: jdbc:mysql://127.0.0.1:3306/seata?rewriteBatchedStatements=true&characterEncoding=utf8&connectTimeout=1000&socketTimeout=3000&autoReconnect=true&useUnicode=true&useSSL=false&serverTimezone=GMT%2B8
      user: root
      password: abcd
      min-conn: 10
      max-conn: 100
      global-table: global_table
      branch-table: branch_table
      lock-table: lock_table
      distributed-lock-table: distributed_lock
      query-limit: 1000
      max-wait: 5000
```


## 补驱动
- 将 `./lib/jdbc/mysql-connector-java-8.0.27.jar`
  - 复制到 `./lib` 目录下


## MySQL
- 创建 `seata` 数据库
- 执行 `./script/server/db/mysql.sql` 脚本


## 启动
- 双击 `./bin/seata-server.bat`


## 访问
- http://localhost:7091/
  - 登录账号默认为：`seata / seata`