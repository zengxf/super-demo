# RocketMQ-Broker-发送-消费者-Pull-消息


---
## 参考
- 客户端拉消息参考：[客户端-消费者-Pull-收消息#拉取 sign_c_440 | sign_m_440](./客户端-消费者-Pull-收消息.md#拉取)
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

        final MessageStore messageStore = brokerController.getMessageStore();
        ... // 冷数据处理

        final boolean useResetOffsetFeature = brokerController.getBrokerConfig().isUseServerSideResetOffset();              // true
        String topic = requestHeader.getTopic();
        String group = requestHeader.getConsumerGroup();
        int queueId = requestHeader.getQueueId();
        Long resetOffset = brokerController.getConsumerOffsetManager().queryThenEraseResetOffset(topic, group, queueId);    // null

        GetMessageResult getMessageResult = null;
        if (useResetOffsetFeature && null != resetOffset) { ... // 不进入此，略
        } else {        // 进入此逻辑
            long broadcastInitOffset = queryBroadcastPullInitOffset(topic, group, queueId, requestHeader, channel);         // = -1
            if (broadcastInitOffset >= 0) { ... // 不进入此，略
            } else {    // 进入此
                SubscriptionData finalSubscriptionData = subscriptionData;
                RemotingCommand finalResponse = response;
                messageStore
                    .getMessageAsync(group, topic, queueId, requestHeader.getQueueOffset(), ...)    // 异步获取消息，ref: sign_m_120
                    .thenApply(result -> { ... })   // 校验与处理 result
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
// sign_c_120  消息存储
public class DefaultMessageStore implements MessageStore {

    // sign_m_120  异步获取消息
    @Override
    public CompletableFuture<GetMessageResult> getMessageAsync(
        String group, String topic, int queueId, long offset, ...
    ) {
        return CompletableFuture.completedFuture(
            getMessage(group, topic, queueId, offset, ...)  // 提取消息 (关键点)，ref: sign_m_121
        );
    }

    // sign_m_121  获取消息
    @Override
    public GetMessageResult getMessage(final String group, final String topic, ...) {
        ... // check
        ... // 其他处理

        GetMessageStatus status = GetMessageStatus.NO_MESSAGE_IN_QUEUE;
        long nextBeginOffset = offset;
        long minOffset = 0;
        long maxOffset = 0;

        GetMessageResult getResult = new GetMessageResult();
        final long maxOffsetPy = this.commitLog.getMaxOffset();

        ConsumeQueueInterface consumeQueue = findConsumeQueue(topic, queueId);
        if (consumeQueue != null) {
            minOffset = consumeQueue.getMinOffsetInQueue();
            maxOffset = consumeQueue.getMaxOffsetInQueue();

            ... // check
            else {
                final int maxFilterMessageSize = Math.max(this.messageStoreConfig.getMaxFilterMessageSize(), maxMsgNums * consumeQueue.getUnitSize());
                ...

                while (getResult.getBufferTotalSize() <= 0 ...) {
                    ReferredIterator<CqUnit> bufferConsumeQueue = null;

                    try {
                        bufferConsumeQueue = consumeQueue.iterateFrom(nextBeginOffset, maxMsgNums);
                        ... // check

                        long nextPhyFileStartOffset = Long.MIN_VALUE;
                        while (bufferConsumeQueue.hasNext() && nextBeginOffset < maxOffset) {
                            CqUnit cqUnit = bufferConsumeQueue.next();
                            long offsetPy = cqUnit.getPos();
                            int sizePy = cqUnit.getSize();
                            ... // check

                            // 从日志中解析消息，ref: sign_m_210
                            SelectMappedBufferResult selectResult = this.commitLog.getMessage(offsetPy, sizePy);
                            ... // 其他处理

                            this.storeStatsService.getGetMessageTransferredMsgCount().add(cqUnit.getBatchNum());
                            getResult.addMessage(selectResult, cqUnit.getQueueOffset(), cqUnit.getBatchNum());  // 将消息设置进结果
                            status = GetMessageStatus.FOUND;    // 状态为“找到”
                            nextPhyFileStartOffset = Long.MIN_VALUE;
                        }
                    } ... // catch ... finally
                }

                ... // 其他处理
            }
        } ... // else

        if (GetMessageStatus.FOUND == status) {
            this.storeStatsService.getGetMessageTimesTotalFound().add(1);   // 计数
        } 
        ...

        getResult.setStatus(status);
        getResult.setNextBeginOffset(nextBeginOffset);
        getResult.setMaxOffset(maxOffset);
        getResult.setMinOffset(minOffset);
        return getResult;
    }
}
```


---
## 解析消息
- `org.apache.rocketmq.store.CommitLog`
```java
// sign_c_210  日志对象
public class CommitLog implements Swappable {

    // sign_m_210  解析消息
    public SelectMappedBufferResult getMessage(final long offset, final int size) {
        int mappedFileSize = this.defaultMessageStore.getMessageStoreConfig().getMappedFileSizeCommitLog();
        MappedFile mappedFile = this.mappedFileQueue.findMappedFileByOffset(offset, offset == 0);           // 获取映射文件
        if (mappedFile != null) {
            int pos = (int) (offset % mappedFileSize);
            SelectMappedBufferResult selectMappedBufferResult = mappedFile.selectMappedBuffer(pos, size);   // 解析消息，ref: sign_m_220
            if (null != selectMappedBufferResult) {
                selectMappedBufferResult.setInCache(coldDataCheckService.isDataInPageCache(offset));
                return selectMappedBufferResult;
            }
        }
        return null;
    }
}
```

- `org.apache.rocketmq.store.logfile.DefaultMappedFile`
```java
// sign_c_220  
public class DefaultMappedFile extends AbstractMappedFile {

    // sign_m_220  解析消息
    @Override
    public SelectMappedBufferResult selectMappedBuffer(int pos, int size) {
        int readPosition = getReadPosition();
        if ((pos + size) <= readPosition) {
            if (this.hold()) {
                this.mappedByteBufferAccessCountSinceLastSwap++;

                ByteBuffer byteBuffer = this.mappedByteBuffer.slice();
                byteBuffer.position(pos);
                ByteBuffer byteBufferNew = byteBuffer.slice();
                byteBufferNew.limit(size);
                return new SelectMappedBufferResult(this.fileFromOffset + pos, byteBufferNew, size, this);  // 封装字节数据返回
            } ...   // log
        } ...       // log
        return null;
    }
}
```