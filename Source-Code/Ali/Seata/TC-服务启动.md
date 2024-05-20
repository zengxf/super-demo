# Seata-TC-服务启动


---
## 应用启动
- 模块为: `server [seata-server]`
- 启动类: `io.seata.server.ServerApplication`

### 初始-TC-监听端口
- 一般为 Web 端口加 `1000`

- `io.seata.server.spring.listener.ServerApplicationListener`
```java
// sign_c_110  应用监听器
public class ServerApplicationListener implements GenericApplicationListener {

    // sign_m_110  监听环境准备好事件
    @Override
    public void onApplicationEvent(ApplicationEvent event) {
        ...

        ConfigurableEnvironment environment = environmentPreparedEvent.getEnvironment();
        ObjectHolder.INSTANCE.setObject(OBJECT_KEY_SPRING_CONFIGURABLE_ENVIRONMENT, environment);
        ...

        // 获取端口顺序为：-p > -D > env > yml > default
        ... // -p 8091
        ... // -Dserver.servicePort=8091
        ... // docker -e SEATA_PORT=8091
        ... // yml properties server.service-port=8091
        
        // server.port=7091
        String serverPort = environment.getProperty("server.port", String.class);
        ...

        // 端口最终为 7091 + 1000 = 8091
        String servicePort = String.valueOf(Integer.parseInt(serverPort) + SERVICE_OFFSET_SPRING_BOOT);
        setTargetPort(environment, servicePort, true); // 设置到配置中
    }
}
```


---
## 服务启动
- `io.seata.server.ServerRunner`
```java
// sign_c_210  服务运行器
@Component
public class ServerRunner implements CommandLineRunner, ... {

    // sign_m_210  运行
    @Override
    public void run(String... args) {
        try {
            Server.start(args); // 启动服务，ref: sign_m_220
            started = true;
            ... // log
        }
        ... // catch
    }

}
```

- `io.seata.server.Server`
```java
// sign_c_220  服务类
public class Server {
    
    // sign_m_220  启动
    public static void start(String[] args) {
        ... // 其他初始化

        ThreadPoolExecutor workingThreads = new ThreadPoolExecutor(...);
        ... // 填充 XID 的 ip / port

        NettyRemotingServer nettyRemotingServer = new NettyRemotingServer(workingThreads); // 创建 TC 远程服务，ref: sign_cm_230
        ...

        DefaultCoordinator coordinator = DefaultCoordinator.getInstance(nettyRemotingServer);
        ... // RAFT 模式，coordinator 为 ApplicationListener 子类时处理

        // log store mode : file, db, redis
        SessionHolder.init();
        LockerManagerFactory.init();
        coordinator.init();
        nettyRemotingServer.setHandler(coordinator);

        ...

        nettyRemotingServer.init(); // 进行初始化，ref: sign_m_230
    }
}
```

- `io.seata.core.rpc.netty.NettyRemotingServer`
```java
// sign_c_230  TC 远程服务
public class NettyRemotingServer extends AbstractNettyRemotingServer {

    // sign_cm_230  构造器
    public NettyRemotingServer(ThreadPoolExecutor messageExecutor) {
        super(messageExecutor, new NettyServerConfig()); // ref: sign_cm_240
    }

    // sign_m_230  初始化处理
    @Override
    public void init() {
        registerProcessor(); // 注解处理器，ref: sign_m_231
        if (initialized.compareAndSet(false, true)) {
            super.init();    // 初始化，ref: sign_m_240
        }
    }

    // sign_m_231  注解处理器
    private void registerProcessor() {
        // 1. 注册请求消息处理器
        ServerOnRequestProcessor onRequestProcessor = new ServerOnRequestProcessor(this, getHandler());
        super.registerProcessor(MessageType.TYPE_BRANCH_REGISTER, onRequestProcessor, messageExecutor);
        ...

        // 2. 注册响应消息处理器
        ServerOnResponseProcessor onResponseProcessor = new ServerOnResponseProcessor(getHandler(), getFutures());
        super.registerProcessor(MessageType.TYPE_BRANCH_COMMIT_RESULT, onResponseProcessor, branchResultMessageExecutor);
        ...

        // 3. 注册 RM 消息处理器
        RegRmProcessor regRmProcessor = new RegRmProcessor(this);
        super.registerProcessor(MessageType.TYPE_REG_RM, regRmProcessor, messageExecutor);

        // 4. 注册 TM 消息处理器
        RegTmProcessor regTmProcessor = new RegTmProcessor(this);
        super.registerProcessor(MessageType.TYPE_REG_CLT, regTmProcessor, null);

        ... // 5. 注册心跳消息处理器
    }
}
```

