# Seata-TM-通信客户端


---
## 初始化
- `io.seata.core.rpc.netty.TmNettyRemotingClient`
```java
// sign_c_110  TM 通信客户端
public final class TmNettyRemotingClient extends AbstractNettyRemotingClient {

    // sign_cm_110  构造器
    private TmNettyRemotingClient(
        NettyClientConfig nettyClientConfig, EventExecutorGroup eventExecutorGroup, // null
        ThreadPoolExecutor messageExecutor
    ) {
        super( // ref: sign_cm_120
            nettyClientConfig, eventExecutorGroup, messageExecutor, 
            NettyPoolKey.TransactionRole.TMROLE // 角色为 TM
        );
    }

    // sign_sm_110  获取实例
    public static TmNettyRemotingClient getInstance() {
        if (instance == null) {
            synchronized (TmNettyRemotingClient.class) {
                if (instance == null) {
                    NettyClientConfig nettyClientConfig = new NettyClientConfig();
                    ThreadPoolExecutor messageExecutor = new ThreadPoolExecutor(...); // 构建线程池
                    instance = new TmNettyRemotingClient(nettyClientConfig, null, messageExecutor); // ref: sign_cm_110
                }
            }
        }
        return instance;
    }
}
```

- `io.seata.core.rpc.netty.AbstractNettyRemotingClient`
```java
// sign_c_120
public abstract class AbstractNettyRemotingClient extends AbstractNettyRemoting implements RemotingClient {

    // sign_cm_120
    public AbstractNettyRemotingClient(
        ..., NettyPoolKey.TransactionRole transactionRole
    ) {
        super(messageExecutor);
        this.transactionRole = transactionRole;
        clientBootstrap = new NettyClientBootstrap(..., transactionRole);
        clientBootstrap.setChannelHandlers(new ClientHandler()); // 额外设置信道处理器
        clientChannelManager = new NettyClientChannelManager(
            new NettyPoolableFactory(this, clientBootstrap), // 信道池化的对象工厂
            getPoolKeyFunction(), nettyClientConfig
        );
    }
}
```

- `io.seata.core.rpc.netty.NettyPoolableFactory`
```java
public class NettyPoolableFactory implements KeyedPoolableObjectFactory<NettyPoolKey, Channel> {
    private  AbstractNettyRemotingClient rpcRemotingClient;
    private  NettyClientBootstrap clientBootstrap;

    public NettyPoolableFactory(AbstractNettyRemotingClient rpcRemotingClient, NettyClientBootstrap clientBootstrap) {
        this.rpcRemotingClient = rpcRemotingClient;
        this.clientBootstrap = clientBootstrap;
    }
}
```

- `io.seata.core.rpc.netty.NettyClientChannelManager`
```java
class NettyClientChannelManager {
    private  GenericKeyedObjectPool<NettyPoolKey, Channel> nettyClientKeyPool;
    
    NettyClientChannelManager(NettyPoolableFactory keyPoolableFactory, ... clientConfig) {
        nettyClientKeyPool = new GenericKeyedObjectPool<>(keyPoolableFactory);
        nettyClientKeyPool.setConfig(getNettyPoolConfig(clientConfig));
        this.poolKeyFunction = poolKeyFunction;
    }
}
```