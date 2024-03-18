# MySQL 安装

---
## Windows 下 MySQL 环境搭建
- 参考：https://zhuanlan.zhihu.com/p/48531203
- zip 下载地址：https://dev.mysql.com/downloads/mysql/
  - 下载 `mysql-8.0.33-winx64.zip`

### 使用 msi 简单快速安装
- 谷歌：`mysql download windows msi`
- https://dev.mysql.com/downloads/installer/
  - 下载 `mysql-installer-community-8.0.33.0.msi`
- **zip 下载安装不了，就用此方法**

### 同目录下创建 my.ini
```conf
# basedir：安装目录； datadir：数据文件存放位置

[mysqld]
# basedir = K:\install\DB\mysql-8 # 可以不用配置
datadir = K:\install\DB\mysql-8\data
port = 3306

# Windows 不需要此配置
# Linux 可启用这三个配置，用于启动多个实例，客户端命令加参：`-S /tmp/mysql-8808.sock`
# socket = /tmp/mysql-3306.sock   
# mysqlx-port = 33080
# mysqlx-socket = /tmp/mysqlx-33080.sock

default_authentication_plugin = mysql_native_password # 默认使用的认证插件

max_connections = 200 # 允许最大连接数
max_connect_errors = 10 # 允许连接失败的次数
default-storage-engine = INNODB # 创建新表时将使用的默认存储引擎

sql_mode = NO_ENGINE_SUBSTITUTION,STRICT_TRANS_TABLES 

character-set-server = utf8mb4

performance_schema_max_table_instances = 600
table_definition_cache = 400
table_open_cache = 256


[client]    # [mysql]
default-character-set = utf8mb4
user = mysqluser
# password = "mysqlpass"           # 测试不行
# socket = /tmp/mysql-3306.sock    # 测试不行
```

### 初始化（管理员权限操作）
- `mysqld --initialize --console`
- `.\mysqld --initialize --console` (Win11 PowerShell)
- 记住密码：`root@localhost: <pwd>`
  - 如：`root@localhost: &Kuuart?2epu`

### 注册服务（管理员权限操作）
- `mysqld --install mysql`
- 启动 `net start mysql`

### 连接并初始密码
- `mysql -uroot -p`
- 初始密码 `ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'abc';`


----
## Linux 安装
### 先初始化文件夹 
- 如：`/data/mysql-data/prod-8806/data`，此文件夹先不用创建，它会自动创建
- 命令：`mysqld --initialize --user=root --datadir=/data/mysql-data/prod-8806/data`
- 密码输出：`A temporary password is generated for root@localhost: SFqn0cuep:-L`
  - 密码就是 `SFqn0cuep:-L`

### 启动
- `mysqld --defaults-file=/data/mysql-data/prod-8806/my.cnf --user=root`
- `my.cnf` 配置与 `my.ini` 相同

### 连接并初始密码
- `mysql -uroot -p`
  - 使用上面的密码：`SFqn0cuep:-L`
  - 如果设置了 socket 文件，则用参数 `-S /tmp/mysql-8808.sock` 指定
- `ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'pwd';`


