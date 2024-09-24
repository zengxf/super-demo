# RocketMQ-总结

---
## 1. 没有推模式，都是基于 pull
- **只是没消息时，会记录请求，5 秒检测一次，有消息时再处理**
  - 参考：https://cloud.tencent.com/developer/article/1850210

- 关键类 `PullRequestHoldService`
```js
// 处理栈
PullRequestHoldService  #run                        // 运行体 (5 秒一次)
PullRequestHoldService  #checkHoldRequest           // 检验挂起的请求
PullRequestHoldService  #notifyMessageArriving      // 有新消息时通知
PullMessageProcessor    #executeRequestWhenWakeup   // 唤醒，处理请求
PullMessageProcessor    #processRequest             // 处理请求
NettyRemotingAbstract   #writeResponse              // 响应结果
```

- 关键类 `DefaultMessageStore.ReputMessageService`
```js
// 处理栈
DefaultMessageStore.ReputMessageService #run                            // 运行体 (1 毫秒一次)
DefaultMessageStore.ReputMessageService #doReput                        // 重新推
DefaultMessageStore                     #notifyMessageArriveIfNecessary // 判断是否推
NotifyMessageArrivingListener           #arriving                       // 监听器处理
PullRequestHoldService                  #notifyMessageArriving          // 有新消息时通知
```