- `io.seata.core.rpc.netty.AbstractNettyRemotingServer`
```java
// sign_c_240  抽象远程服务
public abstract class AbstractNettyRemotingServer extends AbstractNettyRemoting implements RemotingServer {
    private  NettyServerBootstrap serverBootstrap;

    // sign_cm_240  构造器
    public AbstractNettyRemotingServer(ThreadPoolExecutor messageExecutor, NettyServerConfig nettyServerConfig) {
        super(messageExecutor);
        serverBootstrap = new NettyServerBootstrap(nettyServerConfig);  // 创建服务引导类，ref: sign_cm_250
        serverBootstrap.setChannelHandlers(new ServerHandler());        // sign_cb_240 添加额外的信道处理器
    }

    // sign_m_240  初始化
    @Override
    public void init() {
        super.init();
        serverBootstrap.start(); // 启动 Netty 服务监听，ref: sign_m_310
    }
}
```

- `io.seata.core.rpc.netty.NettyServerBootstrap`
```java
// sign_c_250  Netty 服务引导类
public class NettyServerBootstrap implements RemotingBootstrap {
    
    private final ServerBootstrap serverBootstrap = new ServerBootstrap();
    private final EventLoopGroup eventLoopGroupWorker;
    private final EventLoopGroup eventLoopGroupBoss;
    private final NettyServerConfig nettyServerConfig;
    private ChannelHandler[] channelHandlers;
    private int listenPort;

    // sign_cm_250  构造器
    public NettyServerBootstrap(NettyServerConfig nettyServerConfig) {
        this.nettyServerConfig = nettyServerConfig;
        if (NettyServerConfig.enableEpoll()) { // 使用 epoll 的处理
            this.eventLoopGroupBoss = new EpollEventLoopGroup(...);
            this.eventLoopGroupWorker = new EpollEventLoopGroup(...);
        } else {
            this.eventLoopGroupBoss = new NioEventLoopGroup(...);
            this.eventLoopGroupWorker = new NioEventLoopGroup(...);
        }
    }
}
```

### 启动-Netty-服务
- `io.seata.core.rpc.netty.NettyServerBootstrap`
```java
// sign_c_310  Netty 服务引导类
public class NettyServerBootstrap implements RemotingBootstrap {

    // sign_m_310  启动 Netty 服务监听
    @Override
    public void start() {
        int port = getListenPort(); // 获取监听端口，一般返回 8091, ref: sign_m_311
        this.serverBootstrap
            .group(this.eventLoopGroupBoss, this.eventLoopGroupWorker)
            .channel(NettyServerConfig.SERVER_CHANNEL_CLAZZ)
            .option(ChannelOption.SO_BACKLOG, nettyServerConfig.getSoBackLogSize())
            .option(ChannelOption.SO_REUSEADDR, true)
            .childOption(ChannelOption.SO_KEEPALIVE, true)
            .childOption(ChannelOption.TCP_NODELAY, true)
            .childOption(ChannelOption.SO_SNDBUF, nettyServerConfig.getServerSocketSendBufSize())
            .childOption(ChannelOption.SO_RCVBUF, nettyServerConfig.getServerSocketResvBufSize())
            .childOption(ChannelOption.WRITE_BUFFER_WATER_MARK, new WriteBufferWaterMark(...))
            .localAddress(new InetSocketAddress(port))
            .childHandler(new ChannelInitializer<SocketChannel>() {
                @Override
                public void initChannel(SocketChannel ch) {
                    ch.pipeline()
                        .addLast(new IdleStateHandler(..., 0, 0))
                        .addLast(new ProtocolV1Decoder())
                        .addLast(new ProtocolV1Encoder());
                    if (channelHandlers != null) {
                        addChannelPipelineLast(ch, channelHandlers); // 添加额外的信道处理器，来源参考： sign_cb_240
                    }
                }
            });

        try {
            this.serverBootstrap.bind(port).sync();
            ...
            InetSocketAddress address = new InetSocketAddress(XID.getIpAddress(), XID.getPort());
            for (RegistryService<?> registryService : MultiRegistryFactory.getInstances()) {
                registryService.register(address);
            }
            initialized.set(true);
        } 
        ... // catch
    }

    // sign_m_311  获取监听端口，一般返回 8091
    public int getListenPort() {
        ...

        String strPort = ConfigurationFactory.getInstance().getConfig(SERVER_SERVICE_PORT_CAMEL); // 从环境中读取，结果为: 8091
        int port = 0;
        try {
            port = Integer.parseInt(strPort);
        } 
        ...

        listenPort = port;
        return port;
    }
}
```