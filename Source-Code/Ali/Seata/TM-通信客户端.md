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

    // sign_sm_111  获取实例
    public static TmNettyRemotingClient getInstance(String applicationId, ...) {
        TmNettyRemotingClient tmRpcClient = getInstance(); // ref: sign_sm_110
        tmRpcClient.setApplicationId(applicationId);
        tmRpcClient.setTransactionServiceGroup(transactionServiceGroup);
        tmRpcClient.setAccessKey(accessKey);
        tmRpcClient.setSecretKey(secretKey);
        return tmRpcClient;
    }

    // sign_m_110  初始化
    @Override
    public void init() {
        registerProcessor(); // registry processor
        if (initialized.compareAndSet(false, true)) {
            super.init();    // ref: sign_m_120
            if (StringUtils.isNotBlank(transactionServiceGroup)) {
                initConnection();
            }
        }
    }

    // sign_m_111  注册处理器
    private void registerProcessor() {
        // 1. 注册 TC 响应处理器
        ClientOnResponseProcessor onResponseProcessor = new ClientOnResponseProcessor(
            mergeMsgMap, super.getFutures(), 
            getTransactionMessageHandler()
        );
        super.registerProcessor(MessageType.TYPE_SEATA_MERGE_RESULT, onResponseProcessor, null);
        ... // 注册其他响应类型

        ... // 2. 注册心跳消息处理器
    }
}
```

- `io.seata.core.rpc.netty.AbstractNettyRemotingClient`
```java
// sign_c_120  抽象通信客户端
public abstract class AbstractNettyRemotingClient extends AbstractNettyRemoting implements RemotingClient {

    // sign_cm_120  构造器
    public AbstractNettyRemotingClient(
        ..., NettyPoolKey.TransactionRole transactionRole
    ) {
        super(messageExecutor);
        this.transactionRole = transactionRole;
        clientBootstrap = new NettyClientBootstrap(..., transactionRole); // 客户端引导器， ref: sign_cm_150
        clientBootstrap.setChannelHandlers(new ClientHandler());    // 设置额外信道处理器，  ref: sign_cb_150
        clientChannelManager = new NettyClientChannelManager(       // 信道管理器，         ref: sign_cm_140
            new NettyPoolableFactory(this, clientBootstrap),        // 信道池化的对象工厂，  ref: sign_c_130 | sign_cm_130
            getPoolKeyFunction(), nettyClientConfig
        );
    }

    // sign_m_120  初始化
    @Override
    public void init() {
        timerExecutor.scheduleAtFixedRate(() -> clientChannelManager.reconnect(getTransactionServiceGroup()), ...);
        ...
        super.init();
        clientBootstrap.start(); // 启动引导，ref: sign_m_150
    }
}
```

- `io.seata.core.rpc.netty.NettyPoolableFactory`
```java
// sign_c_130  对象池工厂
public class NettyPoolableFactory implements KeyedPoolableObjectFactory<NettyPoolKey, Channel> {
    private  AbstractNettyRemotingClient rpcRemotingClient;
    private  NettyClientBootstrap clientBootstrap;

    // sign_cm_130  构造器
    public NettyPoolableFactory(AbstractNettyRemotingClient rpcRemotingClient, NettyClientBootstrap clientBootstrap) {
        this.rpcRemotingClient = rpcRemotingClient;
        this.clientBootstrap = clientBootstrap;
    }
}
```

- `io.seata.core.rpc.netty.NettyClientChannelManager`
```java
// sign_c_140  信道管理器
class NettyClientChannelManager {
    private  GenericKeyedObjectPool<NettyPoolKey, Channel> nettyClientKeyPool; // sign_f_140  对象池
    
    // sign_cm_140  构造器
    NettyClientChannelManager(NettyPoolableFactory keyPoolableFactory, ... clientConfig) {
        nettyClientKeyPool = new GenericKeyedObjectPool<>(keyPoolableFactory); // 关联对象工厂，ref: sign_c_130
        nettyClientKeyPool.setConfig(getNettyPoolConfig(clientConfig));
        this.poolKeyFunction = poolKeyFunction;
    }
}
```

- `io.seata.core.rpc.netty.NettyClientBootstrap`
```java
// sign_c_150  客户端引导器
public class NettyClientBootstrap implements RemotingBootstrap {
    private  Bootstrap bootstrap = new Bootstrap();
    private ChannelHandler[] channelHandlers;

