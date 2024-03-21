## Unit-Test
- `RedissonLockTest`

## 说明
- 源码类：`RedissonLock`
```java
// 加锁入口
@Override
public void lock() { 
    lock(-1, null, false);
}

/*** 加锁实现 */
private void lock(long leaseTime, TimeUnit unit, boolean interruptibly) {
    long threadId = Thread.currentThread().getId();
    Long ttl = tryAcquire(-1, leaseTime, unit, threadId);
    if (ttl == null) {
        return; // 加锁成功，返回
    }

    // 加锁失败进行订阅
    CompletableFuture<RedissonLockEntry> future = subscribe(threadId); 
    pubSub.timeout(future);
    RedissonLockEntry entry;
    if (interruptibly) {
        entry = commandExecutor.getInterrupted(future);
    } else { // 默认进入这一步
        entry = commandExecutor.get(future);
    }

    try {
        while (true) { // 循环尝试加锁
            ttl = tryAcquire(-1, leaseTime, unit, threadId);
            // lock acquired
            if (ttl == null) { // 获锁成功
                break;
            }
            ...
        }
    } finally {
        // 加锁成功退出时，取消订阅
        unsubscribe(entry, threadId);
    }
}

/*** 尝试获取锁 */
private Long tryAcquire(long waitTime, long leaseTime, TimeUnit unit, long threadId) {
    // 调用异步获取锁，get() 转换成同步
    return get(tryAcquireAsync(waitTime, leaseTime, unit, threadId));
}

/*** 异步获取锁 */
private <T> RFuture<Long> tryAcquireAsync(long waitTime, long leaseTime, TimeUnit unit, long threadId) {
    RFuture<Long> ttlRemainingFuture;
    if (leaseTime > 0) {
        ttlRemainingFuture = tryLockInnerAsync(waitTime, leaseTime, unit, threadId, RedisCommands.EVAL_LONG);
    } else { // 默认进入这一步
        ttlRemainingFuture = tryLockInnerAsync(waitTime, internalLockLeaseTime,
                TimeUnit.MILLISECONDS, threadId, RedisCommands.EVAL_LONG);
    }
    CompletionStage<Long> f = ttlRemainingFuture.thenApply(ttlRemaining -> {
        // 获锁成功的回调
        // lock acquired
        if (ttlRemaining == null) {
            if (leaseTime > 0) {
                internalLockLeaseTime = unit.toMillis(leaseTime);
            } else { // 默认进入这一步
                // 开启锁续期定时任务
                scheduleExpirationRenewal(threadId);
            }
        }
        return ttlRemaining;
    });
    return new CompletableFutureWrapper<>(f);
}

/*** Lua 获锁实现 */
<T> RFuture<T> tryLockInnerAsync(long waitTime, long leaseTime, TimeUnit unit, long threadId, RedisStrictCommand<T> command) {
    return evalWriteAsync(getRawName(), LongCodec.INSTANCE, command,
            "if ((redis.call('exists', KEYS[1]) == 0) " + // 不存在
                        "or (redis.call('hexists', KEYS[1], ARGV[2]) == 1)) then " + // 或是当前线程
                    "redis.call('hincrby', KEYS[1], ARGV[2], 1); " +
                    "redis.call('pexpire', KEYS[1], ARGV[1]); " + // 设置过期时间，默认 30s
                    "return nil; " + // 返回空，表示获锁成功
                "end; " +
                "return redis.call('pttl', KEYS[1]);", // 返回被抢锁的 TTL
            Collections.singletonList(getRawName()), unit.toMillis(leaseTime), getLockName(threadId));
}

/*** 锁续约。在父类 RedissonBaseLock 里面 */
protected void scheduleExpirationRenewal(long threadId) {
    ...
    try {
        renewExpiration(); // 续约
    } finally {
        if (Thread.currentThread().isInterrupted()) {
            cancelExpirationRenewal(threadId); // 线程中断，取消续约
        }
    }
}

/*** 锁续约任务，循环调用。在父类 RedissonBaseLock 里面 */
private void renewExpiration() {
    ...
    Timeout task = commandExecutor.getConnectionManager().newTimeout(new TimerTask() {
        @Override
        public void run(Timeout timeout) throws Exception {
            ...
            CompletionStage<Boolean> future = renewExpirationAsync(threadId);
            future.whenComplete((res, e) -> {
                if (e != null) { // 出现异常，不再续约
                    EXPIRATION_RENEWAL_MAP.remove(getEntryName());
                    return;
                }
                
                if (res) {
                    renewExpiration(); // 调用自己继续续约
                } else {
                    cancelExpirationRenewal(null); // 锁已不是当前线程的，取消续约
                }
            });
        } // internalLockLeaseTime 默认为 30s(30_000)
    }, internalLockLeaseTime / 3, TimeUnit.MILLISECONDS); // 每 10s 续期一次
}

/*** Lua 锁续约实现 */
protected CompletionStage<Boolean> renewExpirationAsync(long threadId) {
    return evalWriteAsync(getRawName(), LongCodec.INSTANCE, RedisCommands.EVAL_BOOLEAN,
            "if (redis.call('hexists', KEYS[1], ARGV[2]) == 1) then " +
                    "redis.call('pexpire', KEYS[1], ARGV[1]); " + // 继续设置过期时间，默认 30s
                    "return 1; " + // 是当前线程的
                    "end; " +
                    "return 0;", // 已不是当前线程的了
            Collections.singletonList(getRawName()),
            internalLockLeaseTime, getLockName(threadId));
}
```

### 流程说明
- 加锁成功则返回，同时内部开启续约任务（每 10s 一次，续约 30s TTL）
- 加锁失败，则订阅通道，以获知别的线程释放锁的通知


## Ref
- https://zhuanlan.zhihu.com/p/135864820