## 总说明
- 源码仓库： https://github.com/redisson/redisson
- 克隆：`git clone git@github.com:redisson/redisson.git`
- 切分支（tag）：`git checkout redisson-3.19.3`


### 单元测试配置
- 本地 `redis-server.exe` 配置，在 redisson 模块下的 `RedissonRuntimeEnvironment` 更改
- Redisson 配置，在 redisson 模块下的 `BaseTest` 更改


### 内容
- 基础
  - [获取连接原理](获取连接原理.md)
  - [CommandAsyncExecutor-原理](CommandAsyncExecutor-原理.md)
- 组件
  - [DelayedQueue-原理](DelayedQueue-原理.md)
  - [Lock-加锁原理](Lock-加锁原理.md)
  - [MapCache-原理](MapCache-原理.md)