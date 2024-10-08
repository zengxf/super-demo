# RocketMQ-客户端-消费者-Push-收消息


---
## 测试
- 参考：`rocketmq-example` 模块

- `org.apache.rocketmq.example.quickstart.Consumer`
```java
public class Consumer2 {
    public static final String CONSUMER_GROUP = "test_push_group_1";
    public static final String NAME_SRV_ADDR = "127.0.0.1:9876";
    public static final String TOPIC = "TopicTest";

    public static void main(String[] args) throws MQClientException {
        DefaultMQPushConsumer consumer = new DefaultMQPushConsumer(CONSUMER_GROUP); // 创建消费者，ref: sign_cm_110
        consumer.setNamesrvAddr(NAME_SRV_ADDR);

        // 指定在全新的消费者组的情况下从哪里开始。
        consumer.setConsumeFromWhere(ConsumeFromWhere.CONSUME_FROM_FIRST_OFFSET);

        consumer.subscribe(TOPIC, "*");     // 订阅 Topic, ref: sign_m_110
        consumer.registerMessageListener(   // 添加监听器，ref: sign_m_111
            // sign_demo_lm_010  自定义监听处理
            (MessageListenerConcurrently) (msgList, context) -> {   // 调用源 ref: sign_i_m_410
                String msg = msgList.stream()
                        .map(item -> String.format("  msg-item: [%s]. %n", new String(item.getBody())))
                        .collect(Collectors.joining());
                System.out.printf("%n[%s] Receive New Messages: %n%s%n", Thread.currentThread().getName(), msg);
                return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
            }
        );

        consumer.start();   // 启动监听，ref: sign_m_210
        System.out.printf("Consumer Started. %n");
    }
}
```


---
## 初始化
- `org.apache.rocketmq.client.consumer.DefaultMQPushConsumer`
```java
// sign_c_110
public class DefaultMQPushConsumer extends ClientConfig implements MQPushConsumer {

    private String consumerGroup;
    private AllocateMessageQueueStrategy allocateMessageQueueStrategy;
    protected final transient DefaultMQPushConsumerImpl defaultMQPushConsumerImpl;  // ref: sign_c_120

    private ConsumeFromWhere consumeFromWhere = ConsumeFromWhere.CONSUME_FROM_LAST_OFFSET;

    private MessageListener messageListener;


    // sign_cm_110  构造器
    public DefaultMQPushConsumer(final String consumerGroup) {
        this(consumerGroup, null, new AllocateMessageQueueAveragely()); // ref: sign_cm_111
    }

    // sign_cm_111  构造器
    public DefaultMQPushConsumer(
        final String consumerGroup, RPCHook rpcHook, 
        AllocateMessageQueueStrategy allocateMessageQueueStrategy
    ) {
        this.consumerGroup = consumerGroup;
        this.allocateMessageQueueStrategy = allocateMessageQueueStrategy;
        defaultMQPushConsumerImpl = new DefaultMQPushConsumerImpl(this, rpcHook);
    }

    // sign_m_110  订阅 Topic
    @Override
    public void subscribe(String topic, String subExpression) throws MQClientException {
        this.defaultMQPushConsumerImpl.subscribe(withNamespace(topic), subExpression);  // ref: sign_m_120
    }

    // sign_m_111  注册监听器
    @Override
    public void registerMessageListener(MessageListenerConcurrently messageListener) {
        this.messageListener = messageListener;
        this.defaultMQPushConsumerImpl.registerMessageListener(messageListener);        // ref: sign_m_121
    }
}
```

