# MySQL-5.7 JSON

标签（空格分隔）： DB

---

```SQL
CREATE TABLE t1 (jdoc JSON);
INSERT INTO t1 VALUES('{"key1": "value1", "key2": "value2"}');

SELECT JSON_TYPE('["a", "b", 1]');	SELECT JSON_TYPE('"hello"');

SELECT JSON_ARRAY('a', 1, NOW());

SELECT JSON_OBJECT('key1', 1, 'key2', 'abc');

SELECT JSON_MERGE('["a", 1]', '{"key": "value"}');

SET @j = JSON_OBJECT('key', 'value');
SELECT @j;
SELECT CHARSET(@j), COLLATION(@j);

SELECT JSON_ARRAY('x') = JSON_ARRAY('X');

SELECT JSON_VALID('null'), JSON_VALID('Null'), JSON_VALID('NULL');

SELECT CAST('null' AS JSON);

SELECT JSON_OBJECT('key1', 1, 'key2', 'abc', 'key1', 'def');

SELECT JSON_MERGE('[1, 2]', '["a", "b"]', '[true, false]');
SELECT JSON_MERGE('{"a": 1, "b": 2}', '{"c": 3, "a": 4}');
SELECT JSON_MERGE('1', '2');
SELECT JSON_MERGE('[10, 20]', '{"a": "x", "b": "y"}');

SELECT JSON_EXTRACT('{"id": 14, "name": "Aztalan"}', '$.name');
SELECT JSON_EXTRACT('{"a": 1, "b": 2, "c": [3, 4, 5]}', '$.*');
SELECT JSON_EXTRACT('{"a": 1, "b": 2, "c": [3, 4, 5]}', '$.c[*]');
SELECT JSON_EXTRACT('{"a": {"b": 1}, "c": {"b": 2}}', '$**.b');

SET @j = '["a", {"b": [true, false]}, [10, 20]]';
SELECT JSON_SET(@j, '$[1].b[0]', 1, '$[2][2]', 2);
SELECT JSON_INSERT(@j, '$[1].b[0]', 1, '$[2][2]', 2);
SELECT JSON_REPLACE(@j, '$[1].b[0]', 1, '$[2][2]', 2);
SELECT JSON_REMOVE(@j, '$[2]', '$[1].b[1]', '$[1].b[1]');

SELECT JSON_OBJECT('key1', 1, 'key2', 'abc') = JSON_OBJECT('key2', 'abc', 'key1', 1);
SELECT '{"a": 1, "b": 2}' = '{"b": 2, "a": 1}';		// String
SELECT CAST('{"b": 2, "a": 1}' AS JSON);			// JSON

SELECT JSON_QUOTE('null');
SELECT JSON_QUOTE('[1, 2, 3]');

SET @j = '{"a": 1, "b": 2, "c": {"d": 4}}';
SET @j2 = '1';
SELECT JSON_CONTAINS(@j, @j2, '$.a');

SET @j = '{"a": 1, "b": 2, "c": {"d": 4}}';
SELECT JSON_CONTAINS_PATH(@j, 'one', '$.a', '$.e');

SELECT jdoc -> "$.key1" FROM t1;
SELECT JSON_UNQUOTE( jdoc -> "$.key1" ) FROM t1;
SELECT jdoc ->> "$.key1" FROM t1;
EXPLAIN SELECT jdoc ->> "$.key1" FROM t1 \G
SHOW WARNINGS \G

SELECT JSON_KEYS('{"a": 1, "b": {"c": 30}}');
SELECT JSON_KEYS('{"a": 1, "b": {"c": 30}}', '$.b');

SET @j = '["abc", [{"k": "10"}, "def"], {"x":"abc"}, {"y":"bc%d"}]';
SELECT JSON_SEARCH(@j, 'one', 'abc');
SELECT JSON_SEARCH(@j, 'all', 'abc');
SELECT JSON_SEARCH(@j, 'all', 'ghi');
SELECT JSON_SEARCH(@j, 'all', '10');
SELECT JSON_SEARCH(@j, 'all', 'abc', NULL, '$[2]');
SELECT JSON_SEARCH(@j, 'all', '%a%');
SELECT JSON_SEARCH(@j, 'all', '%b%', NULL, '$[2]');
SELECT JSON_SEARCH(@j, 'all', '\%', '\', '$[2]');
SELECT JSON_SEARCH(@j, 'all', '%;%%', ';');

SET @j = '["a", ["b", "c"], "d"]';
SELECT JSON_ARRAY_APPEND(@j, '$[1]', 1);
SET @j = '{"a": 1, "b": [2, 3], "c": 4}';
SELECT JSON_ARRAY_APPEND(@j, '$.c', 'y');

SET @j = '["a", {"b": [1, 2]}, [3, 4]]';
SELECT JSON_ARRAY_INSERT(@j, '$[1]', 'x');
SELECT JSON_ARRAY_INSERT(@j, '$[100]', 'x');
SELECT JSON_ARRAY_INSERT(@j, '$[0]', 'x', '$[3][1]', 'y');

SET @j = '{ "a": 1, "b": [2, 3]}';
SELECT JSON_INSERT(@j, '$.a', 10, '$.c', '[true, false]');

SELECT JSON_DEPTH('{}'), JSON_DEPTH('[]'), JSON_DEPTH('true');
SELECT JSON_DEPTH('[10, 20]'), JSON_DEPTH('[[], {}]');
SELECT JSON_DEPTH('[10, {"a": 20}]');

SELECT JSON_LENGTH('[1, 2, {"a": 3}]');
SELECT JSON_LENGTH('{"a": 1, "b": {"c": 30}}');
SELECT JSON_LENGTH('{"a": 1, "b": {"c": 30}}', '$.b');

SET @j = '{"a": [10, true]}';
SELECT JSON_TYPE(@j);
SELECT JSON_TYPE(JSON_EXTRACT(@j, '$.a'));
SELECT JSON_TYPE(JSON_EXTRACT(@j, '$.a[0]'));
SELECT JSON_TYPE(JSON_EXTRACT(@j, '$.a[1]'));

SELECT JSON_VALID('{"a": 1}');
SELECT JSON_VALID('hello'), JSON_VALID('"hello"');

-- 数组变行
SELECT 
	label, COUNT(*) AS total
FROM (
	SELECT 
		JSON_EXTRACT(ami.label, CONCAT('$[', n.n, ']')) AS label
	FROM 
	(
		SELECT anti_result -> '$**.label' AS label
		FROM anti_message_info WHERE from_user_id = 1320929881424007191
	) ami JOIN (
		SELECT 0 AS n UNION 
		SELECT 1 AS n UNION 
		SELECT 2 AS n UNION 
		SELECT 3 AS n UNION 
		SELECT 4 AS n 
	) n ON JSON_EXTRACT(ami.label, CONCAT('$[', n.n, ']')) IS NOT NULL
) t
GROUP BY label;


-- JSON 转 Table
-- 参考 https://developer.aliyun.com/article/768446
SELECT
    main.id, main.remark, 
    t.*
FROM 
    json_data main,     -- 业务主表
    JSON_TABLE(
        main.obj_arr,   -- JSON 列
        '$[*]'
        COLUMNS (
            id FOR ORDINALITY,  -- 生成一个从 1 开始的计数器列
            x INT PATH '$.x' DEFAULT '-1' ON EMPTY,  -- 使用默认值
            y INT PATH '$.y'
        )
    ) AS t;
```