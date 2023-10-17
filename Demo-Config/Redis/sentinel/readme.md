## 版本
- 5.0.14.1

## Ref
- 配置说明 https://juejin.cn/post/6995794821805768718
- Redis学习之哨兵模式 https://www.cnblogs.com/tanghaorong/p/14339453.html

## 准备
- 创建目录：`D:\Data\test\Redis\sentinel`
  - 在此目录下再创建目录：
```js
> cd /d D:\Data\test\Redis\sentinel
  md master-6389-data 
  md slave-6388-data
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
PS C:\Users\feng> redis-cli -h 127.0.0.1 -p 6389

// master
127.0.0.1:6389> set testa abc123
OK
127.0.0.1:6389> get testa
"abc123"
127.0.0.1:6389>

// slave
PS C:\Users\feng>  redis-cli -h 127.0.0.1 -p 6388
127.0.0.1:6388> get testa
"abc123"
127.0.0.1:6388> set testb abc
(error) READONLY You can't write against a read only replica.
127.0.0.1:6388>
```