- `org.apache.rocketmq.client.impl.consumer.DefaultMQPushConsumerImpl`
```java
// sign_c_120
public class DefaultMQPushConsumerImpl implements MQConsumerInner {

    private final DefaultMQPushConsumer defaultMQPushConsumer;
    private final RPCHook rpcHook;
    private long pullTimeDelayMillsWhenException = 3000;

    // 10s 30s 1m 2m 3m 4m 5m 6m 7m 8m 9m 10m 20m 30m 1h 2h
    private final int[] popDelayLevel = new int[] {10, 30, 60, 120, 180, 240, 300, 360, 420, 480, 540, 600, 1200, 1800, 3600, 7200};
    private final RebalanceImpl rebalanceImpl = new RebalancePushImpl(this);

    private MessageListener messageListenerInner;


    // sign_cm_120  构造器
    public DefaultMQPushConsumerImpl(DefaultMQPushConsumer defaultMQPushConsumer, RPCHook rpcHook) {
        this.defaultMQPushConsumer = defaultMQPushConsumer;
        this.rpcHook = rpcHook;
        this.pullTimeDelayMillsWhenException = defaultMQPushConsumer.getPullTimeDelayMillsWhenException();  // def: 1s
    }

    // sign_m_120  订阅 Topic
    public void subscribe(String topic, String subExpression) throws MQClientException {
        try {
            SubscriptionData subscriptionData = FilterAPI.buildSubscriptionData(topic, subExpression);
            this.rebalanceImpl.getSubscriptionInner().put(topic, subscriptionData);
            ...
        } 
        ... // catch
    }

    // sign_m_121  注册监听器
    public void registerMessageListener(MessageListener messageListener) {
        this.messageListenerInner = messageListener;
    }
}
```


---
## 启动
- `org.apache.rocketmq.client.consumer.DefaultMQPushConsumer`
```java
// sign_c_210
public class DefaultMQPushConsumer extends ClientConfig implements MQPushConsumer {

    // sign_m_210  启动消费监听
    @Override
    public void start() throws MQClientException {
        setConsumerGroup(NamespaceUtil.wrapNamespace(this.getNamespace(), this.consumerGroup));
        this.defaultMQPushConsumerImpl.start(); // ref: sign_m_220
        ...
    }
}
```

