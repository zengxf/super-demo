# RocketMQ-Broker-处理请求


---
## 测试命令
```js
mqadmin updateTopic -b 127.0.0.1:10911 -t TopicA
```


---
## 请求处理
- 入口流程参考：[命名服务处理请求-请求处理 sign_m_110 sign_m_130 sign_m_131](./命名服务处理请求.md#请求处理)
- 异步请求执行体参考：[命名服务处理请求-请求处理 sign_m_132](./命名服务处理请求.md#请求处理)

- `org.apache.rocketmq.remoting.netty.NettyRemotingAbstract`
```java
// sign_c_130
public abstract class NettyRemotingAbstract {

    // sign_m_131  处理请求命令
    public void processRequestCommand(final ChannelHandlerContext ctx, final RemotingCommand cmd) {
        final Pair<NettyRequestProcessor, ExecutorService> matched = this.processorTable.get(cmd.getCode()); // 配置了 26 个 (17 没配置)

        // code 为 17, pair 对象类型为 < AdminBrokerProcessor : FutureTaskExtThreadPoolExecutor >
        final Pair<NettyRequestProcessor, ExecutorService> pair = null == matched ? this.defaultRequestProcessorPair : matched;
        ...

        ... // pair 空校验处理

        Runnable run = buildProcessRequestHandler(ctx, cmd, pair, ...); // 异步请求执行体参考：[命名服务处理请求-请求处理 sign_m_132]
            // 执行体里的处理请求，ref: sign_m_210

        ... // 停机判断
        ... // 拒绝(限流)判断

        try {
            final RequestTask requestTask = new RequestTask(run, ctx.channel(), cmd);   // 封装成任务
            pair.getObject2().submit(requestTask);  // (提交到线程池) 异步执行
        } ... // catch
    }
}
```

- **code 参考**：`org.apache.rocketmq.remoting.protocol.RequestCode`


---
## 处理器
- `org.apache.rocketmq.broker.processor.AdminBrokerProcessor`
```java
// sign_c_210  默认 Broker 请求处理器
public class AdminBrokerProcessor implements NettyRequestProcessor {

    // sign_m_210  处理请求
    @Override
    public RemotingCommand processRequest(ChannelHandlerContext ctx, RemotingCommand request) ... {
        switch (request.getCode()) {
            case RequestCode.UPDATE_AND_CREATE_TOPIC:
                return this.updateAndCreateTopic(ctx, request); // 创建或更改 Topic
            case RequestCode.DELETE_TOPIC_IN_BROKER:
                return this.deleteTopic(ctx, request);
            case RequestCode.GET_ALL_TOPIC_CONFIG:
                return this.getAllTopicConfig(ctx, request);
            case RequestCode.GET_TIMER_CHECK_POINT:
                return this.getTimerCheckPoint(ctx, request);
            case RequestCode.GET_TIMER_METRICS:
                return this.getTimerMetrics(ctx, request);
            case RequestCode.UPDATE_BROKER_CONFIG:
                return this.updateBrokerConfig(ctx, request);
            case RequestCode.GET_BROKER_CONFIG:
                return this.getBrokerConfig(ctx, request);
            case RequestCode.UPDATE_COLD_DATA_FLOW_CTR_CONFIG:
                return this.updateColdDataFlowCtrGroupConfig(ctx, request);
            case RequestCode.REMOVE_COLD_DATA_FLOW_CTR_CONFIG:
                return this.removeColdDataFlowCtrGroupConfig(ctx, request);
            case RequestCode.GET_COLD_DATA_FLOW_CTR_INFO:
                return this.getColdDataFlowCtrInfo(ctx);
            case RequestCode.SET_COMMITLOG_READ_MODE:
                return this.setCommitLogReadaheadMode(ctx, request);
            case RequestCode.SEARCH_OFFSET_BY_TIMESTAMP:
                return this.searchOffsetByTimestamp(ctx, request);
            case RequestCode.GET_MAX_OFFSET:
                return this.getMaxOffset(ctx, request);
            case RequestCode.GET_MIN_OFFSET:
                return this.getMinOffset(ctx, request);
            case RequestCode.GET_EARLIEST_MSG_STORETIME:
                return this.getEarliestMsgStoretime(ctx, request);
            case RequestCode.GET_BROKER_RUNTIME_INFO:
                return this.getBrokerRuntimeInfo(ctx, request);
            case RequestCode.LOCK_BATCH_MQ:
                return this.lockBatchMQ(ctx, request);
            case RequestCode.UNLOCK_BATCH_MQ:
                return this.unlockBatchMQ(ctx, request);
            case RequestCode.UPDATE_AND_CREATE_SUBSCRIPTIONGROUP:
                return this.updateAndCreateSubscriptionGroup(ctx, request);
            case RequestCode.GET_ALL_SUBSCRIPTIONGROUP_CONFIG:
                return this.getAllSubscriptionGroup(ctx, request);
            case RequestCode.DELETE_SUBSCRIPTIONGROUP:
                return this.deleteSubscriptionGroup(ctx, request);
            case RequestCode.GET_TOPIC_STATS_INFO:
                return this.getTopicStatsInfo(ctx, request);
            case RequestCode.GET_CONSUMER_CONNECTION_LIST:
                return this.getConsumerConnectionList(ctx, request);
            case RequestCode.GET_PRODUCER_CONNECTION_LIST:
                return this.getProducerConnectionList(ctx, request);
            case RequestCode.GET_ALL_PRODUCER_INFO:
                return this.getAllProducerInfo(ctx, request);
            case RequestCode.GET_CONSUME_STATS:
                return this.getConsumeStats(ctx, request);
            case RequestCode.GET_ALL_CONSUMER_OFFSET:
                return this.getAllConsumerOffset(ctx, request);
            case RequestCode.GET_ALL_DELAY_OFFSET:
                return this.getAllDelayOffset(ctx, request);
            case RequestCode.GET_ALL_MESSAGE_REQUEST_MODE:
                return this.getAllMessageRequestMode(ctx, request);
            case RequestCode.INVOKE_BROKER_TO_RESET_OFFSET:
                return this.resetOffset(ctx, request);
            case RequestCode.INVOKE_BROKER_TO_GET_CONSUMER_STATUS:
                return this.getConsumerStatus(ctx, request);
            case RequestCode.QUERY_TOPIC_CONSUME_BY_WHO:
                return this.queryTopicConsumeByWho(ctx, request);
            case RequestCode.QUERY_TOPICS_BY_CONSUMER:
                return this.queryTopicsByConsumer(ctx, request);
            case RequestCode.QUERY_SUBSCRIPTION_BY_CONSUMER:
                return this.querySubscriptionByConsumer(ctx, request);
            case RequestCode.QUERY_CONSUME_TIME_SPAN:
                return this.queryConsumeTimeSpan(ctx, request);
            case RequestCode.GET_SYSTEM_TOPIC_LIST_FROM_BROKER:
                return this.getSystemTopicListFromBroker(ctx, request);
            case RequestCode.CLEAN_EXPIRED_CONSUMEQUEUE:
                return this.cleanExpiredConsumeQueue();
            case RequestCode.DELETE_EXPIRED_COMMITLOG:
                return this.deleteExpiredCommitLog();
            case RequestCode.CLEAN_UNUSED_TOPIC:
                return this.cleanUnusedTopic();
            case RequestCode.GET_CONSUMER_RUNNING_INFO:
                return this.getConsumerRunningInfo(ctx, request);
            case RequestCode.QUERY_CORRECTION_OFFSET:
                return this.queryCorrectionOffset(ctx, request);
            case RequestCode.CONSUME_MESSAGE_DIRECTLY:
                return this.consumeMessageDirectly(ctx, request);
            case RequestCode.CLONE_GROUP_OFFSET:
                return this.cloneGroupOffset(ctx, request);
            case RequestCode.VIEW_BROKER_STATS_DATA:
                return ViewBrokerStatsData(ctx, request);
            case RequestCode.GET_BROKER_CONSUME_STATS:
                return fetchAllConsumeStatsInBroker(ctx, request);
            case RequestCode.QUERY_CONSUME_QUEUE:
                return queryConsumeQueue(ctx, request);
            case RequestCode.UPDATE_AND_GET_GROUP_FORBIDDEN:
                return this.updateAndGetGroupForbidden(ctx, request);
            case RequestCode.GET_SUBSCRIPTIONGROUP_CONFIG:
                return this.getSubscriptionGroup(ctx, request);
            case RequestCode.UPDATE_AND_CREATE_ACL_CONFIG:
                return updateAndCreateAccessConfig(ctx, request);
            case RequestCode.DELETE_ACL_CONFIG:
                return deleteAccessConfig(ctx, request);
            case RequestCode.GET_BROKER_CLUSTER_ACL_INFO:
                return getBrokerAclConfigVersion(ctx, request);
            case RequestCode.UPDATE_GLOBAL_WHITE_ADDRS_CONFIG:
                return updateGlobalWhiteAddrsConfig(ctx, request);
            case RequestCode.RESUME_CHECK_HALF_MESSAGE:
                return resumeCheckHalfMessage(ctx, request);
            case RequestCode.GET_TOPIC_CONFIG:
                return getTopicConfig(ctx, request);
            case RequestCode.UPDATE_AND_CREATE_STATIC_TOPIC:
                return this.updateAndCreateStaticTopic(ctx, request);
            case RequestCode.NOTIFY_MIN_BROKER_ID_CHANGE:
                return this.notifyMinBrokerIdChange(ctx, request);
            case RequestCode.EXCHANGE_BROKER_HA_INFO:
                return this.updateBrokerHaInfo(ctx, request);
            case RequestCode.GET_BROKER_HA_STATUS:
                return this.getBrokerHaStatus(ctx, request);
            case RequestCode.RESET_MASTER_FLUSH_OFFSET:
                return this.resetMasterFlushOffset(ctx, request);
            case RequestCode.GET_BROKER_EPOCH_CACHE:
                return this.getBrokerEpochCache(ctx, request);
            case RequestCode.NOTIFY_BROKER_ROLE_CHANGED:
                return this.notifyBrokerRoleChanged(ctx, request);
            default:
                return getUnknownCmdResponse(ctx, request);
        }
    }
}
```