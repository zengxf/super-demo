# RocketMQ-单机本地部署

## 参考
- https://github.com/apache/rocketmq/blob/develop/README.md


## 下载
- https://dist.apache.org/repos/dist/release/rocketmq/
  - 选择要下载的版本 `$version`
  - 下载 `rocketmq-all-$version-bin-release.zip` 包
- 如：https://dist.apache.org/repos/dist/release/rocketmq/5.2.0/rocketmq-all-5.2.0-bin-release.zip
  - 下载后解压


## 改配置
- 添加环境变量 `ROCKETMQ_HOME`
  - cmd: ` set "ROCKETMQ_HOME=D:\Install\Java\Ali\rocketmq\rocketmq-all-5.2.0-bin-release" `
- 或改 cmd 文件
  - `.\bin\mqnamesrv.cmd` 和 `.\bin\mqbroker.cmd`
  - 将上面的 set 命令复制到第一行


## 启动
- 先双击 `.\bin\mqnamesrv.cmd`；再双击 `.\bin\mqbroker.cmd`
```js
// mqnamesrv.cmd 输出
The Name Server boot success. serializeType=JSON, address 0.0.0.0:9876

// mqbroker.cmd 输出
The broker[KYE-1000875714, 10.32.50.94:10911] boot success. serializeType=JSON
```


## 测试
- 先改 `.\bin\mqadmin.cmd` 文件，追加 set 命令
```js
// 更新或创建主题
mqadmin updateTopic -b 127.0.0.1:10911 -t TopicA

D:\...\rocketmq-all-5.2.0-bin-release\bin>  mqadmin updateTopic -b 127.0.0.1:10911 -t TopicA
create topic to 127.0.0.1:10911 success.
TopicConfig [topicName=TopicA, readQueueNums=8, writeQueueNums=8, perm=RW-, topicFilterType=SINGLE_TAG, topicSysFlag=0, order=false, attributes={}]


// 更新或创建订阅组
mqadmin updateSubGroup -b 127.0.0.1:10911 -g SubGroupA

D:\...\rocketmq-all-5.2.0-bin-release\bin>  mqadmin updateSubGroup -b 127.0.0.1:10911 -g SubGroupA
create subscription group to 127.0.0.1:10911 success.
SubscriptionGroupConfig{groupName=SubGroupA, consumeEnable=true, consumeFromMinEnable=false, consumeBroadcastEnable=false, consumeMessageOrderly=false, retryQueueNums=1, retryMaxTimes=16, groupRetryPolicy=GroupRetryPolicy{type=CUSTOMIZED, exponentialRetryPolicy=null, customizedRetryPolicy=null}, brokerId=0, whichBrokerWhenConsumeSlowly=1, notifyConsumerIdsChangedEnable=true, groupSysFlag=0, consumeTimeoutMinute=15, subscriptionDataSet=null, attributes={}}
```