## Ref
- http://www.cnblogs.com/ggjucheng/archive/2012/11/11/2765237.html
- 8.0 新特性 https://segmentfault.com/a/1190000041276068
- filtered 说明参考 https://www.cnblogs.com/qianxiaoPro/p/16144899.html

## EXPLAIN 变体
1. EXPLAIN EXTENDED SELECT ……
- 将执行计划“反编译”成SELECT语句，运行`SHOW WARNINGS`，可得到被 MySQL 优化器优化后的查询语句 
2. EXPLAIN PARTITIONS SELECT ……
- 用于分区表的 EXPLAIN


## EXPLAIN 字段解释
- 重点关注 **key**、**rows**和**type** 字段

### id
- 查询中执行 select 子句或操作表的顺序
- 值相同，执行顺序由上至下
- 值越大，越先被执行（优先级越高）

### select_type 
- 查询中每个 `SELECT` 子句的类型
- SIMPLE: 查询中不包含子查询或者 `UNION`
- PRIMARY: 查询中若包含任何复杂的子部分，最外层查询则被标记为：`PRIMARY`
- SUBQUERY: 在`SELECT`或`WHERE`列表中包含了子查询，该子查询被标记为：`SUBQUERY`
- DERIVED: 在`FROM`列表中包含的子查询被标记为：`DERIVED`（衍生）
- UNION: 若第二个`SELECT`出现在`UNION`之后，则被标记为`UNION`；若`UNION`包含在`FROM`子句的子查询中，外层`SELECT`将被标记为：`DERIVED`
- UNION RESULT: 从 `UNION` 表获取结果的`SELECT`被标记为：`UNION RESULT`

### type
- 在表中找到所需行的方式，又称“访问类型”
- ALL：全表扫描
- index：Full Index Scan，只遍历索引树
- range：索引范围扫描
- - 常见于`between、<、>`等的查询
- ref: 非唯一性索引扫描，返回匹配某个单独值的所有行
- eq_ref：唯一性索引扫描
- const：MySQL 对查询某部分进行优化，~~并转换为一个常量~~。如**主键**等值查询
- system：是const类型的特例，当查询的表只有一行
- NULL：MySQL 在优化过程中分解语句，执行时不用访问表或索引

### possible_keys
- MySQL 能使用哪个索引在表中找到行
- 查询涉及到的字段上若存在索引，则该索引将被列出，但不一定被查询使用

### key
- 在查询中实际使用的索引
- NULL：没有使用索引
- 其他：实际用到的索引
- 注：查询中若使用了覆盖索引，则该索引仅出现在 key 列表中

### key_len
- 索引中使用的字节数
- 显示的值为索引字段的最大**可能**长度

### ref
- 连接匹配条件，即哪些列或常量被用于查找索引列上的值

### rows
- **预估**要扫描的记录行

### filtered
- 说明参考 https://www.cnblogs.com/qianxiaoPro/p/16144899.html
- 表示通过查询条件获取的最终记录行数占通过type字段指明的搜索方式搜索出来的记录行数的百分比

### Extra
- 包含不适合在其他列中显示但十分重要的**额外**信息
- Using index：使用了覆盖索引（Covering Index）
- Using where：接受到记录后进行“后过滤”（Post-filter）
- Using temporary：使用**临时表**来存储结果集，常见于排序和分组查询
- Using filesort：无法利用索引完成的排序操作称为“文件排序”



---
## 覆盖索引（Covering Index）
- 相当于**宽索引**
- *MySQL可以利用索引返回`select`列表中的字段，而不必根据索引再次读取数据文件*
- *包含所有满足查询需要的数据的索引称为**覆盖索引**（Covering Index）*
- *注意：*
- - *如果要使用覆盖索引，一定要注意 `select` 列表中只取出需要的列*
