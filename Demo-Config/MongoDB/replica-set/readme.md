## 版本
- 6.0.4

## Ref
- https://juejin.cn/post/7145660938861936676
- 配置 https://www.cnblogs.com/cwp-bg/p/9479945.html
- 认证 https://cloud.tencent.com/developer/article/1799755


## 准备
- 创建目录：`D:\Data\test\MongoDB\replica-set`
  - 在此目录下再创建目录：
```js
> cd /d D:\Data\test\MongoDB\replica-set
  md primary-27027-data 
  md primary-27027-logs
  md secondary-27028-data
  md secondary-27028-logs
  md arbiter-27029-data
  md arbiter-27029-logs
```

## 启动
```js
> cd /d D:\MyData\pub-project\super-demo\MongoDB\replica-set

> mongod --config primary-27027.conf
> mongod --config secondary-27028.conf
> mongod --config arbiter-27029.conf
```

## 配置
- 随便进入一个去配置
  - 使用 **Studio 3T** 进入 `localhost:27027`
- 配置命令：
```js
// 使用 admin
use admin;

// 仲裁节点，需要配置 `arbiterOnly:true`，否则模式不生效。
// priority: 优先级（一般大于 0），越大越有机会成为主节点。
rs.initiate({ 
	_id:"TZxf", 
	members: [ 
		{ _id : 0, host : 'localhost:27027', priority : 2 }, 
		{ _id : 1, host : 'localhost:27028', priority : 1 },
		{ _id : 2, host : 'localhost:27029', arbiterOnly : true }
	] 
});
// 查看配置是否生效
rs.status();		
```

## 测试
- **primary-27027**
```js
use test;
db.test.insert({name: 'zxf', age: 22});
db.test.find();
```

- **secondary-27028**
```js
use test;
db.test.find();
// db.test.insert({name: 'test', age: 55}); // err
```

## ~~认证~~
- https://blog.51cto.com/wsxxsl/2318235
- 稍麻烦
```js
use admin;
db.createUser({user:"admin", pwd:"abc", roles: [{role: "userAdminAnyDatabase", db: "admin"}]});
show users;

// db.auth("admin", "abc");
db.grantRolesToUser("admin", [ 
  { "role": "dbOwner", db: "admin" },
  { "role": "clusterAdmin", "db": "admin" },
  { "role": "userAdminAnyDatabase", "db": "admin" },
  { "role": "dbAdminAnyDatabase", "db": "admin" }
]);
```