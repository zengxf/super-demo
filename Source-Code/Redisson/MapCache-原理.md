## Unit-Test
- `RedissonMapCacheTest`

## 说明
- 源码类：`RedissonMapCache`
```java
// put 并设置 ttl
@Override
public V put(K key, V value, long ttl, TimeUnit unit) {
    return get(putAsync(key, value, ttl, unit));
}

/*** 异步 put */
@Override
public RFuture<V> putAsync(K key, V value, long ttl, TimeUnit ttlUnit) {
    return putAsync(key, value, ttl, ttlUnit, 0, null);
}

/*** 异步 put 实现 */
@Override
public RFuture<V> putAsync(K key, V value, long ttl, TimeUnit ttlUnit, long maxIdleTime, TimeUnit maxIdleUnit) {
    ...
    long ttlTimeout = 0;
    long ttlTimeoutDelta = 0;
    if (ttl > 0) {
        ttlTimeoutDelta = ttlUnit.toMillis(ttl); // 计算 ttl，单位 ms
        ttlTimeout = System.currentTimeMillis() + ttlTimeoutDelta; // 计算过期的时间戳
    }

    ...
    RFuture<V> future = putOperationAsync(key, value, ttlTimeout, maxIdleTimeout, maxIdleDelta, ttlTimeoutDelta);
    if (hasNoWriter()) { // 默认走到这一步，返回了
        return future;
    }
    ...
}

/*** Lua 添加 kv 实现 */
protected RFuture<V> putOperationAsync(K key, V value, long ttlTimeout, long maxIdleTimeout,
        long maxIdleDelta, long ttlTimeoutDelta) {
    String name = getRawName(key); // 啥都没做，直接返回 name
    RFuture<V> future = commandExecutor.evalWriteAsync(name, codec, RedisCommands.EVAL_MAP_VALUE,
            "local insertable = false; "
                ...
                    // 使用 ZSet 管理 ttl
                    + "if tonumber(ARGV[2]) > 0 then "
                        + "redis.call('zadd', KEYS[2], ARGV[2], ARGV[5]); "
                    + "else "
                        + "redis.call('zrem', KEYS[2], ARGV[5]); "
                    + "end; "

                    ...

                    + "local value = struct.pack('dLc0', ARGV[4], string.len(ARGV[6]), ARGV[6]); "
                    + "redis.call('hset', KEYS[1], ARGV[5], value); " // 添加到 Hash 里去

                    ...

                    + "return val",
            Arrays.asList(name, getTimeoutSetName(name), getIdleSetName(name), getCreatedChannelName(name),
                    getUpdatedChannelName(name), getLastAccessTimeSetName(name), getRemovedChannelName(name), getOptionsName(name)),
            System.currentTimeMillis(), ttlTimeout, maxIdleTimeout, maxIdleDelta, encodeMapKey(key), encodeMapValue(value));
    return future;
}
```

### 过期处理
```java
/*** RedissonMapCache 构造器会创建定时任务 */
public RedissonMapCache(EvictionScheduler evictionScheduler, CommandAsyncExecutor commandExecutor,
                        String name, RedissonClient redisson, MapOptions<K, V> options, WriteBehindService writeBehindService) {
    super(commandExecutor, name, redisson, options, writeBehindService);
    if (evictionScheduler != null) {
        evictionScheduler.schedule(getRawName(), getTimeoutSetName(), getIdleSetName(), getExpiredChannelName(), getLastAccessTimeSetName());
    }
    this.evictionScheduler = evictionScheduler;
}

/*** 调度任务。在 EvictionScheduler 类 */
public void schedule(String name, String timeoutSetName, String maxIdleSetName, String expiredChannelName, String lastAccessTimeSetName) {
    // 创建删除过期 key 的任务
    EvictionTask task = new MapCacheEvictionTask(name, timeoutSetName, maxIdleSetName, expiredChannelName, lastAccessTimeSetName, executor);
    EvictionTask prevTask = tasks.putIfAbsent(name, task);
    if (prevTask == null) {
        task.schedule();
    }
}

/*** 调用任务，在任务父类 EvictionTask 里 */
public void schedule() {
    // 默认 5s 一次
    scheduledFuture = executor.getConnectionManager().getGroup().schedule(this, delay, TimeUnit.SECONDS);
}

/*** 任务具体执行方法，在任务父类 EvictionTask 里 */
@Override
public void run() {
    ...
    RFuture<Integer> future = execute(); // 具体子类的执行逻辑
    future.whenComplete((size, e) -> {
        if (e != null) {
            log.error("Unable to evict elements for '{}'", getName(), e);
            schedule(); // 循环调用
            return;
        }
        ...
        sizeHistory.add(size);
        schedule(); // 循环调用
    });
}

/*** 实现父类的钩子函数。 MapCacheEvictionTask */
@Override
RFuture<Integer> execute() {
    int latchExpireTime = Math.min(delay, 30);
    return executor.evalWriteNoRetryAsync(name, LongCodec.INSTANCE, RedisCommands.EVAL_INTEGER,
            "if redis.call('setnx', KEYS[6], ARGV[4]) == 0 then "
                + "return -1;"
            + "end;"
            + "redis.call('expire', KEYS[6], ARGV[3]); "
            // 通过 ZSet 范围查询，查找过期的 key 集合
            + "local expiredKeys1 = redis.call('zrangebyscore', KEYS[2], 0, ARGV[1], 'limit', 0, ARGV[2]); "
            + "for i, key in ipairs(expiredKeys1) do "
                + "local v = redis.call('hget', KEYS[1], key); "
                + "if v ~= false then "
                    + "local t, val = struct.unpack('dLc0', v); "
                    + "local msg = struct.pack('Lc0Lc0', string.len(key), key, string.len(val), val); "
                    + "local listeners = redis.call('publish', KEYS[4], msg); "
                    + "if (listeners == 0) then "
                        + "break;"
                    + "end; "
                + "end;"  
            + "end;"
            + "for i=1, #expiredKeys1, 5000 do "
                + "redis.call('zrem', KEYS[5], unpack(expiredKeys1, i, math.min(i+4999, table.getn(expiredKeys1)))); "
                + "redis.call('zrem', KEYS[3], unpack(expiredKeys1, i, math.min(i+4999, table.getn(expiredKeys1)))); "
                + "redis.call('zrem', KEYS[2], unpack(expiredKeys1, i, math.min(i+4999, table.getn(expiredKeys1)))); "
                // hdel 指令删除 Hash 里面过期的 key
                + "redis.call('hdel', KEYS[1], unpack(expiredKeys1, i, math.min(i+4999, table.getn(expiredKeys1)))); "
            + "end; "
            ...
            + "return #expiredKeys1 + #expiredKeys2;",
            Arrays.<Object>asList(name, timeoutSetName, maxIdleSetName, expiredChannelName, lastAccessTimeSetName, executeTaskOnceLatchName), 
            System.currentTimeMillis(), keysLimit, latchExpireTime, 1);
}
```

### 问题
- 单元测试中，任务是 5s 执行一次，但 TTL 设置为 3s 时，key 也能删除
  - **此问题不纠结**

## Ref
- Lua 解释：https://blog.csdn.net/Michelle_Zhong/article/details/126391915
- 大量 new 会创建大量任务，引起 OOM: https://juejin.cn/post/6844903842728034317