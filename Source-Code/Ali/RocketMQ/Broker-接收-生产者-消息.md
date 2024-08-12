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
                asyncPutMessageFuture = this.brokerController.getMessageStore().asyncPutMessage(msgInner);  // 使用默认消息存储器保存，ref: sign_m_210
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
// sign_c_210  默认消息存储器
public class DefaultMessageStore implements MessageStore {

    // sign_m_210  异步追加消息
    @Override
    public CompletableFuture<PutMessageResult> asyncPutMessage(MessageExtBrokerInner msg) {
        ... // 钩子前处理
        ... // check

        CompletableFuture<PutMessageResult> putResultFuture = this.commitLog.asyncPutMessage(msg);  // 进行日志记录，ref: sign_m_220

        putResultFuture.thenAccept(result -> {
            ... // 记录用时
            ... // 有问题，追加异常计数
        });

        return putResultFuture;
    }

    // sign_m_211  提交日志追加
    @Override
    public void onCommitLogAppend(MessageExtBrokerInner msg, AppendMessageResult result, MappedFile commitLogFile) {
        // empty
    }
}
```

- `org.apache.rocketmq.store.CommitLog`
```java
// sign_c_220  提交日志记录器
public class CommitLog implements Swappable {

    // sign_m_220  记录消息
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
        MappedFile mappedFile = this.mappedFileQueue.getLastMappedFile();   // 日志文件，路径: .../commitlog/00000000000000000000

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

            putMessageLock.lock();  // 加锁
            try {
                long beginLockTimestamp = this.defaultMessageStore.getSystemClock().now();
                this.beginTimeInLock = beginLockTimestamp;
                if (!defaultMessageStore.getMessageStoreConfig().isDuplicationEnable()) {
                    msg.setStoreTimestamp(beginLockTimestamp);
                }
                ... // check

                result = mappedFile.appendMessage(msg, this.appendMessageCallback, putMessageContext);  // 追加消息 (只是到内存)，ref: sign_m_230
                switch (result.getStatus()) {
                    case PUT_OK:
                        onCommitLogAppend(msg, result, mappedFile); // 追加消息，ref: sign_m_221
                        break;
                    ... // END_OF_FILE:
                    ... // 其他异常处理
                }
                ...

            }
            ... // finally

            ... // 消息成功写入后增加队列偏移量
        } 
        ... // catch finally
        ... // log

        if (null != unlockMappedFile && this.defaultMessageStore.getMessageStoreConfig().isWarmMapedFileEnable()) {
            this.defaultMessageStore.unlockMappedFile(unlockMappedFile);
        }

        PutMessageResult putMessageResult = new PutMessageResult(PutMessageStatus.PUT_OK, result);
        ... // 统计

        return handleDiskFlushAndHA(putMessageResult, msg, needAckNums, needHandleHA);  // 刷新到磁盘，ref: sign_m_222
    }

    // sign_m_221  追加消息
    protected void onCommitLogAppend(MessageExtBrokerInner msg, AppendMessageResult result, MappedFile commitLogFile) {
        this.getMessageStore().onCommitLogAppend(msg, result, commitLogFile);       // 提交日志追加 (空实现)，ref: sign_m_211
    }

    // sign_m_222  刷新到磁盘 (并做 HA 处理)
    private CompletableFuture<PutMessageResult> handleDiskFlushAndHA(PutMessageResult putMessageResult, MessageExt messageExt, ...) {
        CompletableFuture<PutMessageStatus> flushResultFuture = handleDiskFlush(    // 刷新到磁盘，ref: sign_m_223
            putMessageResult.getAppendMessageResult(), messageExt
        );
        CompletableFuture<PutMessageStatus> replicaResultFuture;
        if (!needHandleHA) {    // 不需 HA，直接返回 OK
            replicaResultFuture = CompletableFuture.completedFuture(PutMessageStatus.PUT_OK);
        } ...   // else

        return flushResultFuture.thenCombine(replicaResultFuture, (flushStatus, replicaStatus) -> {
            ... // 组合结果状态 (只要一个不是 OK，就返回异常状态)
            return putMessageResult;
        });
    }

    // sign_m_223  刷新到磁盘
    private CompletableFuture<PutMessageStatus> handleDiskFlush(AppendMessageResult result, MessageExt messageExt) {
        return this.flushManager.handleDiskFlush(result, messageExt);   // 磁盘刷新，ref: sign_m_250
    }

}
```

- `org.apache.rocketmq.store.logfile.DefaultMappedFile`
```java
// sign_c_230  默认文件映射
public class DefaultMappedFile extends AbstractMappedFile {

    // sign_m_230  追加单条消息
    @Override
    public AppendMessageResult appendMessage(
        MessageExtBrokerInner msg, AppendMessageCallback cb, PutMessageContext putMessageContext
    ) {
        return appendMessagesInner(msg, cb, putMessageContext);
    }

