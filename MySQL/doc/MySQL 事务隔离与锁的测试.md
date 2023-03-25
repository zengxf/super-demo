# MySQL 事务隔离与锁的测试
- 最新使用 MySQL 8.0.29 测试

## 修改事务隔离级别
- 注：**Windows 上的测试最好用自带的 mysql.exe 客户端**
  - **不要用 GUI，GUI 可能会使语句单独执行**
  - 使用 `BEGIN;` 和 `COMMIT;` 就可以测试
- 改变全局事务隔离级别时，当前 session 需退出重进才有效
  - 设置 `SET GLOBAL TRANSACTION ISOLATION LEVEL SERIALIZABLE;`
  - 级别 `{READ UNCOMMITTED | READ COMMITTED | REPEATABLE READ | SERIALIZABLE}`
- 改当前级别 `SET SESSION TRANSACTION ISOLATION LEVEL SERIALIZABLE;`；要加 `SESSION` 关键字，否则不生效
- 查看当前级别 `SHOW VARIABLES LIKE 'transaction_isolation';`

## 表创建
```SQL
CREATE TABLE `test` (
 `id` INT NOT NULL, 
 `age` INT DEFAULT NULL, 
 `enname` VARCHAR(255) DEFAULT NULL, 
  PRIMARY KEY (`id`) 
) ENGINE=InnoDB DEFAULT CHARSET=UTF8MB4;
```


---
## 顺序读
1. 用 **Next-Key 锁** 实现

2. T1 先执行读，给相关区间加读锁；后续的事务可以读，但 CUD 的时候会被阻塞

T1 | T2 | Main
--- | --- | --- 
-- | - | `SET GLOBAL TRANSACTION ISOLATION LEVEL SERIALIZABLE;`
-- | - | `TRUNCATE TABLE test;`
-- | - | `INSERT INTO test VALUES(1, 10, 'a'), (5, 20, 'b'), (8, 30, 'c'), (10, 40, 'd');`
`START TRANSACTION;` | `START TRANSACTION;` | - 
`SELECT * FROM test WHERE id <= 5;` // 锁 (-∞, 5] | - | - 
-- | C: `INSERT INTO test VALUES(6, 35, 'c');` // 成功 | -
-- | C: `INSERT INTO test VALUES(4, 25, 'c');` // 阻塞 | -
-- | U: `UPDATE test SET enname = 'a' WHERE id = 8;` // 成功 | -
-- | U: `UPDATE test SET enname = 'a' WHERE id = 5;` // 阻塞 | -
-- | D: `DELETE FROM test WHERE id = 8;` // 成功 | -
-- | D: `DELETE FROM test WHERE id = 5;` // 阻塞 | -
-- | T: `COMMIT;` // 提交数据 | -
`SELECT * FROM test WHERE id <= 5;` // 不存在幻读 | - | -

3. T1 先执行 CUD，给相关区间加写锁；后续的事务 CRUD 的时候都会被阻塞

T1 | T2 | Main
--- | --- | --- 
-- | - | `SET GLOBAL TRANSACTION ISOLATION LEVEL SERIALIZABLE;`
-- | - | `TRUNCATE TABLE test;`
-- | - | `INSERT INTO test VALUES(1, 10, 'a'), (5, 20, 'b'), (8, 30, 'c'), (10, 40, 'd');`
`START TRANSACTION;` | `START TRANSACTION;` | - 
`UPDATE test SET enname = 'a' WHERE id <= 5;` // 锁 (-∞, 5] | - | - 
-- | R: `SELECT * FROM test WHERE id > 5;`  // 成功  | -
-- | R: `SELECT * FROM test WHERE id >= 5;` // 阻塞  | -
-- | C: `INSERT INTO test VALUES(6, 35, 'c');` // 成功 | -
-- | C: `INSERT INTO test VALUES(4, 25, 'c');` // 阻塞 | -
-- | U: `UPDATE test SET enname = 'a' WHERE id = 8;` // 成功 | -
-- | U: `UPDATE test SET enname = 'a' WHERE id = 5;` // 阻塞 | -
-- | D: `DELETE FROM test WHERE id = 8;` // 成功 | -
-- | D: `DELETE FROM test WHERE id = 5;` // 阻塞 | -


---
## 可重复读
1. 用 **Next-Key 锁** 实现

2. T1 先执行读，并没有给相关区间加读锁，只是生成快照；后续的事务可以 CRUD，并不会被阻塞

