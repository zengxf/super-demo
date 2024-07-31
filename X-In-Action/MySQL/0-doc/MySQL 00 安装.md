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
- 内容参考：[win-my.ini](../win-my.ini)

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

### 总示例
```js
D:\Install\DB\MySQL\mysql-8.0.37-winx64\bin> mysqld --initialize --console
...
2024-06-27T08:41:10.547442Z 1 [System] [MY-013576] [InnoDB] InnoDB initialization has started.
2024-06-27T08:41:10.855523Z 1 [System] [MY-013577] [InnoDB] InnoDB initialization has ended.
2024-06-27T08:41:12.118630Z 6 [Note] [MY-010454] [Server] A temporary password is generated for root@localhost: .;(hmqrW/2gc // 密码为 ".;(hmqrW/2gc"
...

D:\Install\DB\MySQL\mysql-8.0.37-winx64\bin> mysqld --install mysql
Install/Remove of the Service Denied! // 普通用户，权限拒绝安装

// Win + X => 终端管理员(A) => 运行下面的命令

PS C:\Users\656553> cd D:\Install\DB\MySQL\mysql-8.0.37-winx64\bin

PS D:\Install\DB\MySQL\mysql-8.0.37-winx64\bin> .\mysqld --install mysql
Service successfully installed. // 安装成功

PS D:\Install\DB\MySQL\mysql-8.0.37-winx64\bin> net start mysql
mysql 服务正在启动 .
mysql 服务已经启动成功。

PS D:\Install\DB\MySQL\mysql-8.0.37-winx64\bin>

// 普通终端 => 运行下面命令

D:\Install\DB\MySQL\mysql-8.0.37-winx64\bin> mysql -u root -p.;(hmqrW/2gc // 使用初始密码 ".;(hmqrW/2gc"
...
Server version: 8.0.37
...

mysql> ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'abcd'; // 改密码为 "abcd"
Query OK, 0 rows affected (0.01 sec)
```


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


