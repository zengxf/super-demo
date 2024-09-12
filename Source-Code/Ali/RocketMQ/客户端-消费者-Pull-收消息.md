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
            ConsumeRequest consumeRequest = consumeRequestCache.poll(   // JUC 队列，数据来自定时任务，ref: 
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