T1 | T2 | Main
--- | --- | --- 
-- | - | `SET GLOBAL TRANSACTION ISOLATION LEVEL REPEATABLE READ;`
-- | - | `TRUNCATE TABLE test;`
-- | - | `INSERT INTO test VALUES(1, 10, 'a'), (5, 20, 'b'), (8, 30, 'c'), (10, 40, 'd');`
`START TRANSACTION;` | `START TRANSACTION;` | - 
`SELECT * FROM test WHERE id <= 5;` // 不加锁  | - | - 
-- | C: `INSERT INTO test VALUES(4, 15, 'c');` // 成功  | -
-- | U: `UPDATE test SET enname = 'a' WHERE id = 5;` // 成功  | -
-- | D: `DELETE FROM test WHERE id = 5;` // 成功  | -
-- | T: `COMMIT;` // 提交数据 | -
`SELECT * FROM test WHERE id <= 5;` // 不存在幻读 | - | -

3. T1 先执行 CUR，给相关区间加写锁；后续的事务 CUD 的时候都会被阻塞，但**读不加锁**

T1 | T2 | Main
--- | --- | --- 
-- | - | `SET GLOBAL TRANSACTION ISOLATION LEVEL REPEATABLE READ;`
-- | - | `TRUNCATE TABLE test;`
-- | - | `INSERT INTO test VALUES(1, 10, 'a'), (5, 20, 'b'), (8, 30, 'c'), (10, 40, 'd');`
`START TRANSACTION;` | `START TRANSACTION;` | - 
`UPDATE test SET enname = 'a' WHERE id <= 5;` // 锁 (-∞, 5]  | - | - 
-- | R: `SELECT * FROM test;` // 成功  | -
-- | C: `INSERT INTO test VALUES(6, 35, 'c');` // 成功 | -
-- | C: `INSERT INTO test VALUES(4, 25, 'c');` // 阻塞 | -
-- | U: `UPDATE test SET enname='a' WHERE id = 8;` // 成功 | -
-- | U: `UPDATE test SET enname='a' WHERE id = 5;` // 阻塞 | -
-- | D: `DELETE FROM test WHERE id = 8;` // 成功 | -
-- | D: `DELETE FROM test WHERE id = 5;` // 阻塞 | -


---
## 提交读
1. 用**记录锁**实现

2. T1 先执行读，并不会给相关记录加读锁；后续的事务可以 CRUD，并不会被阻塞

T1 | T2 | Main
--- | --- | --- 
-- | - | `SET GLOBAL TRANSACTION ISOLATION LEVEL READ COMMITTED;`
-- | - | `TRUNCATE TABLE test;`
-- | - | `INSERT INTO test VALUES(1, 10, 'a'), (5, 20, 'b'), (8, 30, 'c'), (10, 40, 'd');`
`START TRANSACTION;` | `START TRANSACTION;` | - 
`SELECT * FROM test WHERE id <= 5;` // 不加锁  | - | - 
-- | C: `INSERT INTO test VALUES(4, 15, 'c');` // 成功  | -
-- | U: `UPDATE test SET enname = 'a' WHERE id = 5;` // 成功  | -
-- | D: `DELETE FROM test WHERE id = 5;` // 成功  | -
-- | T: `COMMIT;` // 提交数据 | -
`SELECT * FROM test WHERE id <= 5;` // 存在不可重复读、幻读 | - | -

3. T1 先执行 CUR，给相关行记录加写锁；后续的事务 CUD 的时候都会被阻塞，但**读不加锁**

T1 | T2 | Main
--- | --- | --- 
-- | - | `SET GLOBAL TRANSACTION ISOLATION LEVEL READ COMMITTED;`
-- | - | `TRUNCATE TABLE test;`
-- | - | `INSERT INTO test VALUES(1, 10, 'a'), (5, 20, 'b'), (8, 30, 'c'), (10, 40, 'd');`
`START TRANSACTION;` | `START TRANSACTION;` | -  
`UPDATE test SET enname = 'a' WHERE id <= 5;` // 锁第`1`行和第`5`行记录  | - | - 
-- | R: `SELECT * FROM test;` // 成功  | -
-- | C: `INSERT INTO test VALUES(4, 15, 'c');` // 成功 | -
-- | U: `UPDATE test SET enname = 'a' WHERE id = 8;` // 成功 | -
-- | U: `UPDATE test SET enname = 'a' WHERE id = 5;` // 阻塞 | -
-- | D: `DELETE FROM test WHERE id = 8;` // 成功 | -
-- | D: `DELETE FROM test WHERE id = 5;` // 阻塞 | -


