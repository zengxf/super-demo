## 版本
- 5.0.14.1

## Ref
- 配置说明 https://juejin.cn/post/6995794821805768718

## 准备
- 创建目录：`D:\Data\test\Redis\sentinel`
  - 在此目录下再创建目录：
```js
> cd /d D:\Data\test\Redis\sentinel
  md master-6389-data 
  md follower-6388-data
  md sentinel-6387-data
```

## 启动
```js
> cd /d D:\MyData\pub-project\super-demo\Redis\sentinel

> redis-server   master-6389.conf
> redis-server   slave-6388.conf
// Windows 没有此命令
> redis-sentinel sentinel-6387.conf
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