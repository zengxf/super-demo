# RocketMQ-Broker-接收-生产者-消息


---
## 参考
- 客户端发消息参考：[客户端-生产者-发消息#Broker-通信 sign_m_321](./客户端-生产者-发消息.md#Broker-通信)
- 处理器注册参考：[Broker-启动#初始化控制器 sign_m_125](./Broker-启动.md#初始化控制器)


## 处理
- `org.apache.rocketmq.broker.processor.SendMessageProcessor`
```java
// sign_c_110  客户端发消息处理器
public class SendMessageProcessor extends AbstractSendMessageProcessor implements NettyRequestProcessor {

    // sign_m_110  处理请求 (保存消息)
    @Override
    public RemotingCommand processRequest(ChannelHandlerContext ctx, RemotingCommand request) throws ... {
        switch (request.getCode()) {
            case RequestCode.CONSUMER_SEND_MSG_BACK:    // 36
                return this.consumerSendMsgBack(ctx, request);
            default:    // code 为 SEND_MESSAGE_V2 (310)，进入此逻辑
                SendMessageRequestHeader requestHeader = parseRequestHeader(request);   // 解析请求头
                ... // 校验

                SendMessageContext sendMessageContext = buildMsgContext(ctx, requestHeader, request);   // 构建消息上下文
                ... // 发送前对消息进行钩子处理

                RemotingCommand response;
                ...

                if (requestHeader.isBatch()) {
                    response = this.sendBatchMessage(ctx, request, ...);    // 处理批量消息 (略)
                } else {    // (非批量) 进入此逻辑
                    response = this.sendMessage(    // 单条消息处理，ref: sign_m_111
                        ctx, request, ...,
                        (ctx12, response12) -> executeSendMessageHookAfter(response12, ctx12)   // 设置结果钩子处理
                    );
                }

                return response;
        }
    }

    // sign_m_111  处理发送来的消息
    public RemotingCommand sendMessage(
        ChannelHandlerContext ctx, RemotingCommand request, ..., 
        SendMessageCallback sendMessageCallback
    ) throws ... {
        final RemotingCommand response = preSend(ctx, request, requestHeader);  // 初始化响应对象
        ... // check

        final SendMessageResponseHeader responseHeader = (SendMessageResponseHeader) response.readCustomHeader();
        final byte[] body = request.getBody();

        int queueIdInt = requestHeader.getQueueId();
        TopicConfig topicConfig = this.brokerController.getTopicConfigManager().selectTopicConfig(requestHeader.getTopic());
        ... // queueId 小于 0，则随机选择

        MessageExtBrokerInner msgInner = new MessageExtBrokerInner();
        msgInner.setTopic(requestHeader.getTopic());
        msgInner.setBody(body);
        ... // check
        msgInner.setStoreHost(this.getStoreHost());
        ... // 填充 msg

        boolean sendTransactionPrepareMessage ... = false;  // 默认非事务

        if (brokerController.getBrokerConfig().isAsyncSendEnable()) {
            CompletableFuture<PutMessageResult> asyncPutMessageFuture;
            if (sendTransactionPrepareMessage) {    // 事务方式存
                asyncPutMessageFuture = this.brokerController.getTransactionalMessageService().asyncPrepareMessage(msgInner);
            } else {    // 进入此逻辑 (非事务存消息)
                asyncPutMessageFuture = this.brokerController.getMessageStore().asyncPutMessage(msgInner);
            }

            final int finalQueueIdInt = queueIdInt;
            final MessageExtBrokerInner finalMsgInner = msgInner;
            asyncPutMessageFuture.thenAcceptAsync(putMessageResult -> {
                ... // 按需处理响应结果
                ... // 记录事务指标
                sendMessageCallback.onComplete(sendMessageContext, response);   // 回调，响应结果钩子处理
            }, this.brokerController.getPutMessageFutureExecutor());
            
            return null;    // 返回 null 以释放发送消息线程
        } 
        ... // else 同步处理
    }
}
```


---
## 存储
- `org.apache.rocketmq.store.DefaultMessageStore`
```java
public class DefaultMessageStore implements MessageStore {

    @Override
    public CompletableFuture<PutMessageResult> asyncPutMessage(MessageExtBrokerInner msg) {
        ... // 钩子前处理
        ... // check

        CompletableFuture<PutMessageResult> putResultFuture = this.commitLog.asyncPutMessage(msg);

        putResultFuture.thenAccept(result -> {
            ... // 记录用时
            ... // 有问题，追加异常计数
        });

        return putResultFuture;
    }
}
```

- `org.apache.rocketmq.store.CommitLog`
```java
public class CommitLog implements Swappable {

    public CompletableFuture<PutMessageResult> asyncPutMessage(final MessageExtBrokerInner msg) {
        ... // 设置存储时间和内容 CRC32
        ... // 设置版本
        ... // 设置 IPv6 标识

        // 返回结果
        AppendMessageResult result = null;

        PutMessageThreadLocal putMessageThreadLocal = this.putMessageThreadLocal.get();
        updateMaxMessageSize(putMessageThreadLocal);
        String topicQueueKey = generateKey(..., msg);   // 格式: Topic-QueueId
        MappedFile unlockMappedFile = null;
        MappedFile mappedFile = this.mappedFileQueue.getLastMappedFile();   // .../commitlog/00000000000000000000

        long currOffset = 0;    // 写的偏移量
        if (mappedFile != null) {
            currOffset = mappedFile.getFileFromOffset()         // 文件名的解析值 (当前为 0)
                            + mappedFile.getWrotePosition();    // 当前写入位置
        }

        int needAckNums = this.defaultMessageStore.getMessageStoreConfig().getInSyncReplicas();
        boolean needHandleHA = needHandleHA(msg);
        ... // HA 校验与计算

        topicQueueLock.lock(topicQueueKey);
        try {
            ... // 处理消费偏移量

            PutMessageResult encodeResult = putMessageThreadLocal.getEncoder().encode(msg);
            ...
            msg.setEncodedBuff(putMessageThreadLocal.getEncoder().getEncoderBuffer());
            PutMessageContext putMessageContext = new PutMessageContext(topicQueueKey);

            putMessageLock.lock(); //spin or ReentrantLock ,depending on store config
            try {
                long beginLockTimestamp = this.defaultMessageStore.getSystemClock().now();
                this.beginTimeInLock = beginLockTimestamp;
                if (!defaultMessageStore.getMessageStoreConfig().isDuplicationEnable()) {
                    msg.setStoreTimestamp(beginLockTimestamp);
                }
                ... // check

                result = mappedFile.appendMessage(msg, this.appendMessageCallback, putMessageContext);
                switch (result.getStatus()) {
                    case PUT_OK:
                        onCommitLogAppend(msg, result, mappedFile);
                        break;
                    ... // END_OF_FILE:
                    ... // 其他异常处理
                }
                ...

            } ... // finally

            // Increase queue offset when messages are successfully written
            if (AppendMessageStatus.PUT_OK.equals(result.getStatus())) {
                this.defaultMessageStore.increaseOffset(msg, getMessageNum(msg));
            }
        } 
        ... // catch finally
        ... // log

        if (null != unlockMappedFile && this.defaultMessageStore.getMessageStoreConfig().isWarmMapedFileEnable()) {
            this.defaultMessageStore.unlockMappedFile(unlockMappedFile);
        }

        PutMessageResult putMessageResult = new PutMessageResult(PutMessageStatus.PUT_OK, result);
        ... // 统计

        return handleDiskFlushAndHA(putMessageResult, msg, needAckNums, needHandleHA);
    }
}
```

- `org.apache.rocketmq.store.logfile.DefaultMappedFile`
```java

public class DefaultMappedFile extends AbstractMappedFile {

    @Override
    public AppendMessageResult appendMessage(
        MessageExtBrokerInner msg, AppendMessageCallback cb, PutMessageContext putMessageContext
    ) {
        return appendMessagesInner(msg, cb, putMessageContext);
    }

    public AppendMessageResult appendMessagesInner(
        MessageExt messageExt,  AppendMessageCallback cb, PutMessageContext putMessageContext
    ) {
        ... // check
        int currentPos = WROTE_POSITION_UPDATER.get(this);

        if (currentPos < this.fileSize) {
            ByteBuffer byteBuffer = appendMessageBuffer().slice();  // 文件的映射 buffer
            byteBuffer.position(currentPos);                        // 设置要追加的位置

            AppendMessageResult result;
            if (messageExt instanceof MessageExtBatch && ...) {
                ... // 批处理
            } else if (messageExt instanceof MessageExtBrokerInner) {   // 单消息处理
                result = cb.doAppend(
                    this.getFileFromOffset(), byteBuffer, this.fileSize - currentPos,
                    (MessageExtBrokerInner) messageExt, putMessageContext
                );
            } ... // else 

            WROTE_POSITION_UPDATER.addAndGet(this, result.getWroteBytes()); // 更新位置记录
            return result;
        }

        ... // 返回错误标识
    }

}
```

- `org.apache.rocketmq.store.CommitLog.DefaultAppendMessageCallback`
```java
    class DefaultAppendMessageCallback implements AppendMessageCallback {

        public AppendMessageResult doAppend(final long fileFromOffset, final ByteBuffer byteBuffer, final int maxBlank,
            final MessageExtBrokerInner msgInner, PutMessageContext putMessageContext) {
            // STORETIMESTAMP + STOREHOSTADDRESS + OFFSET <br>

            ByteBuffer preEncodeBuffer = msgInner.getEncodedBuff();
            boolean isMultiDispatchMsg = messageStoreConfig.isEnableMultiDispatch() && CommitLog.isMultiDispatchMsg(msgInner);
            if (isMultiDispatchMsg) {
                AppendMessageResult appendMessageResult = handlePropertiesForLmqMsg(preEncodeBuffer, msgInner);
                if (appendMessageResult != null) {
                    return appendMessageResult;
                }
            }

            final int msgLen = preEncodeBuffer.getInt(0);
            preEncodeBuffer.position(0);
            preEncodeBuffer.limit(msgLen);

            // PHY OFFSET
            long wroteOffset = fileFromOffset + byteBuffer.position();

            Supplier<String> msgIdSupplier = () -> {
                int sysflag = msgInner.getSysFlag();
                int msgIdLen = (sysflag & MessageSysFlag.STOREHOSTADDRESS_V6_FLAG) == 0 ? 4 + 4 + 8 : 16 + 4 + 8;
                ByteBuffer msgIdBuffer = ByteBuffer.allocate(msgIdLen);
                MessageExt.socketAddress2ByteBuffer(msgInner.getStoreHost(), msgIdBuffer);
                msgIdBuffer.clear();//because socketAddress2ByteBuffer flip the buffer
                msgIdBuffer.putLong(msgIdLen - 8, wroteOffset);
                return UtilAll.bytes2string(msgIdBuffer.array());
            };

            // Record ConsumeQueue information
            Long queueOffset = msgInner.getQueueOffset();

            // this msg maybe an inner-batch msg.
            short messageNum = getMessageNum(msgInner);

            // Transaction messages that require special handling
            final int tranType = MessageSysFlag.getTransactionValue(msgInner.getSysFlag());
            switch (tranType) {
                // Prepared and Rollback message is not consumed, will not enter the consume queue
                case MessageSysFlag.TRANSACTION_PREPARED_TYPE:
                case MessageSysFlag.TRANSACTION_ROLLBACK_TYPE:
                    queueOffset = 0L;
                    break;
                case MessageSysFlag.TRANSACTION_NOT_TYPE:
                case MessageSysFlag.TRANSACTION_COMMIT_TYPE:
                default:
                    break;
            }

            // Determines whether there is sufficient free space
            if ((msgLen + END_FILE_MIN_BLANK_LENGTH) > maxBlank) {
                this.msgStoreItemMemory.clear();
                // 1 TOTALSIZE
                this.msgStoreItemMemory.putInt(maxBlank);
                // 2 MAGICCODE
                this.msgStoreItemMemory.putInt(CommitLog.BLANK_MAGIC_CODE);
                // 3 The remaining space may be any value
                // Here the length of the specially set maxBlank
                final long beginTimeMills = CommitLog.this.defaultMessageStore.now();
                byteBuffer.put(this.msgStoreItemMemory.array(), 0, 8);
                return new AppendMessageResult(AppendMessageStatus.END_OF_FILE, wroteOffset,
                    maxBlank, /* only wrote 8 bytes, but declare wrote maxBlank for compute write position */
                    msgIdSupplier, msgInner.getStoreTimestamp(),
                    queueOffset, CommitLog.this.defaultMessageStore.now() - beginTimeMills);
            }

            int pos = 4 + 4 + 4 + 4 + 4;
            // 6 QUEUEOFFSET
            preEncodeBuffer.putLong(pos, queueOffset);
            pos += 8;
            // 7 PHYSICALOFFSET
            preEncodeBuffer.putLong(pos, fileFromOffset + byteBuffer.position());
            int ipLen = (msgInner.getSysFlag() & MessageSysFlag.BORNHOST_V6_FLAG) == 0 ? 4 + 4 : 16 + 4;
            // 8 SYSFLAG, 9 BORNTIMESTAMP, 10 BORNHOST, 11 STORETIMESTAMP
            pos += 8 + 4 + 8 + ipLen;
            // refresh store time stamp in lock
            preEncodeBuffer.putLong(pos, msgInner.getStoreTimestamp());
            if (enabledAppendPropCRC) {
                // 18 CRC32
                int checkSize = msgLen - crc32ReservedLength;
                ByteBuffer tmpBuffer = preEncodeBuffer.duplicate();
                tmpBuffer.limit(tmpBuffer.position() + checkSize);
                int crc32 = UtilAll.crc32(tmpBuffer);
                tmpBuffer.limit(tmpBuffer.position() + crc32ReservedLength);
                MessageDecoder.createCrc32(tmpBuffer, crc32);
            }

            final long beginTimeMills = CommitLog.this.defaultMessageStore.now();
            CommitLog.this.getMessageStore().getPerfCounter().startTick("WRITE_MEMORY_TIME_MS");
            // Write messages to the queue buffer
            byteBuffer.put(preEncodeBuffer);
            CommitLog.this.getMessageStore().getPerfCounter().endTick("WRITE_MEMORY_TIME_MS");
            msgInner.setEncodedBuff(null);

            if (isMultiDispatchMsg) {
                CommitLog.this.multiDispatch.updateMultiQueueOffset(msgInner);
            }

            return new AppendMessageResult(AppendMessageStatus.PUT_OK, wroteOffset, msgLen, msgIdSupplier,
                msgInner.getStoreTimestamp(), queueOffset, CommitLog.this.defaultMessageStore.now() - beginTimeMills, messageNum);
        }
    }
```