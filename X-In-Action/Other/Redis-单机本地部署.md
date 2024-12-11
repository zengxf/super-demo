# Redis-单机本地部署


---
## 下载
- 可直接用 https://github.com/tporadowski/redis/releases
- 有点问题 https://github.com/redis-windows/redis-windows/releases
  - `windows redis service server can't set maximum open files to 10032 because of os error: operation not permitted.`


---
## 配置
- 创建 **start.bat**
```shell
@echo off
cd /d %~dp0
redis-server.exe redis.windows-service.conf
pause
```

- **redis.windows-service.conf** 配置文件不动
```shell
bind 127.0.0.1
protected-mode yes
port 6379
loglevel notice
logfile "server_log.txt" # 日志文件
databases 16
always-show-logo yes
```


---
## 启动
- 直接双击 **start.bat**