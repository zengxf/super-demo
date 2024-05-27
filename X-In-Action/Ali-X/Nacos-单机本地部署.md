# Nacos-单机本地部署

## 参考
- https://nacos.io/zh-cn/docs/quick-start.html


## 下载
- https://github.com/alibaba/nacos/releases
  - 下载 `nacos-server-$version.zip` 包
- 如：https://github.com/alibaba/nacos/releases/download/2.3.1/nacos-server-2.3.1.zip
  - 下载后解压


## 改配置
- 改 `./bin/startup.cmd`
```js
rem set MODE="cluster" // 相当于注释掉
set MODE="standalone"  // 设置为单机模式
```

- 改 `./conf/application.properties`
```js
// 只需打开注释
spring.datasource.platform=mysql
spring.sql.init.platform=mysql
db.num=1

// 改下 URL 和用户名密码
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