# RocketMQ-客户端-消费者-Pull-收消息


---
## 测试
- 参考：`rocketmq-example` 模块

- `org.apache.rocketmq.example.quickstart.Consumer`
```java
public class Consumer3 {
    public static final String CONSUMER_GROUP = "test_pull_group_1";
    public static final String NAME_SRV_ADDR = "127.0.0.1:9876";
    public static final String TOPIC = "TopicTest";

    public static void main(String[] args) throws MQClientException {
        DefaultLitePullConsumer consumer = new DefaultLitePullConsumer(CONSUMER_GROUP);
        consumer.setNamesrvAddr(NAME_SRV_ADDR);

        // 指定在全新的消费者组的情况下从哪里开始。
        consumer.setConsumeFromWhere(ConsumeFromWhere.CONSUME_FROM_FIRST_OFFSET);
        consumer.subscribe(TOPIC, "*"); // 订阅，ref: sign_m_110
        consumer.setPullBatchSize(1);
        consumer.start();               // 启动，ref: sign_m_210
        System.out.printf("Consumer Started. %n");

        for (int i = 0; i < 2; i++) {
            List<MessageExt> msgList = consumer.poll(); // 轮询拉消息，ref: sign_m_310
            String msg = msgList.stream()
                    .map(item -> String.format("  msg-item: [%s]. %n", new String(item.getBody())))
                    .collect(Collectors.joining());
            System.out.printf("%n[%s] Receive New Messages: %n%s%n", Thread.currentThread().getName(), msg);
        }
    }
}
```


---
## 初始化
- `org.apache.rocketmq.client.consumer.DefaultLitePullConsumer`
```java
// sign_c_110
public class DefaultLitePullConsumer extends ClientConfig implements LitePullConsumer {

    private String consumerGroup;
    private final DefaultLitePullConsumerImpl defaultLitePullConsumerImpl;  // ref: sign_c_120


    // sign_cm_110  构造器
    public DefaultLitePullConsumer(final String consumerGroup) {
        this(consumerGroup, null);  // ref: sign_cm_111
    }

    // sign_cm_111  构造器
    public DefaultLitePullConsumer(final String consumerGroup, RPCHook rpcHook) {
        this.consumerGroup = consumerGroup;
        this.enableStreamRequestType = true;
        defaultLitePullConsumerImpl = new DefaultLitePullConsumerImpl(this, rpcHook);
    }

    // sign_m_110  订阅 Topic
    @Override
    public void subscribe(String topic, String subExpression) throws MQClientException {
        this.defaultLitePullConsumerImpl.subscribe(withNamespace(topic), subExpression);  // ref: sign_m_120
    }
}
```

- `org.apache.rocketmq.client.impl.consumer.DefaultLitePullConsumerImpl`
```java
// sign_c_120
public class DefaultLitePullConsumerImpl implements MQConsumerInner {

    private final DefaultMQPushConsumer defaultMQPushConsumer;
    private final RPCHook rpcHook;
    private long pullTimeDelayMillsWhenException = 1000;

    private final RebalanceImpl rebalanceImpl = new RebalancePushImpl(this);


    // sign_cm_120  构造器
    public DefaultLitePullConsumerImpl(final DefaultLitePullConsumer defaultLitePullConsumer, final RPCHook rpcHook) {
        this.defaultLitePullConsumer = defaultLitePullConsumer;
        this.rpcHook = rpcHook;
        this.scheduledThreadPoolExecutor = new ScheduledThreadPoolExecutor(
            this.defaultLitePullConsumer.getPullThreadNums(),
            new ThreadFactoryImpl("PullMsgThread-" + this.defaultLitePullConsumer.getConsumerGroup())
        );
        this.scheduledExecutorService = Executors.newSingleThreadScheduledExecutor(new ThreadFactoryImpl("MonitorMessageQueueChangeThread"));
        this.pullTimeDelayMillsWhenException = defaultLitePullConsumer.getPullTimeDelayMillsWhenException();
    }

    // sign_m_120  订阅 Topic
    public synchronized void subscribe(String topic, String subExpression) throws MQClientException {
        try {
            ... // check
            setSubscriptionType(SubscriptionType.SUBSCRIBE);
            SubscriptionData subscriptionData = FilterAPI.buildSubscriptionData(topic, subExpression);
            this.rebalanceImpl.getSubscriptionInner().put(topic, subscriptionData);
            this.defaultLitePullConsumer.setMessageQueueListener(new MessageQueueListenerImpl());
            assignedMessageQueue.setRebalanceImpl(this.rebalanceImpl);
            ...
        } ... // catch
    }
}
```


