# MySql 循环插入

标签（空格分隔）： DB

---

## 创建存储过程再执行
```
DROP PROCEDURE IF EXISTS per2;
CREATE PROCEDURE per2()
BEGIN
	DECLARE num INT;
	DECLARE dates VARCHAR(100);
	SET num = 1;
	SET dates = '2018-04-19 16:33:';
	WHILE num < 10 DO
		INSERT INTO t_g1 (u_date, u_name, u_value)
			VALUES
				( CONCAT(dates, num), 'cpu',  13 * num % 100 ),
				( CONCAT(dates, num), 'disk', 11 * num % 100 );
		SET num = num + 1;
	END WHILE;
END;
CALL per2();
```

### 使用变量
```
DROP PROCEDURE IF EXISTS proc_init_data;
DELIMITER ;; -- HeidiSQL 需要声明下
CREATE PROCEDURE proc_init_data()
BEGIN
	DECLARE days INT DEFAULT 30;
	DECLARE num INT DEFAULT 1;
	WHILE days > 1 DO
		WHILE num < 10 DO
			INSERT INTO user_day_active(user_id, uid, gender, `type`, daily) 
				SELECT id, uid, gender, 1, DATE_FORMAT(DATE_ADD(NOW(), INTERVAL (0 - days) DAY), '%Y%m%d') FROM user1;
			SET num = num + 1;
		END WHILE;
		SET num = 1;
		SET days = days - 1;
	END WHILE;
END;;
CALL proc_init_data();
```


