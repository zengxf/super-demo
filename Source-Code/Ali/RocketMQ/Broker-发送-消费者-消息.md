# RocketMQ-Broker-发送-消费者-消息


---
## 参考
- 客户端收消息参考：[客户端-消费者-收消息#拉消息 sign_c_340](./客户端-消费者-收消息.md#拉消息)
- 处理器注册参考：[Broker-启动#初始化控制器 sign_m_125](./Broker-启动.md#初始化控制器)


## 处理
- `org.apache.rocketmq.broker.processor.PullMessageProcessor`
```java
// sign_c_110
public class PullMessageProcessor implements NettyRequestProcessor {

    // sign_m_110
    @Override
    public RemotingCommand processRequest(ChannelHandlerContext ctx, RemotingCommand request) throws ... {
        return this.processRequest(ctx.channel(), request, true, true);
    }
}
```