---
## 启动
- `org.apache.rocketmq.client.consumer.DefaultLitePullConsumer`
```java
// sign_c_210
public class DefaultLitePullConsumer extends ClientConfig implements LitePullConsumer {

    // sign_m_210  启动消费者
    @Override
    public void start() throws MQClientException {
        setTraceDispatcher();
        setConsumerGroup(NamespaceUtil.wrapNamespace(this.getNamespace(), this.consumerGroup));
        this.defaultLitePullConsumerImpl.start();   // ref: sign_m_220
        ...
    }
}
```

- `org.apache.rocketmq.client.impl.consumer.DefaultLitePullConsumerImpl`
  - 客户端实例初始化参考：[Admin-命令工具#初始化客户端 sign_cm_330](./Admin-命令工具.md#初始化客户端)
  - 客户端实例启动参考：[Admin-命令工具#初始化客户端 sign_m_330](./Admin-命令工具.md#初始化客户端)
```java
// sign_c_220
public class DefaultLitePullConsumerImpl implements MQConsumerInner {
    
    // sign_m_220  启动
    public synchronized void start() throws MQClientException {
        switch (this.serviceState) {
            case CREATE_JUST:
                ... // check

                initMQClientFactory();  // 初始化客户端实例，ref: sign_m_221
                initRebalanceImpl();    // 初始化负载均衡
                initPullAPIWrapper();   // 初始化包装器
                initOffsetStore();      // 初始化偏移量存储
                mQClientFactory.start();// 客户端实例启动参考：[Admin-命令工具#初始化客户端 sign_m_330]
                ...

                break;
            ... // 其他状态直接异常
        }
    }

    // sign_m_221  初始化客户端实例
    private void initMQClientFactory() throws MQClientException {
        // 客户端实例初始化参考：[Admin-命令工具#初始化客户端 sign_cm_330]
        this.mQClientFactory = MQClientManager.getInstance().getOrCreateMQClientInstance(this.defaultLitePullConsumer, this.rpcHook);
        boolean registerOK = mQClientFactory.registerConsumer(this.defaultLitePullConsumer.getConsumerGroup(), this);
        ...
    }

}
```


---
## 轮询
- `org.apache.rocketmq.client.consumer.DefaultLitePullConsumer`
```java
// sign_c_310
public class DefaultLitePullConsumer extends ClientConfig implements LitePullConsumer {

    // sign_m_310  轮询消息
    @Override
    public List<MessageExt> poll() {
        return defaultLitePullConsumerImpl.poll(    // 轮询消息，ref: sign_m_320
            this.getPollTimeoutMillis()             // 5s
        );
    }
}
```

- `org.apache.rocketmq.client.impl.consumer.DefaultLitePullConsumerImpl`
```java
// sign_c_320
public class DefaultLitePullConsumerImpl implements MQConsumerInner {

    // sign_m_320   限时轮询消息
    public synchronized List<MessageExt> poll(long timeout) {
        try {
            ... // check

            if (defaultLitePullConsumer.isAutoCommit()) {
                maybeAutoCommit();  // 记录消费偏移量
            }

            long endTime = System.currentTimeMillis() + timeout;
            ConsumeRequest consumeRequest = consumeRequestCache.poll(   // JUC 队列，数据来自定时任务，ref: sign_m_314
                endTime - System.currentTimeMillis(), TimeUnit.MILLISECONDS
            );
            ...

            if (consumeRequest != null && !consumeRequest.getProcessQueue().isDropped()) {
                List<MessageExt> messages = consumeRequest.getMessageExts();    // 获取请求里面的消息
                
                ... // 偏移量和其他处理
                ... // 钩子处理

                consumeRequest.getProcessQueue().setLastConsumeTimestamp(System.currentTimeMillis());
                return messages;
            }
        } ... // catch
        
        return Collections.emptyList();
    }
}
```


---
## 定时拉取任务
- 启动
  - 负载均衡处理任务启动时，会调用客户端实例做尝试处理
  - 队列变更时，调用相应的监听器进行处理
  - 监听器处理时，会启动拉取任务 (ref: `sign_c_420`)
- 调用栈如下：
```js
// new RuntimeException("定时拉取任务启动调用栈").printStackTrace();

java.lang.RuntimeException: 定时拉取任务启动调用栈
	at *.consumer.DefaultLitePullConsumerImpl.startPullTask(DefaultLitePullConsumerImpl.java:446)   // ref: sign_m_310
	at *.consumer.DefaultLitePullConsumerImpl.updatePullTask(DefaultLitePullConsumerImpl.java:237)
	at *.consumer.DefaultLitePullConsumerImpl.updateAssignQueueAndStartPullTask(DefaultLitePullConsumerImpl.java:256)
	at *.consumer.DefaultLitePullConsumerImpl$MessageQueueListenerImpl.messageQueueChanged(DefaultLitePullConsumerImpl.java:243)
	at *.consumer.RebalanceLitePullImpl.messageQueueChanged(RebalanceLitePullImpl.java:53)
	at *.consumer.RebalanceImpl.rebalanceByTopic(RebalanceImpl.java:329)
	at *.consumer.RebalanceImpl.doRebalance(RebalanceImpl.java:250)
	at *.consumer.DefaultLitePullConsumerImpl.tryRebalance(DefaultLitePullConsumerImpl.java:1127)
	at *.factory.MQClientInstance.doRebalance(MQClientInstance.java:1069)
	at *.consumer.RebalanceService.run(RebalanceService.java:51)
	at java.lang.Thread.run(Thread.java:750)
```

- `org.apache.rocketmq.client.impl.consumer.DefaultLitePullConsumerImpl`
```java
// sign_c_410
public class DefaultLitePullConsumerImpl implements MQConsumerInner {

    // sign_m_410
    private void startPullTask(Collection<MessageQueue> mqSet) {
        for (MessageQueue messageQueue : mqSet) {
            if (!this.taskTable.containsKey(messageQueue)) {
                PullTaskImpl pullTask = new PullTaskImpl(messageQueue); // 拉取消息的执行体，ref: sign_m_420
                this.taskTable.put(messageQueue, pullTask);
                this.scheduledThreadPoolExecutor.schedule(pullTask, 0, TimeUnit.MILLISECONDS);
            }
        }
    }

    // sign_m_411
    private PullResult pull(MessageQueue mq, SubscriptionData subscriptionData, long offset, int maxNums) throws ... {
        return pull(mq, subscriptionData, offset, maxNums, this.defaultLitePullConsumer.getConsumerPullTimeoutMillis());    // ref: sign_m_312
    }

    // sign_m_412
    private PullResult pull(MessageQueue mq, SubscriptionData subscriptionData, long offset, int maxNums, long timeout) throws ... {
        return this.pullSyncImpl(mq, subscriptionData, offset, maxNums, true, timeout); // ref: sign_m_313
    }

    // sign_m_413
    private PullResult pullSyncImpl(
        MessageQueue mq, SubscriptionData subscriptionData, long offset, int maxNums,
        boolean block, long timeout
    ) throws ... {
        ... // check
        ...

        PullResult pullResult = this.pullAPIWrapper.pullKernelImpl(
            mq, ..., CommunicationMode.SYNC, null
        );
        this.pullAPIWrapper.processPullResult(mq, pullResult, subscriptionData);
        return pullResult;
    }

    // sign_m_414
    private void submitConsumeRequest(ConsumeRequest consumeRequest) {
        try {
            consumeRequestCache.put(consumeRequest);
        } ... // catch
    }
}
```

- `org.apache.rocketmq.client.impl.consumer.DefaultLitePullConsumerImpl.PullTaskImpl`
```java
    // sign_c_420  拉取消息的执行体
    public class PullTaskImpl implements Runnable {

        // sign_m_420  拉取消息的执行体
        @Override
        public void run() {
            if (!this.isCancelled()) {
                this.currentThread = Thread.currentThread();
                ... // check

                ProcessQueue processQueue = assignedMessageQueue.getProcessQueue(messageQueue);
                ... // check

                processQueue.setLastPullTimestamp(System.currentTimeMillis());
                ... // check

                long offset = 0L;
                try {
                    offset = nextPullOffset(messageQueue);  // CONSUME_FROM_FIRST_OFFSET 第一次返回 0
                } ... // catch
                ...

                long pullDelayTimeMills = 0;        // 没异常时，相当于立即再执行一次
                try {
                    SubscriptionData subscriptionData;
                    String topic = this.messageQueue.getTopic();
                    if (subscriptionType == SubscriptionType.SUBSCRIBE) {
                        subscriptionData = rebalanceImpl.getSubscriptionInner().get(topic);
                    } ... // else

                    PullResult pullResult = pull(   // 拉取数据，ref: sign_m_311
                        messageQueue, subscriptionData, offset, defaultLitePullConsumer.getPullBatchSize()
                    );
                    ...

                    switch (pullResult.getPullStatus()) {
                        case FOUND:
                            final Object objLock = messageQueueLock.fetchLockObject(messageQueue);
                            synchronized (objLock) {
                                if (pullResult.getMsgFoundList() != null && !... .isEmpty() && ...) {
                                    ...
                                    // 提交请求 (相当于记录拉取的消息). ref: sign_m_314
                                    submitConsumeRequest(new ConsumeRequest(pullResult.getMsgFoundList(), ...));
                                }
                            }
                            break;
                        ... // OFFSET_ILLEGAL: default:
                    }
                    updatePullOffset(messageQueue, pullResult.getNextBeginOffset(), ...);  // 更新偏移量
                } ... // catch

                if (!this.isCancelled()) {
                    // 循环调度
                    scheduledThreadPoolExecutor.schedule(this, pullDelayTimeMills, TimeUnit.MILLISECONDS);
                } ...
            }
        }
    }
```