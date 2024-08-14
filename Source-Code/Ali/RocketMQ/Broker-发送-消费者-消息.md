# RocketMQ-Broker-发送-消费者-消息


---
## 参考
- 客户端收消息参考：[客户端-消费者-收消息#拉消息 sign_c_340](./客户端-消费者-收消息.md#拉消息)
- 处理器注册参考：[Broker-启动#初始化控制器 sign_m_125](./Broker-启动.md#初始化控制器)


## 处理
- `org.apache.rocketmq.broker.processor.PullMessageProcessor`
```java
// sign_c_110  客户端拉消息处理器
public class PullMessageProcessor implements NettyRequestProcessor {

    // sign_m_110  处理请求 (发送消息)
    @Override
    public RemotingCommand processRequest(ChannelHandlerContext ctx, RemotingCommand request) throws ... {
        return this.processRequest(ctx.channel(), request, true, true); // ref: sign_m_110
    }

    // sign_m_110  处理请求
    private RemotingCommand processRequest(
        Channel channel, RemotingCommand request, boolean brokerAllowSuspend, boolean brokerAllowFlowCtrSuspend
    ) throws ... {
        final long beginTimeMills = this.brokerController.getMessageStore().now();
        RemotingCommand response = RemotingCommand.createResponseCommand(PullMessageResponseHeader.class);
        final PullMessageResponseHeader responseHeader = (...) response.readCustomHeader();
        final PullMessageRequestHeader requestHeader = (...) request.decodeCommandCustomHeader(PullMessageRequestHeader.class);

        response.setOpaque(request.getOpaque());
        ... // 是否可拉取校验

        SubscriptionGroupConfig subscriptionGroupConfig = this.brokerController.getSubscriptionGroupManager()
            .findSubscriptionGroupConfig(requestHeader.getConsumerGroup());
        ... // 消费组校验

        TopicConfig topicConfig = this.brokerController.getTopicConfigManager().selectTopicConfig(requestHeader.getTopic());
        ... // Topic 配置校验

        TopicQueueMappingContext mappingContext = this.brokerController.getTopicQueueMappingManager().buildTopicQueueMappingContext(requestHeader, false);

        ... // 重定向判断处理
        ... // 队列 ID 校验

        ConsumerManager consumerManager = brokerController.getConsumerManager();
        ... // 设置消费组

        SubscriptionData subscriptionData = null;
        ConsumerFilterData consumerFilterData = null;
        final boolean hasSubscriptionFlag = PullSysFlag.hasSubscriptionFlag(requestHeader.getSysFlag());    // false
        if (hasSubscriptionFlag) {  ... // 不进入此，略
        } else {
            ConsumerGroupInfo consumerGroupInfo = this.brokerController.getConsumerManager().getConsumerGroupInfo(requestHeader.getConsumerGroup());
            ... // 消费组校验
            ... // 广播消息校验
            ... // 是否禁用读校验

            subscriptionData = consumerGroupInfo.findSubscriptionData(requestHeader.getTopic());
            ... // 订阅信息校验
            ... // 订阅版本校验
        }
        ... // Tag 校验

        MessageFilter messageFilter ... = new ExpressionMessageFilter(...);

        final MessageStore messageStore = brokerController.getMessageStore();
        if (this.brokerController.getMessageStore() instanceof DefaultMessageStore) {
            DefaultMessageStore defaultMessageStore = (DefaultMessageStore)this.brokerController.getMessageStore();
            boolean cgNeedColdDataFlowCtr = brokerController.getColdDataCgCtrService().isCgNeedColdDataFlowCtr(requestHeader.getConsumerGroup());   // false
            if (cgNeedColdDataFlowCtr) {
                ... // 不进入此，(冷数据处理) 略
            }
        }

        final boolean useResetOffsetFeature = brokerController.getBrokerConfig().isUseServerSideResetOffset();              // true
        String topic = requestHeader.getTopic();
        String group = requestHeader.getConsumerGroup();
        int queueId = requestHeader.getQueueId();
        Long resetOffset = brokerController.getConsumerOffsetManager().queryThenEraseResetOffset(topic, group, queueId);    // null

        GetMessageResult getMessageResult = null;
        if (useResetOffsetFeature && null != resetOffset) { ... // 不进入此，略
        } else {    // 进入此逻辑
            long broadcastInitOffset = queryBroadcastPullInitOffset(topic, group, queueId, requestHeader, channel);         // -1
            if (broadcastInitOffset >= 0) { ... // 不进入此，略
            } else {
                SubscriptionData finalSubscriptionData = subscriptionData;
                RemotingCommand finalResponse = response;
                messageStore
                    .getMessageAsync(group, topic, queueId, requestHeader.getQueueOffset(), ...)    // 异步获取消息 TODO
                    .thenApply(result -> {
                        ... // 校验 result
                        brokerController.getColdDataCgCtrService().coldAcc(...);
                        return pullMessageResultHandler.handle(                                     // 处理拉取 TODO
                            result, request, requestHeader, channel, ...
                        );
                    })
                    .thenAccept(result -> NettyRemotingAbstract.writeResponse(channel, request, result));   // (使用 Netty 信道) 响应结果
            }
        }

        ... 
        return null;
    }

}
```