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

- `org.apache.rocketmq.store.DefaultMessageStore`
```java
public class DefaultMessageStore implements MessageStore {
    @Override
    public CompletableFuture<GetMessageResult> getMessageAsync(
        String group, String topic, int queueId, long offset, ...
    ) {
        return CompletableFuture.completedFuture(
            getMessage(group, topic, queueId, offset, ...)
        );
    }
}
```

- `org.apache.rocketmq.broker.processor.DefaultPullMessageResultHandler`
```java
public class DefaultPullMessageResultHandler implements PullMessageResultHandler {

    @Override
    public RemotingCommand handle(final GetMessageResult getMessageResult,
        final RemotingCommand request,
        final PullMessageRequestHeader requestHeader,
        final Channel channel,
        final SubscriptionData subscriptionData,
        final SubscriptionGroupConfig subscriptionGroupConfig,
        final boolean brokerAllowSuspend,
        final MessageFilter messageFilter,
        RemotingCommand response,
        TopicQueueMappingContext mappingContext,
        long beginTimeMills) {
        PullMessageProcessor processor = brokerController.getPullMessageProcessor();
        final String clientAddress = RemotingHelper.parseChannelRemoteAddr(channel);
        TopicConfig topicConfig = this.brokerController.getTopicConfigManager().selectTopicConfig(requestHeader.getTopic());
        processor.composeResponseHeader(requestHeader, getMessageResult, topicConfig.getTopicSysFlag(),
            subscriptionGroupConfig, response, clientAddress);
        try {
            processor.executeConsumeMessageHookBefore(request, requestHeader, getMessageResult, brokerAllowSuspend, response.getCode());
        } catch (AbortProcessException e) {
            response.setCode(e.getResponseCode());
            response.setRemark(e.getErrorMessage());
            return response;
        }

        //rewrite the response for the static topic
        final PullMessageResponseHeader responseHeader = (PullMessageResponseHeader) response.readCustomHeader();
        RemotingCommand rewriteResult = processor.rewriteResponseForStaticTopic(requestHeader, responseHeader, mappingContext, response.getCode());
        if (rewriteResult != null) {
            response = rewriteResult;
        }

        processor.updateBroadcastPulledOffset(requestHeader.getTopic(), requestHeader.getConsumerGroup(),
            requestHeader.getQueueId(), requestHeader, channel, response, getMessageResult.getNextBeginOffset());
        processor.tryCommitOffset(brokerAllowSuspend, requestHeader, getMessageResult.getNextBeginOffset(),
            clientAddress);

        switch (response.getCode()) {
            case ResponseCode.SUCCESS:
                this.brokerController.getBrokerStatsManager().incGroupGetNums(requestHeader.getConsumerGroup(), requestHeader.getTopic(),
                    getMessageResult.getMessageCount());

                this.brokerController.getBrokerStatsManager().incGroupGetSize(requestHeader.getConsumerGroup(), requestHeader.getTopic(),
                    getMessageResult.getBufferTotalSize());

                this.brokerController.getBrokerStatsManager().incBrokerGetNums(requestHeader.getTopic(), getMessageResult.getMessageCount());

                if (!BrokerMetricsManager.isRetryOrDlqTopic(requestHeader.getTopic())) {
                    Attributes attributes = BrokerMetricsManager.newAttributesBuilder()
                        .put(LABEL_TOPIC, requestHeader.getTopic())
                        .put(LABEL_CONSUMER_GROUP, requestHeader.getConsumerGroup())
                        .put(LABEL_IS_SYSTEM, TopicValidator.isSystemTopic(requestHeader.getTopic()) || MixAll.isSysConsumerGroup(requestHeader.getConsumerGroup()))
                        .build();
                    BrokerMetricsManager.messagesOutTotal.add(getMessageResult.getMessageCount(), attributes);
                    BrokerMetricsManager.throughputOutTotal.add(getMessageResult.getBufferTotalSize(), attributes);
                }

                if (!channelIsWritable(channel, requestHeader)) {
                    getMessageResult.release();
                    //ignore pull request
                    return null;
                }

                if (this.brokerController.getBrokerConfig().isTransferMsgByHeap()) {
                    final byte[] r = this.readGetMessageResult(getMessageResult, requestHeader.getConsumerGroup(), requestHeader.getTopic(), requestHeader.getQueueId());
                    this.brokerController.getBrokerStatsManager().incGroupGetLatency(requestHeader.getConsumerGroup(),
                        requestHeader.getTopic(), requestHeader.getQueueId(),
                        (int) (this.brokerController.getMessageStore().now() - beginTimeMills));
                    response.setBody(r);
                    return response;
                } else {
                    try {
                        FileRegion fileRegion =
                            new ManyMessageTransfer(response.encodeHeader(getMessageResult.getBufferTotalSize()), getMessageResult);
                        RemotingCommand finalResponse = response;
                        channel.writeAndFlush(fileRegion)
                            .addListener((ChannelFutureListener) future -> {
                                getMessageResult.release();
                                Attributes attributes = RemotingMetricsManager.newAttributesBuilder()
                                    .put(LABEL_REQUEST_CODE, RemotingHelper.getRequestCodeDesc(request.getCode()))
                                    .put(LABEL_RESPONSE_CODE, RemotingHelper.getResponseCodeDesc(finalResponse.getCode()))
                                    .put(LABEL_RESULT, RemotingMetricsManager.getWriteAndFlushResult(future))
                                    .build();
                                RemotingMetricsManager.rpcLatency.record(request.getProcessTimer().elapsed(TimeUnit.MILLISECONDS), attributes);
                                if (!future.isSuccess()) {
                                    log.error("Fail to transfer messages from page cache to {}", channel.remoteAddress(), future.cause());
                                }
                            });
                    } catch (Throwable e) {
                        log.error("Error occurred when transferring messages from page cache", e);
                        getMessageResult.release();
                    }
                    return null;
                }
            case ResponseCode.PULL_NOT_FOUND:
                final boolean hasSuspendFlag = PullSysFlag.hasSuspendFlag(requestHeader.getSysFlag());
                final long suspendTimeoutMillisLong = hasSuspendFlag ? requestHeader.getSuspendTimeoutMillis() : 0;

                if (brokerAllowSuspend && hasSuspendFlag) {
                    long pollingTimeMills = suspendTimeoutMillisLong;
                    if (!this.brokerController.getBrokerConfig().isLongPollingEnable()) {
                        pollingTimeMills = this.brokerController.getBrokerConfig().getShortPollingTimeMills();
                    }

                    String topic = requestHeader.getTopic();
                    long offset = requestHeader.getQueueOffset();
                    int queueId = requestHeader.getQueueId();
                    PullRequest pullRequest = new PullRequest(request, channel, pollingTimeMills,
                        this.brokerController.getMessageStore().now(), offset, subscriptionData, messageFilter);
                    this.brokerController.getPullRequestHoldService().suspendPullRequest(topic, queueId, pullRequest);
                    return null;
                }
            case ResponseCode.PULL_RETRY_IMMEDIATELY:
                break;
            case ResponseCode.PULL_OFFSET_MOVED:
                if (this.brokerController.getMessageStoreConfig().getBrokerRole() != BrokerRole.SLAVE
                    || this.brokerController.getMessageStoreConfig().isOffsetCheckInSlave()) {
                    MessageQueue mq = new MessageQueue();
                    mq.setTopic(requestHeader.getTopic());
                    mq.setQueueId(requestHeader.getQueueId());
                    mq.setBrokerName(this.brokerController.getBrokerConfig().getBrokerName());

                    OffsetMovedEvent event = new OffsetMovedEvent();
                    event.setConsumerGroup(requestHeader.getConsumerGroup());
                    event.setMessageQueue(mq);
                    event.setOffsetRequest(requestHeader.getQueueOffset());
                    event.setOffsetNew(getMessageResult.getNextBeginOffset());
                    log.warn(
                        "PULL_OFFSET_MOVED:correction offset. topic={}, groupId={}, requestOffset={}, newOffset={}, suggestBrokerId={}",
                        requestHeader.getTopic(), requestHeader.getConsumerGroup(), event.getOffsetRequest(), event.getOffsetNew(),
                        responseHeader.getSuggestWhichBrokerId());
                } else {
                    responseHeader.setSuggestWhichBrokerId(subscriptionGroupConfig.getBrokerId());
                    response.setCode(ResponseCode.PULL_RETRY_IMMEDIATELY);
                    log.warn("PULL_OFFSET_MOVED:none correction. topic={}, groupId={}, requestOffset={}, suggestBrokerId={}",
                        requestHeader.getTopic(), requestHeader.getConsumerGroup(), requestHeader.getQueueOffset(),
                        responseHeader.getSuggestWhichBrokerId());
                }

                break;
            default:
                log.warn("[BUG] impossible result code of get message: {}", response.getCode());
                assert false;
        }

        return response;
    }

}
```