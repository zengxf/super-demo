## Unit-Test
- `RedissonDelayedQueueTest`

### 常规测试
```java
@Test
public void testCommon() throws InterruptedException {
    RBlockingQueue<String> destinationQueue = redisson.getBlockingQueue("delay_queue"); // 目标队列
    RDelayedQueue<String> delayedQueue = redisson.getDelayedQueue(destinationQueue); // 只是对目标队列的一个封装

    destinationQueue.offer("22_1");
    destinationQueue.offer("22_2");
    delayedQueue.offer("1_1_1", 2, TimeUnit.SECONDS);
    delayedQueue.offer("1_1_2", 3, TimeUnit.SECONDS);

    for (int i = 0; i < 4; i++) {
        String e0 = destinationQueue.poll();
        System.out.println("=========> e0: " + e0);
    }

    Thread.sleep(2000);
    System.out.println("------------------");
    for (int i = 0; i < 2; i++) {
        String e1 = destinationQueue.poll();
        System.out.println("=========> e1: " + e1);
    }

    Thread.sleep(2000);
    System.out.println("------------------");
    for (int i = 0; i < 2; i++) {
        String e2 = destinationQueue.poll();
        System.out.println("=========> e2: " + e2);
    }
}

// 输出
=========> e0: 22_1
=========> e0: 22_2
=========> e0: null
=========> e0: null
------------------
// 等待 2s 之后，才获取到
=========> e1: 1_1_1
=========> e1: null
------------------
// 再等 2s 之后，才获取到
=========> e2: 1_1_2
=========> e2: null
```

## 说明
- 源码类：`RedissonDelayedQueue`
```java
/*** 构造器，将目标队列转入，并启用定时转移任务 */
protected RedissonDelayedQueue(QueueTransferService queueTransferService, Codec codec, final CommandAsyncExecutor commandExecutor, String name) {
    super(codec, commandExecutor, name);
    channelName = prefixName("redisson_delay_queue_channel", getRawName());
    queueName = prefixName("redisson_delay_queue", getRawName());
    timeoutSetName = prefixName("redisson_delay_queue_timeout", getRawName());
    
    QueueTransferTask task = new QueueTransferTask(commandExecutor.getConnectionManager()) {
        @Override
        protected RFuture<Long> pushTaskAsync() {
            return commandExecutor.evalWriteAsync(getRawName(), LongCodec.INSTANCE, RedisCommands.EVAL_LONG,
                    "local expiredValues = redis.call('zrangebyscore', KEYS[2], 0, ARGV[1], 'limit', 0, ARGV[2]); "
                    + "if #expiredValues > 0 then "
                        + "for i, v in ipairs(expiredValues) do "
                            + "local randomId, value = struct.unpack('dLc0', v);"
                            + "redis.call('rpush', KEYS[1], value);" // 添加到目标队列里面去
                            + "redis.call('lrem', KEYS[3], 1, v);" // 删除缓存队列
                        + "end; "
                        + "redis.call('zrem', KEYS[2], unpack(expiredValues));" // 删除延迟排序的任务
                    + "end; "
                    // get startTime from scheduler queue head task
                    + "local v = redis.call('zrange', KEYS[2], 0, 0, 'WITHSCORES'); "
                    + "if v[1] ~= nil then "
                        + "return v[2]; "
                    + "end "
                    + "return nil;",
                    Arrays.asList(getRawName(), timeoutSetName, queueName),
                    System.currentTimeMillis(), 100);
        }
        ...
    };
    
    // 开启任务
    queueTransferService.schedule(queueName, task);
    
    this.queueTransferService = queueTransferService;
}

/*** 添加延时的队列元素 */
@Override
public void offer(V e, long delay, TimeUnit timeUnit) {
    get(offerAsync(e, delay, timeUnit));
}

/*** Lua 添加延时的队列元素 */
@Override
public RFuture<Void> offerAsync(V e, long delay, TimeUnit timeUnit) {
    ...

    long delayInMs = timeUnit.toMillis(delay);
    long timeout = System.currentTimeMillis() + delayInMs;
    
    long randomId = ThreadLocalRandom.current().nextLong();
    return commandExecutor.evalWriteNoRetryAsync(getRawName(), codec, RedisCommands.EVAL_VOID,
            "local value = struct.pack('dLc0', tonumber(ARGV[2]), string.len(ARGV[3]), ARGV[3]);" 
            + "redis.call('zadd', KEYS[2], ARGV[1], value);" // 添加到 ZSet 排序
            + "redis.call('rpush', KEYS[3], value);" // 添加到缓存队列
            // if new object added to queue head when publish its startTime 
            // to all scheduler workers 
            + "local v = redis.call('zrange', KEYS[2], 0, 0); "
            + "if v[1] == value then "
                + "redis.call('publish', KEYS[4], ARGV[1]); "
            + "end;",
            Arrays.asList(getRawName(), timeoutSetName, queueName, channelName),
            timeout, randomId, encode(e));
}
```