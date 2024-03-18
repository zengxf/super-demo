# MySQL CURD 等小记

标签（空格分隔）： DB

---

## 系统
### 改系统变量(variables)
- `set global binlog_format='STATEMENT'` 语句修改无效
- 要在 `my.ini` 文件修改，然后重启

### 查看系统变量
- `show variables like 'binlog_row_image';`
- `show variables like 'binlog_format';`

### 查看系统状态
- `show engine innodb status;`
- `show master status;`

## 修改
### update 与原数据相同时
- `binlog_format` 是 `ROW` 时，不会执行
  - MySQL 在 binlog 里面记录所有的字段
  - 在读数据时会把所有数据都读出来，重复数据时 update 不会执行
- `binlog_format` 是 `STATEMENT` 时，会执行
  - 该加锁的加锁，该更新的更新
- 通过 `show master status;` 进行验证

### 关联更新、删除
- `UPDATE testb b JOIN testa a ON a.id = b.aid SET b.NAME = < 'cc'| a.name >;`
  - 修改 b 表的 name 列
- `DELETE a, b FROM testb b JOIN testa a ON b.aid = a.id WHERE a.id < 2;`
  - a, b 两表同时删除
- `DELETE b FROM testb b LEFT JOIN testa a ON b.aid = a.id WHERE a.id IS NULL;`
  - 只删除 b 表

## 查询执行顺序
```
(8)  SELECT  (9)  DISTINCT <slect list>
(1)  FROM <left_table>
(3)  <join_tpye> JOIN <right_table>
(2)     ON <join_condition>
(4)  WHERE <where_condition>
(5)  GROUP BY <group_by_list>
(6)  WITH (CUBE|ROLLUP)
(7)  HAVING <having_condition>
(10) ORDER BY <order_by_list>
(11) LIMIT <limit_number>
##
FROM：对 FROM 子句中左表和右表执行笛卡尔积，产生虚拟表 VT1。
ON：对虚拟表 VT1 应用 ON 删选，只有那些符合的行才被插入虚拟表 VT2 中。
JOIN：如果指定了 OUTER JOIN(LEFT OUTER JOIN、RIGHT OUTER JOIN)，
  那么表六中未匹配的行作为外部行添加到虚拟表 VT2 中，产生虚拟表 VT3。
  如果 FROM 子句包含两个以上的表，
  则对上一个连接生成的结果表 VT3 和下一个表重复执行步骤1 > ~步骤3 >，
  直到处理完所有的表位置。
WHERE：对虚拟表 VT3 应用 WHERE 过滤条件，只有符合的记录才被插入虚拟表 VT4 中。
GROUP BY：根据 GROUP BY 子句中的列，对 VT4 中的记录进行分组操作，产生 VT5。
WITH (CUBE|ROLLUP)：对表 VT5 进行 CUBE 或 ROLLUP 操作，产生表 VT6。
HAVING：对虚拟表 VT6 应用 HAVING 过滤器，只有符合的记录才被插入到虚拟表 VT7 中。
SELECT：第二次执行 SELECT 操作，指定制定的列，插入大虚拟表 VT8 中。
DISTINCT：取出重复数据，产生虚拟表 VT9.
ORDER BY：将虚拟表 VT9 中的记录按照进行排序操作，产生虚拟表 VT10。
LIMIT：取出指定行的记录，产生虚拟表 VT11，并返回给查询用户。
```

### 优化经验
- 正常情况是先 join 再进行 where 过滤
  - 利用连接语句先 where 再 join
  - MySQL 嵌套子查询效率比较低

## 查询优化原理、技巧
### 查看优化后的 SQL 语句
- `explain <sql>;`
- `show warnings;`
- 两句同时执行

### MySQL 对待 EXISTS 子句时
- 仍然采用嵌套子查询的执行方式
- 应更改为 JOIN

### MySQL 外部条件不能下推
- 要根据语义上查询条件进行修改

