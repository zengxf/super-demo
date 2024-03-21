## 简介
- 执行各种命令的执行器

## 实现类
- `CommandAsyncService`

## 常用方法
- **命令**
  - `# readAsync`
    - 执行 Redis 命令**读数据**
  - `# writeAsync`
    - 执行 Redis 命令**写数据**
  - `# async`
    - 最终处理所有的命令请求
- **脚本**
  - `# evalReadAsync`
    - 执行 Lua 脚本**读数据**
  - `# evalWriteAsync`
    - 执行 Lua 脚本**写数据**
  - `# evalAsync`
    - 最终处理所有的脚本请求

## 测试
- 在 `RedissonLockTest` 加个方法
```java
    @Test
    public void testLock() {
        RLock lock = redisson.getLock("lock");
        lock.lock(10, TimeUnit.SECONDS);
        try {
            System.out.println("OK!");
        } finally {
            lock.unlock();
        }
    }

// 在 RedissonLock #tryLockInnerAsync() 方法打个断点
// 在 org.redisson.RedissonBaseLock #evalWriteAsync() 方法打个断点
// 在 org.redisson.command.CommandAsyncService #evalWriteAsync() 方法打个断点
// 没开启脚本缓存，进入 evalAsync() 后又转给 async()


    // 模拟 org.redisson.RedissonBaseLock #evalWriteAsync() 里面的代码
    @Test
    public void testCompletionStage() {
        CompletionStage<String> replicationFuture = CompletableFuture.completedFuture("test-001");
        CompletionStage<String> resFuture = replicationFuture.thenCompose(r -> { // 会立即执行进来
            System.out.println("r: " + r);
            return CompletableFuture.completedFuture("OK-123");
        });
        resFuture.thenAccept(res -> System.out.println("res: " + res));
    }
```

## 说明
- `org.redisson.command.CommandAsyncService`
```java
public class CommandAsyncService implements CommandAsyncExecutor {
    /*** 执行各种 Redis 命令 */
    public <V, R> RFuture<R> async(boolean readOnlyMode, NodeSource source, Codec codec,
            RedisCommand<V> command, Object[] params, boolean ignoreRedirect, boolean noRetry) {
        ...
        CompletableFuture<R> mainPromise = createPromise(); // promise 模式
        // 构建执行器
        RedisExecutor<V, R> executor = new RedisExecutor<>(readOnlyMode, source, codec, command, params, mainPromise,
                                                    ignoreRedirect, connectionManager, objectBuilder, referenceType, noRetry);
        executor.execute(); // 执行
        return new CompletableFutureWrapper<>(mainPromise);
    }
    /*** 执行各种 Lua 脚本 */
    private <T, R> RFuture<R> evalAsync(NodeSource nodeSource, boolean readOnlyMode, Codec codec, RedisCommand<T> evalCommandType,
                                        String script, List<Object> keys, boolean noRetry, Object... params) {
        if (isEvalCacheActive() && evalCommandType.getName().equals("EVAL")) { // 默认没有开启缓存
            // promise 模式
            CompletableFuture<R> mainPromise = new CompletableFuture<>();
            ...
            List<Object> args = new ArrayList<Object>(2 + keys.size() + params.length);
            args.add(sha1);
            ...
            // 构建执行器
            RedisExecutor<T, R> executor = new RedisExecutor<>(readOnlyMode, nodeSource, codec, cmd,
                                                        args.toArray(), promise, false,
                                                        connectionManager, objectBuilder, referenceType, noRetry);
            executor.execute(); // 执行
            promise.whenComplete((res, e) -> { // promise 回调
                if (e != null) {
                    if (e.getMessage().startsWith("ERR unknown command")) {
                        evalShaROSupported.set(false);
                        // 重试
                        RFuture<R> future = evalAsync(nodeSource, readOnlyMode, codec, evalCommandType, script, keys, noRetry, pps);
                        transfer(future.toCompletableFuture(), mainPromise);
                    } else if (e.getMessage().startsWith("NOSCRIPT")) {
                        ...
                        // 保存 Lua 脚本
                    } else {
                        free(pps);
                        mainPromise.completeExceptionally(e); // 有错误，异常完成
                    }
                    return;
                }
                free(pps);
                mainPromise.complete(res); // 没有错误，完成
            });
            return new CompletableFutureWrapper<>(mainPromise);
        }
        ...
        // 未开启缓存或不是 EVAL 脚本，则调用 async() 命令执行
        return async(readOnlyMode, nodeSource, codec, evalCommandType, args.toArray(), false, noRetry);
    }
}
```

- `org.redisson.command.RedisExecutor`
```java
    /*** 执行 */
    public void execute() {
        ...
        // 获取连接
        CompletableFuture<RedisConnection> connectionFuture = getConnection();
        ...
        connectionFuture.whenComplete((connection, e) -> { // 获取连接后的处理逻辑
            ...
            // 发送命令 
            sendCommand(attemptPromise, connection);
            ...
        });
        ...
    }
    /*** 发送命令 */
    protected void sendCommand(CompletableFuture<R> attemptPromise, RedisConnection connection) {
        if (source.getRedirect() == Redirect.ASK) {
            ...
        } else {
            ...
            // 使用 RedisConnection 发送数据
            writeFuture = connection.send(new CommandData<>(attemptPromise, codec, command, params));
            ...
        }
    }
```

- `org.redisson.client.RedisConnection`
```java
    /*** 调用 Netty 发送数据 */
    public <T, R> ChannelFuture send(CommandData<T, R> data) {
        return channel.writeAndFlush(data);
    }
```