# Neo4j-单机部署


## 下载社区版
- 版本：`2025.11.2` 示例
- 入口：https://neo4j.com/product/community-edition/
- 进入：https://neo4j.com/deployment-center/?gdb-selfmanaged&community
  - 选择 `版本` 和 `Windows`
  - 点击下载按钮 `Download Community`
- 最终：https://go.neo4j.com/download-thanks.html?edition=community&release=2025.11.2&flavour=winzip


## 启动
- 在 `/bin` 目录下
- 创建 `neo4j21.bat` (**指定 JDK-21 运行**)
```bat
@echo off
set JAVA_HOME=D:\Install\Java\JDK\jdk-21
set PATH=%JAVA_HOME%\bin;%PATH%
call neo4j console
```

- (添加 env 后) 直接运行
```shell
# 变量 neo4j = xx/neo4j/bin

cd /d %neo4j%

neo4j21
```


## Web UI
- 访问：http://localhost:7474/browser/
- 初始默认密码：`neo4j / neo4j`
- 初次要改新密码：`abcd1234`


## 忘记密码处理
- 改 `conf/neo4j.conf` 文件
```conf
# 去掉下面的注释
dbms.security.auth_enabled=false
```

- 重启之后，重新进入
```shell
# 找到 neo4j$ 命令窗口，输入下面的命令：
ALTER USER neo4j SET PASSWORD 'abcd1234';

# 实测不行 (本地环境直接重装)
```


## 命令测试
```shell
# https://chatgpt.com/c/695b95a2-01ec-8323-9dcb-4f18374396c9

# 查看数据库命令
SHOW DATABASE;

# 查看所有节点类型（相当于“所有表”）
CALL db.labels();

# 查看所有关系类型
CALL db.relationshipTypes();

# 查看所有属性（字段）
CALL db.schema.nodeTypeProperties();

# 图模型结构一览（标签 + 关系）
CALL db.schema.visualization();


# ===================================
# ========== 查看节点的值 ============

# 查看某类节点的全部内容
MATCH (p:Person)
RETURN p;

# 只返回节点的属性字段
MATCH (p:Person)
RETURN p.name, p.age;

# 限定条件查询（WHERE）
MATCH (p:Person)
WHERE p.name = "张三"
RETURN p;

# 查看节点 ID、标签、属性分开展示
MATCH (n:Person)
RETURN id(n) AS node_id, labels(n) AS labels, properties(n) AS props
LIMIT 5;

# ========== 查看节点的值 ============
# ===================================

# +++++++++++++++++++++++++++++++++++

# ===================================
# ========== 用户相关操作 ============

# cypher-shell 进入
cypher-shell -u neo4j -p abcd1234 -d system

# 退出 
:exit

# 查看用户和角色
SHOW USERS;

# 创建普通用户
# 首次登录不用修改密码
CREATE USER alice SET PASSWORD '12345678';
# 要求首次登录修改密码
CREATE USER bob SET PASSWORD 'test1234' CHANGE REQUIRED;

# 创建后立即分配角色
# 只读访问（可查询数据）
GRANT ROLE reader TO alice;
# 给管理员权限
GRANT ROLE admin TO alice;

# 删除用户
DROP USER alice;

# ========== 用户相关操作 ============
# ===================================
```