---
## 未提交读
 1. 用**记录锁**实现
 
 2. T1 先执行读，并不会给相关记录加读锁；后续的事务可以 CRUD，并不会被阻塞

T1 | T2 | Main
--- | --- | --- 
-- | - | `SET GLOBAL TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;`
-- | - | `TRUNCATE TABLE test;`
-- | - | `INSERT INTO test VALUES(1, 10, 'a'), (5, 20, 'b'), (8, 30, 'c'), (10, 40, 'd');`
`START TRANSACTION;` | `START TRANSACTION;` | -  
`SELECT * FROM test WHERE id <= 5;` // 不加锁  | - | - 
-- | C: `INSERT INTO test VALUES(4, 15, 'c');` // 成功  | -
`SELECT * FROM test WHERE id <= 5;` // 存在幻读 | - | -
-- | U: `UPDATE test SET enname = 'a' WHERE id = 5;` // 成功  | -
-- | D: `DELETE FROM test WHERE id = 5;` // 成功  | -
-- | T: `-- COMMIT;` // 不提交数据 | -
`SELECT * FROM test WHERE id <= 5;` // 存在脏读、不重复读、幻读 | - | -

3. T1 先执行 CUR，给相关行记录加写锁；后续的事务 CUD 的时候都会被阻塞，但**读不加锁**

T1 | T2 | Main
--- | --- | --- 
-- | - | `SET GLOBAL TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;`
-- | - | `TRUNCATE TABLE test;`
-- | - | `INSERT INTO test VALUES(1, 10, 'a'), (5, 20, 'b'), (8, 30, 'c'), (10, 40, 'd');`
`START TRANSACTION;` | `START TRANSACTION;` | -  
`UPDATE test SET enname = 'a' WHERE id <= 5;` // 锁第`1`行和第`5`行记录  | - | - 
-- | R: `SELECT * FROM test;` // 成功  | -
-- | C: `INSERT INTO test VALUES(4, 15, 'c');` // 成功 | -
-- | U: `UPDATE test SET enname = 'a' WHERE id = 8;` // 成功 | -
-- | U: `UPDATE test SET enname = 'a' WHERE id = 5;` // 阻塞 | -
-- | D: `DELETE FROM test WHERE id = 8;` // 成功 | -
-- | D: `DELETE FROM test WHERE id = 5;` // 阻塞 | -


---
## 总结
隔离级别 | RW - 先读 | RW - 后 CUR] | WR - 先 CUR  | WR - 后读
-- | -- | -- | -- | --
顺序读   | 给区间加 Next-Key 读锁 | 读任意执行，CUD 阻塞 | 给区间加 Next-Key 写锁 | CURD 都阻塞
可重复读 | 不加锁 | 任意执行 | 加 Next-Key 锁      | 读任意执行，CUD 阻塞
提交读   | 不加锁 | 任意执行 | 给行加写锁（记录锁） | 读任意执行，CUD 阻塞
未提交读 | 不加锁 | 任意执行 | 给行加写锁（记录锁） | 读任意执行，CUD 阻塞


## 注：
1. 如果是`id = 5`的操作，只是用行锁
2. 不同隔离级别之间也是按锁规则执行（如 T1 顺序读，T2 未提交读）
3. MySQL 默认是隐式添加事务操作，即 T1 事务开启未释放锁，用户 T2 未开启事务时的操作也会阻塞

## 非索引列上操作
- 示例：
```SQL
T1:
  UPDATE test SET enname = 'a' WHERE age <= 10;
T2: 
  INSERT INTO test VALUES(9, 11, 'c'); -- 检验 Next-Key 锁
  INSERT INTO test VALUES(9, 41, 'c'); -- 检验表锁
  UPDATE test SET enname = 'a' WHERE age > 20; -- 检验表锁
  UPDATE test SET enname = 'a' WHERE age < 20; -- 检验行锁
```
级别 | 锁情况
--- | ---
顺序读 | 锁表
可重复读 | 锁表
提交读 | 锁行
未提交读 | 锁行

### 注
- **锁表**说明：没索引，不好计算 Next-Key，因此锁表