- `org.apache.rocketmq.client.impl.consumer.DefaultMQPushConsumerImpl`
  - 客户端实例初始化参考：[Admin-命令工具#初始化客户端 sign_cm_330](./Admin-命令工具.md#初始化客户端)
  - 客户端实例启动参考：[Admin-命令工具#初始化客户端 sign_m_330](./Admin-命令工具.md#初始化客户端)
```java
// sign_c_220
public class DefaultMQPushConsumerImpl implements MQConsumerInner {
    
    // sign_m_220  启动
    public synchronized void start() throws MQClientException {
        switch (this.serviceState) {
            case CREATE_JUST:
                ... // 校验及其他配置

                // 客户端实例初始化参考：[Admin-命令工具#初始化客户端 sign_cm_330]
                this.mQClientFactory = ... .getOrCreateMQClientInstance(this.defaultMQPushConsumer, this.rpcHook);

                ... // 设置 rebalanceImpl 其他属性
                this.rebalanceImpl.setmQClientFactory(this.mQClientFactory);    // 设置连接客户端

                ... // 初始化 pullAPIWrapper

                if (this.defaultMQPushConsumer.getOffsetStore() != null) { 
                    ...
                } else { // 进入此逻辑
                    switch (this.defaultMQPushConsumer.getMessageModel()) {
                        ...
                        case CLUSTERING:
                            this.offsetStore = new RemoteBrokerOffsetStore(this.mQClientFactory, ...);
                            break;
                    }
                    this.defaultMQPushConsumer.setOffsetStore(this.offsetStore);
                }
                this.offsetStore.load();

                ... // MessageListenerOrderly 处理
                else if (this.getMessageListenerInner() instanceof MessageListenerConcurrently) {
                    this.consumeOrderly = false;
                    this.consumeMessageService = new ConsumeMessageConcurrentlyService(this, this.getMessageListenerInner());
                    this.consumeMessagePopService = new ConsumeMessagePopConcurrentlyService(this, this.getMessageListenerInner());
                }

                this.consumeMessageService.start();         // 启动内部定时任务，ref: sign_m_230
                this.consumeMessagePopService.start();

                boolean registerOK = mQClientFactory.registerConsumer(... .getConsumerGroup(), this);   // 客户端注册
                ... // 注册校验

                mQClientFactory.start();                    // 客户端实例启动参考：[Admin-命令工具#初始化客户端 sign_m_330]
                this.serviceState = ServiceState.RUNNING;   // 设置状态
                break;
            ... // 其他状态直接异常
        }

        this.updateTopicSubscribeInfoWhenSubscriptionChanged(); // 更新 Topic 路由信息
        ...
    }
}
```

- `org.apache.rocketmq.client.impl.consumer.ConsumeMessageConcurrentlyService`
```java
// sign_c_230
public class ConsumeMessageConcurrentlyService implements ConsumeMessageService {

    // sign_m_230  启动定时任务
    public void start() {
        this.cleanExpireMsgExecutors.scheduleAtFixedRate(new Runnable() {
            @Override
            public void run() {
                try {
                    cleanExpireMsg();   // 清理过期消息
                } 
                ... // catch
            }
        }, ..., this.defaultMQPushConsumer.getConsumeTimeout(), TimeUnit.MINUTES);
    }
}
```


---
## 消息处理栈
- 栈
```js
// Netty 接受响应
// new RuntimeException("栈跟踪3").printStackTrace();
java.lang.RuntimeException: 栈跟踪3
    at org.apache.rocketmq.remoting.netty.NettyRemotingAbstract.executeInvokeCallback(NettyRemotingAbstract.java:400)
    at org.apache.rocketmq.remoting.netty.NettyRemotingAbstract.processResponseCommand(NettyRemotingAbstract.java:382)
    at org.apache.rocketmq.remoting.netty.NettyRemotingAbstract.processMessageReceived(NettyRemotingAbstract.java:181)
    at org.apache.rocketmq.remoting.netty.NettyRemotingClient$NettyClientHandler.channelRead0(NettyRemotingClient.java:1091)
    at org.apache.rocketmq.remoting.netty.NettyRemotingClient$NettyClientHandler.channelRead0(NettyRemotingClient.java:1087)

// 处理响应结果
// new RuntimeException("栈跟踪2").printStackTrace();
java.lang.RuntimeException: 栈跟踪2
    at org.apache.rocketmq.client.impl.consumer.ConsumeMessageConcurrentlyService.submitConsumeRequest(ConsumeMessageConcurrentlyService.java:196)
    at org.apache.rocketmq.client.impl.consumer.DefaultMQPushConsumerImpl$1.onSuccess(DefaultMQPushConsumerImpl.java:370)
    at org.apache.rocketmq.client.impl.MQClientAPIImpl$5.operationSucceed(MQClientAPIImpl.java:1027)
    at org.apache.rocketmq.remoting.netty.NettyRemotingClient$InvokeCallbackWrapper.operationSucceed(NettyRemotingClient.java:1078)
    at org.apache.rocketmq.remoting.netty.NettyRemotingAbstract.lambda$invokeAsyncImpl$6(NettyRemotingAbstract.java:596)
    ...
    at org.apache.rocketmq.remoting.netty.NettyRemotingAbstract$1.operationSucceed(NettyRemotingAbstract.java:540)
    at org.apache.rocketmq.remoting.netty.ResponseFuture.executeInvokeCallback(ResponseFuture.java:67)
    at org.apache.rocketmq.remoting.netty.NettyRemotingAbstract.lambda$executeInvokeCallback$2(NettyRemotingAbstract.java:402)

// 处理消息
// new RuntimeException("栈跟踪1").printStackTrace();
java.lang.RuntimeException: 栈跟踪1
    at org.apache.rocketmq.example.quickstart.Consumer2.lambda$main$1(Consumer2.java:44)
    at org.apache.rocketmq.client.impl.consumer.ConsumeMessageConcurrentlyService$ConsumeRequest.run(ConsumeMessageConcurrentlyService.java:411)
    ...


// ---------------------------

// 拉消息
// new RuntimeException("栈跟踪L").printStackTrace();
java.lang.RuntimeException: 栈跟踪L
    at org.apache.rocketmq.remoting.netty.NettyRemotingAbstract.invokeAsyncImpl(NettyRemotingAbstract.java:586) // 成功时回调
    at org.apache.rocketmq.remoting.netty.NettyRemotingClient.invokeAsync(NettyRemotingClient.java:754)
    at org.apache.rocketmq.client.impl.MQClientAPIImpl.pullMessageAsync(MQClientAPIImpl.java:1017)  // 设置回调
    at org.apache.rocketmq.client.impl.MQClientAPIImpl.pullMessage(MQClientAPIImpl.java:831)        // code: 11
    at org.apache.rocketmq.client.impl.consumer.PullAPIWrapper.pullKernelImpl(PullAPIWrapper.java:241)
    at org.apache.rocketmq.client.impl.consumer.DefaultMQPushConsumerImpl.pullMessage(DefaultMQPushConsumerImpl.java:480)
    at org.apache.rocketmq.client.impl.consumer.PullMessageService.pullMessage(PullMessageService.java:109) // 拉消息，ref: sign_m_311
    at org.apache.rocketmq.client.impl.consumer.PullMessageService.run(PullMessageService.java:135)         // 执行体，ref: sign_m_310
    at java.lang.Thread.run(Thread.java:750)
```


---
## 拉消息
- `org.apache.rocketmq.client.impl.consumer.PullMessageService`
  - 客户端实例初始化参考：[Admin-命令工具#初始化客户端 sign_m_320](./Admin-命令工具.md#初始化客户端)
```java
// sign_c_310 拉消息服务 (本质相当于一个线程)
public class PullMessageService extends ServiceThread {

    // sign_f_310  无界队列 (启动时，由 RebalancePushImpl #doRebalance() 填充)
    private LinkedBlockingQueue<MessageRequest> messageRequestQueue = new LinkedBlockingQueue<>();

    // sign_m_310  线程执行体 (在客户端实例启动时启动，参考：[Admin-命令工具#初始化客户端 sign_m_320])
    @Override
    public void run() {
        while (!this.isStopped()) { // 相当于死循环监听请求队列
            try {
                MessageRequest messageRequest = this.messageRequestQueue.take();    // 从队列里获取等待的请求 (无则等待)
                if (messageRequest.getMessageRequestMode() == MessageRequestMode.POP) {
                    this.popMessage((PopRequest) messageRequest);
                } else {    // 一般进入此逻辑
                    this.pullMessage((PullRequest) messageRequest); // 拉消息，ref: sign_m_311
                }
            } 
            ... // catch
        }
    }

    // sign_m_311  拉消息
    private void pullMessage(final PullRequest pullRequest) {
        final MQConsumerInner consumer = this.mQClientFactory.selectConsumer(pullRequest.getConsumerGroup());
        if (consumer != null) {
            DefaultMQPushConsumerImpl impl = (DefaultMQPushConsumerImpl) consumer;
            impl.pullMessage(pullRequest);  // 拉取消息，ref: sign_m_320
        } ... // else
    }
}
```

- `org.apache.rocketmq.client.impl.consumer.DefaultMQPushConsumerImpl`
```java
// sign_c_320
public class DefaultMQPushConsumerImpl implements MQConsumerInner {
    
    private ConsumeMessageService consumeMessageService;    // 一般为 ConsumeMessageConcurrentlyService 实例

    // sign_m_320  拉取消息
    public void pullMessage(final PullRequest pullRequest) {
        final ProcessQueue processQueue = pullRequest.getProcessQueue();
        ... // 校验

        final MessageQueue messageQueue = pullRequest.getMessageQueue();
        final SubscriptionData subscriptionData = this.rebalanceImpl.getSubscriptionInner().get(messageQueue.getTopic());
        ... // 校验

        PullCallback pullCallback = new PullCallback() {    // 设置拉取后的回调
            // sign_in_m_320  成功时的回调方法
            @Override
            public void onSuccess(PullResult pullResult) {
                if (pullResult != null) {
                    ...

                    switch (pullResult.getPullStatus()) {
                        case FOUND:
                            pullRequest.setNextOffset(pullResult.getNextBeginOffset());
                            ...

                            if (pullResult.getMsgFoundList() == null || pullResult.getMsgFoundList().isEmpty()) {
                                DefaultMQPushConsumerImpl.this.executePullRequestImmediately(pullRequest);  // 将请求追加到队列里面去，ref: sign_f_310
                            } else {
                                ...

                                boolean dispatchToConsume = processQueue.putMessage(pullResult.getMsgFoundList());
                                DefaultMQPushConsumerImpl.this.consumeMessageService.submitConsumeRequest(  // 提交消费请求，ref: sign_m_410
                                    pullResult.getMsgFoundList(),  processQueue,
                                    pullRequest.getMessageQueue(), dispatchToConsume
                                );

                                ... // 继续将请求追加到队列里面去，ref: sign_f_310
                            }

                            ...
                            break;
                        case NO_NEW_MSG:
                        case NO_MATCHED_MSG:
                            ...

                            DefaultMQPushConsumerImpl.this.executePullRequestImmediately(pullRequest);      // 将请求追加到队列里面去，ref: sign_f_310
                            break;
                        ... // OFFSET_ILLEGAL:
                    }
                }
            }

            ... // onException(Throwable e)
        };
        ...

        try {
            this.pullAPIWrapper.pullKernelImpl( // 组装请求头拉取消息，ref: sign_m_330
                pullRequest.getMessageQueue(),
                ...
                CommunicationMode.ASYNC,
                pullCallback
            );
        } ... // catch
    }
}
```

- `org.apache.rocketmq.client.impl.consumer.PullAPIWrapper`
```java
// sign_c_330
public class PullAPIWrapper {

    // sign_m_330  组装请求头拉取消息
    public PullResult pullKernelImpl(
        MessageQueue mq, long offset,
        ...,
        PullCallback pullCallback
    ) throws ... {
        // 获取要请求的 Broker 信息
        FindBrokerResult findBrokerResult = this.mQClientFactory.findBrokerAddressInSubscribe(... BrokerName, ...);
        ...

        if (findBrokerResult != null) {
            ... // check version
            ...

            PullMessageRequestHeader requestHeader = new PullMessageRequestHeader();
            requestHeader.setConsumerGroup(this.consumerGroup);
            requestHeader.setTopic(mq.getTopic());
            requestHeader.setQueueId(mq.getQueueId());
            requestHeader.setQueueOffset(offset);
            ... // requestHeader 其他设置

            String brokerAddr = findBrokerResult.getBrokerAddr();
            ...

            PullResult pullResult = this.mQClientFactory.getMQClientAPIImpl().pullMessage(  // 组装请求体拉取消息，ref: sign_m_340
                brokerAddr, requestHeader,
                ...
                pullCallback
            );

            return pullResult;  // 异步，结果为 null
        }

        ... // throw
    }
}
```

- `org.apache.rocketmq.client.impl.MQClientAPIImpl`
  - Broker 处理器注册参考：[Broker-启动#初始化控制器 sign_m_125](./Broker-启动.md#初始化控制器)
```java
// sign_c_340
public class MQClientAPIImpl implements NameServerUpdateCallback {

    // sign_m_340  组装请求体拉取消息
    public PullResult pullMessage(
        String addr, PullMessageRequestHeader requestHeader, long timeoutMillis, 
        CommunicationMode communicationMode, PullCallback pullCallback
    ) throws ... {
        RemotingCommand request;
        ... else {  // 创建请求
            /*
                Broker 处理器注册参考：[Broker-启动#初始化控制器 sign_m_125]
                PULL_MESSAGE (11) 对应的处理器为: PullMessageProcessor
            */
            request = RemotingCommand.createRequestCommand(RequestCode.PULL_MESSAGE, requestHeader);
        }

        switch (communicationMode) {
            ... // ONEWAY
            ... // SYNC
            case ASYNC:
                this.pullMessageAsync(addr, request, timeoutMillis, pullCallback);  // ref: sign_m_341
                return null;
        }
        return null;
    }

    // sign_m_341  异步拉取消息
    private void pullMessageAsync(
        String addr, RemotingCommand request, long timeoutMillis, PullCallback pullCallback
    ) throws ... {
        // 进行 RPC 通信，并处理回调
        this.remotingClient.invokeAsync(addr, request, timeoutMillis, new InvokeCallback() {

            ... // operationComplete(ResponseFuture responseFuture)
            ... // operationFail(Throwable throwable)

            @Override
            public void operationSucceed(RemotingCommand response) {
                try {
                    PullResult pullResult = MQClientAPIImpl.this.processPullResponse(response, addr);
                    pullCallback.onSuccess(pullResult); // 进行成功时的回调处理，ref: sign_in_m_320
                } ... // catch
            }
        });
    }
}
```


---
## 消费消息
- `org.apache.rocketmq.client.impl.consumer.ConsumeMessageConcurrentlyService`
```java
// sign_c_410
public class ConsumeMessageConcurrentlyService implements ConsumeMessageService {

    // sign_m_410  提交消费请求
    @Override
    public void submitConsumeRequest(
        final List<MessageExt> msgs,
        final ProcessQueue processQueue,
        final MessageQueue messageQueue, ...
    ) {
        int consumeBatchSize = this.defaultMQPushConsumer.getConsumeMessageBatchMaxSize();          // def: 1
        if (msgs.size() <= consumeBatchSize) {  // 单批处理
            ConsumeRequest consumeRequest = new ConsumeRequest(msgs, processQueue, messageQueue);   // ref: sign_i_c_410
            try {
                this.consumeExecutor.submit(consumeRequest);    // 提交到线程池，异步处理。执行体 ref: sign_i_m_410
            } catch (RejectedExecutionException e) {
                this.submitConsumeRequestLater(consumeRequest); // 线程池拒绝时，进行延迟再提交
            }
        } 
        ... // else  多条消息时，分批处理，思路与上面一样
    }

    // 延迟 5 秒，再提交
    private void submitConsumeRequestLater(final ConsumeRequest consumeRequest) {
        this.scheduledExecutorService.schedule(new Runnable() {
            @Override
            public void run() {
                ConsumeMessageConcurrentlyService.this.consumeExecutor.submit(consumeRequest);
            }
        }, 5000, TimeUnit.MILLISECONDS);
    }

    
    // sign_i_c_410  消费请求
    class ConsumeRequest implements Runnable {

        // sign_i_m_410  执行体
        @Override
        public void run() {
            ... // 校验

            MessageListenerConcurrently listener = ConsumeMessageConcurrentlyService.this.messageListener;
            ConsumeConcurrentlyContext context = new ConsumeConcurrentlyContext(messageQueue);
            ConsumeConcurrentlyStatus status = null;
            ...
            ... // 钩子及其他处理

            try {
                ... // 设置消息的消费开始时间戳
                status = listener.consumeMessage(...(msgs), context);   // 调用自定义监听器进行处理。ref: sign_demo_lm_010
            } 
            ... // catch

            ... // 钩子及后续处理
        }
    }
}
```


---
## 总结
- 主动拉数据，发送请求是：`RequestCode.PULL_MESSAGE (11)` (参考: sign_m_340)
  - Broker 对应的处理器为: `PullMessageProcessor`
  - 参考：[Broker-发送-消费者-Pull-消息#处理 sign_m_110](./Broker-发送-消费者-Pull-消息.md#处理)