### MySQL 查询-提前缩小范围
- 左连接时，WHERE 条件以及排序均针对最左主表
- 可先对主表排序提前缩小数据量再做左连接

### MySQL 查询-中间结果集下推
- 用于左连接时，另一张表要进行全表聚合查询时
- 子查询出现多次时，使用 WITH 重写
- 编写复杂 SQL 要养成使用 WITH 语句的习惯
  - 简洁的 SQL 能减小数据库的负担

### MySQL WITH 查询
```
WITH 
a AS ( SELECT id, NAME FROM testa ),
b AS ( SELECT id, NAME FROM testb )
SELECT * FROM a, b; // 相当于把 a, b 单独作为表
```

### MySQL 优化小记
- [原文参考](https://juejin.im/post/5c6b9c09f265da2d8a55a855)

#### 数据库设计三大范式(Normal Format)
- 第一范式 1NF：字段原子性
  - 字段不可再分割。关系型数据库，默认就满足
- 第二范式：消除对主键的部分依赖
  - 确保数据库表中的每一列都和主键相关，而不能只与主键的某一部分相关
  - - 主要针对联合主键，即：与联合主键无关
- 第三范式：消除对主键的传递依赖
  - 确保每列都和主键列直接相关，而不是间接相关
  - 即：存在传递依赖时，要拆表

#### MySQL 存储引擎 InnoDB、MyISAM 差异
功能差异 | MyISAM  | InnoDB
-- | -- | -- 
文件碎片（删除记录并flush table 表名之后，表文件大小不变） | 产生。定时整理：使用命令optimize table 表名实现 | 不产生
事务 | 不支持 | 支持
外键 | 不支持 | 支持
锁支持（锁是避免资源争用的一个机制，MySQL 锁对用户几乎是透明的） | 表级锁 | 行级锁、间隙锁、表级锁
- 选择依据：
  - 如果没有特别的需求，使用默认的 `InnoDB` 即可
  - `MyISAM`：以读写插入为主的应用程序，比如博客系统、新闻门户网站
  - `InnoDB`：更新（删除）操作频率高，保证数据的完整性
  - - 并发量高，支持事务和外键保证数据完整性
  - - 比如 OA 自动化办公系统

#### MySQL 锁说明
- 表级锁：
  - `lock tables <t1>,<t2>... read/write`、`unlock tables <t1>,<t2>`
  - `read` 是共享读锁，一旦锁定任何客户端可读不可写
  - `write` 是独占写锁，执有者可读可写，其他客户端既不可读也不可写
- 行级锁、间隙锁：
  - `select ... where ... LOCK IN SHARE MODE` # 对查询记录增加共享锁
  - `select ... where ... FOR UPDATE` # 对查询记录增加排他锁

#### MySQL 压测工具 mysqlslap
- MySQL 附带的
- 自动生成 SQL 测试：`mysqlslap --auto-generate-sql -uroot -p`
- 并发测试 `mysqlslap xx --concurrency=100`
- 多轮测试 `mysqlslap xx --iterations=10`
- 存储引擎测试 `mysqlslap xx --engine=innodb`

#### MySQL 典型的服务器配置
- 查询命令：`show variables like 'var'`
- `max_connections`，最大客户端连接数
- `table_open_cache`，表文件句柄缓存
  - 表数据是存储在磁盘上的，缓存磁盘文件的句柄方便打开文件读取数据
- `key_buffer_size`，索引缓存大小
  - 将从磁盘上读取的索引缓存到内存，可以设置大一些，有利于快速检索
- `innodb_buffer_pool_size`，InnoDB 存储引擎缓存池大小
  - 对于 InnoDB 来说最重要的一个配置，如果所有的表用的都是 InnoDB
  - 那么甚至建议将该值设置到物理内存的 80%，InnoDB 的很多性能提升如索引都是依靠这个
- `innodb_file_per_table`，InnoDB 中，表数据存放在 `ibd` 文件中
  - 如果将该配置项设置为 `ON`，那么一个表对应一个 `ibd` 文件，否则所有 InnoDB 共享表空间