    // sign_cm_150  构造器
    public NettyClientBootstrap(NettyClientConfig nettyClientConfig, ..., NettyPoolKey.TransactionRole transactionRole) {
        ...
        this.nettyClientConfig = nettyClientConfig;
        this.transactionRole = transactionRole;
        this.eventLoopGroupWorker = new NioEventLoopGroup(...);
        ...
    }

    // sign_m_150  启动引导
    @Override
    public void start() {
        ...
        
        this.bootstrap
                .group(this.eventLoopGroupWorker)
                .channel(nettyClientConfig.getClientChannelClazz()) // NioSocketChannel.class | EpollSocketChannel.class
                .option(ChannelOption.TCP_NODELAY, true)
                .option(ChannelOption.SO_KEEPALIVE, true)
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, nettyClientConfig.getConnectTimeoutMillis())
                .option(ChannelOption.SO_SNDBUF, nettyClientConfig.getClientSocketSndBufSize())
                .option(ChannelOption.SO_RCVBUF, nettyClientConfig.getClientSocketRcvBufSize());

        if (nettyClientConfig.enableNative()) {
            ...
            else {
                bootstrap
                    .option(EpollChannelOption.EPOLL_MODE, EpollMode.EDGE_TRIGGERED) // epoll 边沿触发
                    .option(EpollChannelOption.TCP_QUICKACK, true);
            }
        }

        bootstrap.handler(
            new ChannelInitializer<SocketChannel>() {
                @Override
                public void initChannel(SocketChannel ch) {
                    ChannelPipeline pipeline = ch.pipeline();
                    pipeline
                        .addLast(new IdleStateHandler(...))
                        .addLast(new ProtocolV1Decoder())
                        .addLast(new ProtocolV1Encoder());
                    if (channelHandlers != null) {
                        addChannelPipelineLast(ch, channelHandlers); // sign_cb_150  添加额外的处理器
                    }
                }
            });

        ...
    }

}
```

### 调用源
- `io.seata.spring.annotation.GlobalTransactionScanner`
```java
// sign_c_160  全局事务扫描器
public class GlobalTransactionScanner extends AbstractAutoProxyCreator
        implements ConfigurationChangeListener, InitializingBean, ApplicationContextAware, DisposableBean 
{

    // sign_m_160  Bean 初始化后处理方法
    @Override
    public void afterPropertiesSet() {
        ...
        if (initialized.compareAndSet(false, true)) {
            initClient();
        }
    }

    // sign_m_161  初始化客户端
    private void initClient() {
        ...

        // init TM, ref: sign_sm_170
        TMClient.init(applicationId, txServiceGroup, accessKey, secretKey);
        ...

        // init RM
        RMClient.init(applicationId, txServiceGroup);
        
        ...
        registerSpringShutdownHook();
    }
}
```

- `io.seata.tm.TMClient`
```java
// sign_c_170
public class TMClient {
    
    // sign_sm_170  初始化 TM 客户端
    public static void init(String applicationId, String transactionServiceGroup, String accessKey, String secretKey) {
        TmNettyRemotingClient tmNettyRemotingClient = TmNettyRemotingClient.getInstance(...); // ref: sign_sm_111
        tmNettyRemotingClient.init(); // ref: sign_m_110
    }
}
```


---
## 创建信道
- `io.seata.core.rpc.netty.NettyClientChannelManager`
```java
// sign_c_210  信道管理器
class NettyClientChannelManager {

    // sign_m_210  获取信道
    Channel acquireChannel(String serverAddress) {
        ... // 缓存中获取
        ... // log

        Object lockObj = CollectionUtils.computeIfAbsent(channelLocks, serverAddress, key -> new Object());
        synchronized (lockObj) {
            return doConnect(serverAddress);
        }
    }

