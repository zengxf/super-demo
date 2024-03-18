# MySql InnoDB 概述

标签（空格分隔）： DB

---

**[原文参考](https://draveness.me/mysql-innodb)**

## 数据库和实例
- 数据库相当于类
- 实例相当于对象

## 数据的存储
- 表空间（tablespace）
- 段（segment）
- 区（extent）
- 页（page）
- - 同一个数据库实例的所有表空间都有相同的页大小；默认情况下，页大小都为 16KB
- - 大小值可为 4, 8, 16, 32, 64 KB
- - 在 InnoDB 存储引擎中，一个区的大小最小为 1MB，页的数量最少为 64 个
- 行（row）
- - 每个 16KB 大小的页中可以存放 2-200 行的记录
- 表空间（tablespace）-> n 段（segment）-> n 区（extent）-> n 页（page）

## 如何存储表
- 表的定义 .frm 文件（表格式）
- 数据索引 .ibd 文件（数据和索引）


## 如何存储记录

### 行存储方式
- 行格式 Compact (Variable Length Header, NULL Indicator, Record Header, RowID, Transaction ID, Roll Pointer, Column1, Column2)
- 行格式 Redundant (Length Offer List, Record Header, RowID, Transaction ID, Roll Pointer, Column1, Column2, Column3)
- 总体上上看，Compact 行记录格式相比 Redundant 格式能够减少 20% 的存储空间

### 行溢出数据
- 将行数据中的前 768 个字节存储在数据页中，后面会通过偏移量指向溢出页。
- 新的行记录格式 Compressed 或者 Dynamic 时都只会在行记录中保存 20 个字节的指针，实际的数据都会存放在溢出页面中

## 数据页结构
- 页是 InnoDB 存储引擎管理数据的最小磁盘单位
- B-Tree 节点就是实际存放表中数据的页面
- 页（`Fil Header, Page Header, Infimum Supermum, User Records, Free Space, Page Directory, Fil Trailer`）
- 每一个页包含一对 `header/trailer`：内部的 `Page Header/Page Directory` 页的状态信息，而 `Fil Header/Fil Trailer` 记录页的头信息。
- Infimum 和 Supremum 这两个虚拟的记录（可以理解为占位符），Infimum 记录是比该页中任何主键值都要小的值，Supremum 是该页中的最大值
- `User Records` 页面中真正用于存放**行记录**的部分
- `Free Space` 空余空间
- 为了保证插入和删除的效率，整个页面并不会按照主键顺序对所有记录进行排序
- 行记录在物理存储上并不是按照顺序的，它们之间的顺序是由 next_record 这一指针控制的
- B+ 树在查找对应的记录时，并不会找出行记录，它只能获取记录所在的页，将整个页加载到内存中，在内存中进行的，所以会忽略耗时


## 索引

### 索引的数据结构
- 绝大多数情况下使用 B+ 树建立索引
- 只能找到数据行对应的页
- B+ 树是平衡树，它查找任意节点所耗费的时间都是完全相同的，比较的次数就是 B+ 树的高度

### 聚集索引和辅助索引

#### 聚集索引（clustered index）
- 存放一条行记录的全部信息
- 聚集索引就是按照表中主键的顺序构建一颗 B+ 树，并在叶节点中存放表中的行记录数据。
- 所有正常的表应该有且仅有一个聚集索引（绝大多数情况下都是主键），表中的所有行记录数据都是按照聚集索引的顺序存放的
- 检索时，可以直接获得聚集索引所对应的整条行记录数据所在的页，不需要进行第二次操作。

#### 辅助索引（secondary index）
- 只包含索引列和一个用于查找对应行记录的『书签』
- 节点并不包含行记录的全部数据，仅包含索引中的所有键和一个用于查找对应行记录的『书签』，在 InnoDB 中这个书签就是当前记录的主键
- 通过辅助索引查找到对应的主键，最后在聚集索引中使用主键获取对应的行记录


## 锁

### 锁的种类
- InnoDB 存储引擎中使用的是**悲观锁**
- 粒度，分成行锁和表锁。
- InnoDB 实现了标准的行级锁，也就是共享锁（Shared Lock）和互斥锁（Exclusive Lock）
- - 共享锁（读锁）：允许事务对一条行数据进行读取；
- - 互斥锁（写锁）：允许事务对一条行数据进行删除或更新；

### 锁的粒度
- 行锁和表锁，意向锁（Intention Lock）
- 意向锁就是一种表级锁
- - 意向共享锁：事务想要在获得表中某些记录的共享锁，需要在表上先加意向共享锁；
- - 意向互斥锁：同上，只是互斥
- - 意向锁其实不会阻塞全表扫描之外的任何请求，主要目的是为了表示是否有人请求锁定表中的某一行数据

#### 加锁示意
##### 如果没有意向锁
用户 A | 用户 B
--- | --- 
使用行锁对表中的某一行进行修改 | 请求要对全表进行修改
x | 需要对所有的行是否被锁定进行扫描
X | 效率是非常低
##### 在引入意向锁之后
用户 A | 用户 B
- | -
行锁对表中的某一行进行修改之前 | x
先为表添加意向互斥锁（IX），再为行记录添加互斥锁（X） | 尝试对全表进行修改，只需要通过等待意向互斥锁被释放
##### 总结: 一个行修改，一个全表修改

### 锁的算法
- 三种锁的算法：Record Lock、Gap Lock 和 Next-Key Lock

#### 记录锁（Record Lock）
- 是加到索引记录上的锁
- 如果使用 id 作为 SQL 中 WHERE 语句的过滤条件，那么 InnoDB 就可以通过索引建立的 B+ 树找到行记录并添加索引
- 如果使用 non_index_column 作为过滤条件时，由于 InnoDB 不知道待修改的记录具体存放的位置，也无法对将要修改哪条记录提前做出判断就会锁定整个表
- **表格总结为**
锁行记录 | 锁表
--- | ---
使用 id 作为过滤条件 | 使用 non_index_column 作为过滤条件
通过 B+ 树找到行记录并添加锁 | 不知道记录具体位置，锁定整个表

#### 间隙锁（Gap Lock）
- 是对索引记录中的一段连续区域的锁
- 当使用类似`SELECT ... WHERE id BETWEEN 10 AND 20 FOR UPDATE;`的 SQL 语句时，就会阻止其他事务向表中插入`id = 15` 的记录，因为整个范围都被间隙锁锁定了
- 唯一阻止的就是**其他事务向这个范围中添加新的记录**
- 只用于某些事务隔离级别

#### Next-Key Lock
- 是记录锁和记录前的间隙锁的结合
- 如：age 字段有记录`21, 30, 80`
- - 在需要的时候锁定以下的范围`
(-∞, 21]
(21, 30]
(30, 80]
(80, ∞)`
- 锁定的是当前值和后面的范围
- 比如`SELECT ... WHERE age = 30 FOR UPDATE;`，InnoDB 不仅会在范围`(21, 30]`上加 Next-Key 锁，还会在这条记录后面的范围`(30, 40]`加间隙锁，所以插入 `(21, 40]`范围内的记录都会被锁定。
- 作用是为了解决幻读的问题

### 死锁的发生
- MySQL 能在发生死锁时及时发现问题，并保证其中的一个事务能正常工作
- 示例
Session 1 | Session 2
--- | ---
begin | begin
where id = 1 for update | where id = 2 for update 
where id = 2 for update | -
- | where id = 1 for update 
(return) | (dead lock!!!)

## 事务
- InnoDB 遵循 SQL:1992 标准中的四种隔离级别：READ UNCOMMITED、READ COMMITED、REPEATABLE READ 和 SERIALIZABLE

### 隔离级别
- RAED UNCOMMITED：使用查询语句不会加锁，可能会读到未提交的行（Dirty Read）；
- READ COMMITED：只对记录加记录锁，而不会在记录之间加间隙锁，所以允许新的记录插入到被锁定记录的附近，所以再多次使用查询语句时，可能得到不同的结果（Non-Repeatable Read）；
- REPEATABLE READ：多次读取同一范围的数据会返回第一次查询的快照，不会返回不同的数据行，但是可能发生幻读（Phantom Read）；（**默认**）
- - 读取不到新插入的行，但自己插入时报重复 id 错误
- - 可用 Next-Key 锁解决`select xx lock in share mode`
- SERIALIZABLE：InnoDB 隐式地将全部的查询语句加上共享锁，解决了幻读的问题；