    // sign_m_231  追加消息
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
            } else if (messageExt instanceof MessageExtBrokerInner) {       // 单消息处理
                result = cb.doAppend(   // 回调处理，ref: sign_m_240
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
    // sign_c_240  消息追加回调 (CommitLog 内部类)
    class DefaultAppendMessageCallback implements AppendMessageCallback {

        // sign_m_240  回调处理
        public AppendMessageResult doAppend(final long fileFromOffset, final ByteBuffer byteBuffer, final int maxBlank,
            final MessageExtBrokerInner msgInner, PutMessageContext putMessageContext) {
            // STORETIMESTAMP + STOREHOSTADDRESS + OFFSET <br>

            ByteBuffer preEncodeBuffer = msgInner.getEncodedBuff();
            ... // 广播消息处理 (微消息队列 LMQ (Light MQ) - MQTT)

            final int msgLen = preEncodeBuffer.getInt(0);
            preEncodeBuffer.position(0);
            preEncodeBuffer.limit(msgLen);
            ...

            Supplier<String> msgIdSupplier = () -> {
                ByteBuffer msgIdBuffer = ByteBuffer.allocate(msgIdLen);
                ...
                return UtilAll.bytes2string(msgIdBuffer.array());
            };

            // 记录消费队列信息
            Long queueOffset = msgInner.getQueueOffset();
            // this msg maybe an inner-batch msg.
            short messageNum = getMessageNum(msgInner);

            ... // 事务消息处理
            ... // 文件空闲空间判断处理 (超过 1G 则做其他处理)
            ... // preEncodeBuffer 的其他特殊填充

            ...
            byteBuffer.put(preEncodeBuffer);    // 追加到目标 buf
            msgInner.setEncodedBuff(null);
            ...

            return new AppendMessageResult(
                AppendMessageStatus.PUT_OK, ..., msgIdSupplier, ..., queueOffset, ..., messageNum
            );
        }
    }
```

- `org.apache.rocketmq.store.CommitLog.DefaultFlushManager`
```java
    // sign_c_250  刷新管理器 (CommitLog 内部类)
    class DefaultFlushManager implements FlushManager {

        // sign_m_250  磁盘刷新
        @Override
        public CompletableFuture<PutMessageStatus> handleDiskFlush(AppendMessageResult result, MessageExt messageExt) {
            if (FlushDiskType.SYNC_FLUSH == ... .defaultMessageStore.getMessageStoreConfig().getFlushDiskType()) {
                ... // 同步刷新
            }
            else {  // 异步刷新
                if (!CommitLog.this.defaultMessageStore.isTransientStorePoolEnable()) { // 非事务存储
                    flushCommitLogService.wakeup(); // 实例类为 CommitLog.FlushRealTimeService, ref: sign_c_260 | sign_m_260
                }  ... // else
                return CompletableFuture.completedFuture(PutMessageStatus.PUT_OK);
            }
        }
    }
```

- `org.apache.rocketmq.store.CommitLog.FlushRealTimeService`
```java
    // sign_c_260  实时刷新磁盘线程
    class FlushRealTimeService extends FlushCommitLogService {  // FlushCommitLogService extends ServiceThread, 相当于线程

        // sign_m_260  (刷新磁盘) 线程执行体
        @Override
        public void run() {
            while (!this.isStopped()) {
                ...

                try {
                    ...

                    CommitLog.this.mappedFileQueue.flush(flushPhysicQueueLeastPages);   // 刷新，ref: sign_m_310
                    ... // 记录 (物理) 时间戳、打印

                } ...   // catch
            }

            ... // 关机时再刷新下处理
        }
    }
```


## 持久化
- `org.apache.rocketmq.store.MappedFileQueue`
```java
// sign_c_310  文件队列
public class MappedFileQueue implements Swappable {

    // sign_m_310  刷新
    public boolean flush(final int flushLeastPages) {
        boolean result = true;
        MappedFile mappedFile = this.findMappedFileByOffset(...);   // 查找目标写入文件，ref: sign_m_311
        if (mappedFile != null) {
            int offset = mappedFile.flush(flushLeastPages);         // 刷新文件，ref: sign_m_320
            ...
        }

        return result;
    }

    // sign_m_311  查找目标写入文件
    public MappedFile findMappedFileByOffset(final long offset, final boolean returnFirstOnNotFound) {
        try {
            MappedFile firstMappedFile = this.getFirstMappedFile();
            MappedFile lastMappedFile = this.getLastMappedFile();
            if (firstMappedFile != null && lastMappedFile != null) {
                if (offset < firstMappedFile.getFileFromOffset() || ...) {
                    ... // log
                } else {
                    int index = (int) ((offset / this.mappedFileSize) - (... /* = 0 */ ));   // = 0
                    MappedFile targetFile = ... this.mappedFiles.get(index);

                    if (targetFile != null && offset >= targetFile.getFileFromOffset()
                        && offset < targetFile.getFileFromOffset() + this.mappedFileSize
                    ) { // 偏移量在文件范围内
                        return targetFile;  // 返回当前文件
                    }
                    ...
                }
                ...
            }
        } ... // catch

        return null;
    }
}
```

- `org.apache.rocketmq.store.logfile.DefaultMappedFile`
```java
// sign_c_320  映射文件
public class DefaultMappedFile extends AbstractMappedFile {
    protected String fileName;  // = "$\store\commitlog\00000000000000000000"
    protected MappedByteBuffer mappedByteBuffer;

    private void init(final String fileName, final int fileSize) throws ... {
        ...
        try {
            this.fileChannel = new RandomAccessFile(this.file, "rw").getChannel();
            this.mappedByteBuffer = this.fileChannel.map(MapMode.READ_WRITE, 0, fileSize);  // 直接做了映射 (fileSize = 1G)
        }
        ...
    }


    // sign_m_320  刷新文件
    @Override
    public int flush(final int flushLeastPages) {
        if (this.isAbleToFlush(flushLeastPages)) {
            if (this.hold()) {
                ...
                try {
                    if (writeBuffer != null || this.fileChannel.position() != 0) {
                    } else {                            // writeBuffer 为 null, 进入此逻辑
                        this.mappedByteBuffer.force();  // 强制刷新到磁盘
                    }
                    this.lastFlushTime = System.currentTimeMillis();    // 记录时间
                }
                ...
            } 
            ... // else
        }
        return this.getFlushedPosition();
    }
}
```