    // sign_m_211  连接创建信道
    private Channel doConnect(String serverAddress) {
        ... // 缓存中获取。上面的锁相当于 DCL

        Channel channelFromPool;
        try {
            NettyPoolKey currentPoolKey = poolKeyFunction.apply(serverAddress);
            ... // poolKeyMap.put(serverAddress, currentPoolKey);

            // 从对象池获取，ref: sign_f_140
            // 最终会从工厂创建，ref: sign_c_130 | sign_c_220 | sign_m_220
            channelFromPool = nettyClientKeyPool.borrowObject(poolKeyMap.get(serverAddress));
            channels.put(serverAddress, channelFromPool);
        } ... // catch
        return channelFromPool;
    }
}
```

- `io.seata.core.rpc.netty.NettyPoolableFactory`
```java
// sign_c_220  对象池工厂
public class NettyPoolableFactory implements KeyedPoolableObjectFactory<NettyPoolKey, Channel> {

    // sign_m_220  创建对象（信道）
    @Override
    public Channel makeObject(NettyPoolKey key) {
        InetSocketAddress address = NetUtil.toInetSocketAddress(key.getAddress());
        ... // log

        Channel tmpChannel = clientBootstrap.getNewChannel(address);
        Object response;
        Channel channelToServer = null;
        ... // 校验

        try {
            response = rpcRemotingClient.sendSyncRequest(tmpChannel, key.getMessage());
            ... // 注册状态判断处理； channelToServer = tmpChannel;
        }
        ... // catch
        ... // log

        return channelToServer;
    }

}
```

- `io.seata.core.rpc.netty.NettyClientBootstrap`
```java
// sign_c_230  客户端引导器
public class NettyClientBootstrap implements RemotingBootstrap {

    // sign_m_230  获取新信道
    public Channel getNewChannel(InetSocketAddress address) {
        Channel channel;
        ChannelFuture f = this.bootstrap.connect(address); // 连接服务端，其初始化参考: sign_m_150
        try {
            f.await(this.nettyClientConfig.getConnectTimeoutMillis(), TimeUnit.MILLISECONDS);
            ... // 
            else {
                channel = f.channel();
            }
        } ... // catch
        return channel;
    }
}
```


---
## 发送请求
- `io.seata.core.rpc.netty.AbstractNettyRemotingClient`
```java
// sign_c_310
public abstract class AbstractNettyRemotingClient extends AbstractNettyRemoting implements RemotingClient {

    // sign_m_310  同步方式发送请求
    @Override
    public Object sendSyncRequest(Channel channel, Object msg) throws TimeoutException {
        ...
        RpcMessage rpcMessage = buildRequestMessage(msg, ProtocolConstants.MSGTYPE_RESQUEST_SYNC);
        return super.sendSync(channel, rpcMessage, this.getRpcRequestTimeout()); // 发送请求，ref: sign_m_320
    }
}
```

- `io.seata.core.rpc.netty.AbstractNettyRemoting`
```java
// sign_c_320
public abstract class AbstractNettyRemoting implements Disposable {

    // sign_m_320  同步方式发送消息
    protected Object sendSync(Channel channel, RpcMessage rpcMessage, long timeoutMillis) throws TimeoutException {
        ...

        MessageFuture messageFuture = new MessageFuture();
        messageFuture.setRequestMessage(rpcMessage);
        messageFuture.setTimeout(timeoutMillis);
        futures.put(rpcMessage.getId(), messageFuture);

        channelWritableCheck(channel, rpcMessage.getBody()); // 校验是否可发送

        String remoteAddr = ChannelUtil.getAddressFromChannel(channel);
        doBeforeRpcHooks(remoteAddr, rpcMessage);            // 钩子处理

        channel.writeAndFlush(rpcMessage) // 发送消息
            .addListener((ChannelFutureListener) future -> {
                ... // 发送不成功的处理
            });

        try {
            Object result = messageFuture.get(timeoutMillis, TimeUnit.MILLISECONDS); // 获取结果
            doAfterRpcHooks(remoteAddr, rpcMessage, result); // 钩子处理
            return result;
        } ... // catch
    }
}
```