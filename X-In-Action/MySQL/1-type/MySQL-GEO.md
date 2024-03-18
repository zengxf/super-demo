## 参考
- https://blog.51cto.com/u_15127678/4355762
- https://www.sjkjc.com/mysql-ref/geometry-datatype/
- https://blog.csdn.net/wisfy_21/article/details/124180133
- http://mysql.taobao.org/monthly/2021/07/06/

## 测试
### 建表
```sql
CREATE TABLE `test_type` (
  `id` int DEFAULT NULL,
  `v_point` point DEFAULT NULL,
  `v_polygon` polygon DEFAULT NULL,
  `v_geometry` geometry DEFAULT NULL
) ENGINE=InnoDB;
```

### 插入数据
```sql
INSERT INTO test_type (id, v_point)
    VALUES (1, POINT(-73.935242, 40.730610));

INSERT INTO test_type (id, v_polygon)
    VALUES (2, ST_GeomFromText('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0), (5 5, 7 5, 7 7, 5 7, 5 5))'));

INSERT INTO test_type (id, v_geometry)
    VALUES (3, ST_GeomFromText('LINESTRING(0 0, 10 10, 20 25, 50 60)'));
```

### 查询
```sql
SELECT 
    id,

    ST_AsText(v_point) AS v_point_text, 
    ST_X(v_point) AS v_point_x, ST_Y(v_point) AS v_point_y,
	ST_AsGeoJSON(v_point) AS v_point_json,
    
    ST_AsText(v_polygon) AS v_polygon_text, 
	ST_AsGeoJSON(v_polygon) AS v_polygon_json,
    
    ST_AsText(v_geometry) AS v_geometry_text, 
	ST_AsGeoJSON(v_geometry) AS v_geometry_json,
    
    'xx'
FROM test_type;
```

### 看各类型数据
```sql
-- 查看点 Point 经纬度
SELECT ST_AsGeoJSON( ST_GeomFromText('POINT(0 0)') );

-- 查看线 LineString
SELECT ST_AsGeoJSON( ST_GeomFromText('LINESTRING(0 0, 10 10, 20 25, 50 60)') );

-- 查看边界 Polygon
SELECT ST_AsGeoJSON( ST_GeomFromText('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0), (5 5, 7 5, 7 7, 5 7, 5 5))') );
```