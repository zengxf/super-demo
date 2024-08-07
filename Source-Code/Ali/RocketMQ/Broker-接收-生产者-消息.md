# RocketMQ-Broker-接收-生产者-消息


---
## 参考
- 客户端发消息参考：[客户端-生产者-发消息#Broker-通信 sign_m_321](./客户端-生产者-发消息.md#Broker-通信)
- 处理器注册参考：[Broker-启动#初始化控制器 sign_m_125](./Broker-启动.md#初始化控制器)


## 处理
- `org.apache.rocketmq.broker.processor.SendMessageProcessor`
```java
public class SendMessageProcessor extends AbstractSendMessageProcessor implements NettyRequestProcessor {

    @Override
    public RemotingCommand processRequest(ChannelHandlerContext ctx, RemotingCommand request) throws ... {
        switch (request.getCode()) {
            case RequestCode.CONSUMER_SEND_MSG_BACK:    // 36
                return this.consumerSendMsgBack(ctx, request);
            default:    // code 为 SEND_MESSAGE_V2 (310)，进入此逻辑
                SendMessageRequestHeader requestHeader = parseRequestHeader(request);
                ... // 校验

                SendMessageContext sendMessageContext = buildMsgContext(ctx, requestHeader, request);
                ... // 发送前对消息进行钩子处理

                RemotingCommand response;
                ...

                if (requestHeader.isBatch()) {
                    response = this.sendBatchMessage(ctx, request, ...);
                } else {    // (非批量) 进入此逻辑
                    response = this.sendMessage(
                        ctx, request, ...,
                        (ctx12, response12) -> executeSendMessageHookAfter(response12, ctx12)
                    );
                }

                return response;
        }
    }


    public RemotingCommand sendMessage(
        ChannelHandlerContext ctx, RemotingCommand request, SendMessageContext sendMessageContext, 
        SendMessageRequestHeader requestHeader, TopicQueueMappingContext mappingContext, 
        SendMessageCallback sendMessageCallback
    ) throws RemotingCommandException {
        final RemotingCommand response = preSend(ctx, request, requestHeader);
        ... // check

        final SendMessageResponseHeader responseHeader = (SendMessageResponseHeader) response.readCustomHeader();
        final byte[] body = request.getBody();

        int queueIdInt = requestHeader.getQueueId();
        TopicConfig topicConfig = this.brokerController.getTopicConfigManager().selectTopicConfig(requestHeader.getTopic());
        ... // queueId 小于 0，则随机选择

        MessageExtBrokerInner msgInner = new MessageExtBrokerInner();
        msgInner.setTopic(requestHeader.getTopic());
        msgInner.setQueueId(queueIdInt);

        Map<String, String> oriProps = MessageDecoder.string2messageProperties(requestHeader.getProperties());
        if (!handleRetryAndDLQ(requestHeader, response, request, msgInner, topicConfig, oriProps)) {
            return response;
        }

        msgInner.setBody(body);
        msgInner.setFlag(requestHeader.getFlag());
        ... // check

        MessageAccessor.setProperties(msgInner, oriProps);
        ... // check

        msgInner.setTagsCode(MessageExtBrokerInner.tagsString2tagsCode(topicConfig.getTopicFilterType(), msgInner.getTags()));
        msgInner.setBornTimestamp(requestHeader.getBornTimestamp());
        msgInner.setBornHost(ctx.channel().remoteAddress());
        msgInner.setStoreHost(this.getStoreHost());
        msgInner.setReconsumeTimes(requestHeader.getReconsumeTimes() == null ? 0 : requestHeader.getReconsumeTimes());
        String clusterName = this.brokerController.getBrokerConfig().getBrokerClusterName();
        MessageAccessor.putProperty(msgInner, MessageConst.PROPERTY_CLUSTER, clusterName);

        msgInner.setPropertiesString(MessageDecoder.messageProperties2String(msgInner.getProperties()));

        String traFlag = oriProps.get(MessageConst.PROPERTY_TRANSACTION_PREPARED);
        boolean sendTransactionPrepareMessage ... = false;  // 默认非事务

        long beginTimeMillis = this.brokerController.getMessageStore().now();

        if (brokerController.getBrokerConfig().isAsyncSendEnable()) {
            CompletableFuture<PutMessageResult> asyncPutMessageFuture;
            if (sendTransactionPrepareMessage) {
                asyncPutMessageFuture = this.brokerController.getTransactionalMessageService().asyncPrepareMessage(msgInner);
            } else {    // 非事务存消息
                asyncPutMessageFuture = this.brokerController.getMessageStore().asyncPutMessage(msgInner);
            }

            final int finalQueueIdInt = queueIdInt;
            final MessageExtBrokerInner finalMsgInner = msgInner;
            asyncPutMessageFuture.thenAcceptAsync(putMessageResult -> {
                RemotingCommand responseFuture =
                    handlePutMessageResult(putMessageResult, response, request, finalMsgInner, responseHeader, sendMessageContext,
                        ctx, finalQueueIdInt, beginTimeMillis, mappingContext, BrokerMetricsManager.getMessageType(requestHeader));
                if (responseFuture != null) {
                    doResponse(ctx, request, responseFuture);
                }

                // record the transaction metrics, responseFuture == null means put successfully
                if (sendTransactionPrepareMessage && (responseFuture == null || responseFuture.getCode() == ResponseCode.SUCCESS)) {
                    this.brokerController.getTransactionalMessageService().getTransactionMetrics().addAndGet(msgInner.getProperty(MessageConst.PROPERTY_REAL_TOPIC), 1);
                }

                sendMessageCallback.onComplete(sendMessageContext, response);
            }, this.brokerController.getPutMessageFutureExecutor());
            
            return null;    // 返回 null 以释放发送消息线程
        } 
        
        ... // else 同步处理
    }
}
```