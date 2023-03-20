## 版本
- 5.0.14.1

## Ref
- %Redis%`/redis.windows-service.conf`
- 配置说明 https://www.runoob.com/redis/redis-conf.html

## 准备
- 设置 Redis 到 `%Path%`
- 创建目录：`D:\Data\test\Redis\stand-alone`
  - 在此目录下再创建目录：`data`

## 启动
```js
> cd /d D:\MyData\pub-project\super-demo\Redis\stand-alone

> redis-server redis-6379.conf
```

## 测试
```js
C:\Users\feng> redis-cli

127.0.0.1:6379> set t1 abc
OK
127.0.0.1:6379> get t2
(nil)
127.0.0.1:6379> get t1
"abc"
127.0.0.1:6379>
```