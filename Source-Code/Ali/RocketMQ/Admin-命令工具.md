# RocketMQ-Admin-命令工具


---
## main
- 启动脚本 `.\bin\mqadmin.cmd`
  - 参考：[RocketMQ-单机本地部署-测试](../../../X-In-Action/Ali-X/RocketMQ-单机本地部署.md#测试)
```bat
rem  需先设置 ROCKETMQ_HOME 环境变量，否则直接退出

if not exist "%ROCKETMQ_HOME%\bin\tools.cmd" echo Please set the ROCKETMQ_HOME variable ...! & EXIT /B 1

call "%ROCKETMQ_HOME%\bin\tools.cmd" ^                  rem  设置 JVM 参数
  -Drmq.logback.configurationFile=%ROCKETMQ_HOME%\conf\rmq.tools.logback.xml ^
  org.apache.rocketmq.tools.command.MQAdminStartup %*   rem  main 类，ref: sign_c_010
```

- **示例**
```js
// sign_dome_010  更新或创建主题
mqadmin updateTopic -b 127.0.0.1:10911 -t TopicA
```

- `org.apache.rocketmq.tools.command.MQAdminStartup`
```java
// sign_c_010
public class MQAdminStartup {

    public static void main(String[] args) {
        args = "updateTopic -b 127.0.0.1:10911 -t TopicA".split(" ");   // 相当于上面的示例命令

        main0(args, null);  // ref: sign_sm_020
    }
}
```


---
## 主命令执行
- `org.apache.rocketmq.tools.command.MQAdminStartup`
```java
// sign_c_020
public class MQAdminStartup {
    protected static final List<SubCommand> SUB_COMMANDS = new ArrayList<>();   // sign_f_020  子命令集

    // sign_sm_020
    public static void main0(String[] args, RPCHook rpcHook) {
        ...

        initCommand();  // 初始化命令，ref: sign_m_110

        try {
            switch (args.length) {
                case 0:
                    printHelp();    // 打印帮助 (输出所有的子命令 -> 指令和描述)，ref: sign_sm_021
                    break;
                case 2:
                    if (args[0].equals("help")) {
                        // 打印子命令的帮助信息
                        SubCommand cmd = findSubCommand(args[1]);   // 查找对应的子命令，ref: sign_sm_022
                        if (cmd != null) {
                            Options options = ServerUtil.buildCommandlineOptions(new Options());
                            options = cmd.buildCommandlineOptions(options);
                            if (options != null) {                  // 打印子命令帮助信息
                                ServerUtil.printCommandLineHelp("mqadmin " + cmd.commandName(), options);
                            }
                        } ... // else 
                        break;
                    }
                case 1:
                default:
                    SubCommand cmd = findSubCommand(args[0]);       // 查找对应的子命令，ref: sign_sm_022
                    if (cmd != null) {
                        String[] subargs = parseSubArgs(args);      // 解析子命令参数 (排除第一个参数，即：子命令名)

                        Options options = ServerUtil.buildCommandlineOptions(new Options());
                        final CommandLine commandLine = ServerUtil.parseCmdLine(    // 使用 commons-cli 解析
                            "mqadmin " + cmd.commandName(), subargs, 
                            cmd.buildCommandlineOptions(options),   // 构建命令支持的选项，以便输出
                            new DefaultParser() // 解析器带状态，非线程安全，每次用新的
                        );
                        ... // 校验

                        if (commandLine.hasOption('n')) {   // -n 命令参数指定命令服务；此处逻辑是记录命令服务地址
                            String namesrvAddr = commandLine.getOptionValue('n');
                            System.setProperty(MixAll.NAMESRV_ADDR_PROPERTY, namesrvAddr);
                        }

                        ...
                            cmd.execute(commandLine, options, AclUtils.getAclRPCHook(..._FILE));    // 执行具体命令，ref: sign_m_210
                    } 
                    ... // else
                    break;
            }
        } ... // catch
    }

    // sign_sm_021  打印帮助
    private static void printHelp() {
        ...
        for (SubCommand cmd : SUB_COMMANDS) {
            // %-35s 表示字符长度 35 个，不足的用空格填充
            System.out.printf("   %-35s %s%n", cmd.commandName(), cmd.commandDesc());   // ref: sign_m_120 | sign_m_121
        }
        ...
    }

    // sign_sm_022  查找子命令
    private static SubCommand findSubCommand(final String name) {
        for (SubCommand cmd : SUB_COMMANDS) {
            if (cmd.commandName().equalsIgnoreCase(name)    // ref: sign_m_120
                || ... cmd.commandAlias().equalsIgnoreCase(name)
            ) { // 名称或别名相等就返回 (表示已找到)
                return cmd; 
            }
        }
        return null;
    }
}
```


---
## 初始化命令
- `org.apache.rocketmq.tools.command.MQAdminStartup`
```java
// sign_c_110
public class MQAdminStartup {

    // sign_m_110  初始化命令
    public static void initCommand() {
        initCommand(new UpdateTopicSubCommand());       // 添加子命令，ref: sign_m_111 | sign_c_120
        initCommand(new DeleteTopicSubCommand());
        initCommand(new UpdateSubGroupSubCommand());
        ... // 其他子命令添加
    }

    // sign_m_111  添加子命令
    public static void initCommand(SubCommand command) {
        SUB_COMMANDS.add(command);  // (未做其他处理) 直接添加到集合，ref: sign_f_020
    }
}
```

- `org.apache.rocketmq.tools.command.topic.UpdateTopicSubCommand`
```java
// sign_c_120  改 Topic 子命令 (示例)
public class UpdateTopicSubCommand implements SubCommand {

    // sign_m_120  命令名 (即：指令)
    @Override
    public String commandName() {
        return "updateTopic";
    }

    // sign_m_121  命令描述
    @Override
    public String commandDesc() {
        return "Update or create topic.";
    }
}
```


---
## 子命令执行
- `org.apache.rocketmq.tools.command.topic.UpdateTopicSubCommand`
```java
// sign_c_210  改 Topic 子命令 (示例)
public class UpdateTopicSubCommand implements SubCommand {

    // 示例： -b 127.0.0.1:10911 -t TopicA

    // sign_m_210  具体命令执行体
    @Override
    public void execute(final CommandLine commandLine, final Options options, RPCHook rpcHook) ... {
        DefaultMQAdminExt defaultMQAdminExt = new DefaultMQAdminExt(rpcHook);   // ref: sign_cm_310
        ...

        try {
            TopicConfig topicConfig = new TopicConfig();
            ...
            topicConfig.setTopicName(           // 设置 Topic 名称
                commandLine.getOptionValue('t') // 读取 -t 选项对应的值
            );
            ... // 其他命令选项处理

            if (commandLine.hasOption('b')) {
                String addr = commandLine.getOptionValue('b').trim();

                defaultMQAdminExt.start();      // 初始化客户端，ref: sign_m_310
                defaultMQAdminExt.createAndUpdateTopicConfig(addr, topicConfig);    // 发送指令，ref: sign_m_410

                ... // 处理 -o 选项 (排序处理)
                ... // 输出成功信息
                return;
            }
            ... // -c 选项处理

            // 没有 -b 或 -c 选项，则打印当前命令的帮助信息
            ServerUtil.printCommandLineHelp("mqadmin " + this.commandName(), options);
        } 
        ... // catch finally
    }
}
```


---
## 远程通信
### 初始化客户端
- `org.apache.rocketmq.tools.admin.DefaultMQAdminExt`
```java
// sign_c_310
public class DefaultMQAdminExt extends ClientConfig implements MQAdminExt {
    private final DefaultMQAdminExtImpl defaultMQAdminExtImpl;
    private long timeoutMillis = 5000;

    // sign_cm_310
    public DefaultMQAdminExt(RPCHook rpcHook) {
        this.defaultMQAdminExtImpl = new DefaultMQAdminExtImpl(this, rpcHook, timeoutMillis);   // ref: sign_cm_320
    }

    // sign_m_310  启动 (初始化)
    @Override
    public void start() throws MQClientException {
        defaultMQAdminExtImpl.start();  // ref: sign_m_320
    }
}
```

- `org.apache.rocketmq.tools.admin.DefaultMQAdminExtImpl`
```java
// sign_c_320
public class DefaultMQAdminExtImpl implements MQAdminExt, MQAdminExtInner {

    // sign_cm_320
    public DefaultMQAdminExtImpl(DefaultMQAdminExt defaultMQAdminExt, RPCHook rpcHook, long timeoutMillis) {
        this.defaultMQAdminExt = defaultMQAdminExt;
        this.rpcHook = rpcHook;
        this.timeoutMillis = timeoutMillis;
    }

    // sign_m_320  启动 (初始化)
    @Override
    public void start() throws MQClientException {
        switch (this.serviceState) {
            case CREATE_JUST:
                ...

                this.mqClientInstance = MQClientManager.getInstance().getOrCreateMQClientInstance(...); // 创建，ref: sign_cm_330
                ...

                mqClientInstance.start();                   // 启动，ref: sign_m_330
                this.serviceState = ServiceState.RUNNING;   // 设置服务状态

                ... // 创建线程池
                break;
            ...
        }
    }
}
```

- `org.apache.rocketmq.client.impl.factory.MQClientInstance`
```java
// sign_c_330
public class MQClientInstance {

    // sign_cm_330  客户端实例构造器
    public MQClientInstance(ClientConfig clientConfig, int instanceIndex, String clientId, RPCHook rpcHook) {
        this.clientConfig = clientConfig;
        this.nettyClientConfig = new NettyClientConfig();
        ... // 设置 nettyClientConfig
        ... // 其他处理
       
        this.mQClientAPIImpl = new MQClientAPIImpl(this.nettyClientConfig, ...);    // ref: sign_cm_340
        ...

        this.clientId = clientId;
        this.mQAdminImpl = new MQAdminImpl(this);
        this.pullMessageService = new PullMessageService(this);
        this.rebalanceService = new RebalanceService(this);

        ...
    }
    
    // sign_m_330  客户端实例启动
    public void start() throws MQClientException {
        synchronized (this) {
            switch (this.serviceState) {
                case CREATE_JUST:
                    ...

                    this.mQClientAPIImpl.start();   // 初始化客户端，ref: sign_m_340
                    this.pullMessageService.start();// 启动拉取消息服务 (相当于启动拉取线程)
                    ... // 启动其他服务的线程或线程池

                    this.serviceState = ServiceState.RUNNING;   // 设置状态
                    break;
                ...
            }
        }
    }
}
```

- `org.apache.rocketmq.client.impl.MQClientAPIImpl`
```java
// sign_c_340
public class MQClientAPIImpl implements NameServerUpdateCallback {

    // sign_cm_340
    public MQClientAPIImpl(...) {
        this(nettyClientConfig, clientRemotingProcessor, rpcHook, clientConfig, null);  // ref: sign_cm_341
    }

    // sign_cm_341
    public MQClientAPIImpl(..., final ChannelEventListener channelEventListener) {
        this.clientConfig = clientConfig;
        ...

        this.remotingClient = new NettyRemotingClient(nettyClientConfig, channelEventListener); // ref: sign_cm_350
        this.clientRemotingProcessor = clientRemotingProcessor;
        ...

        this.remotingClient.registerProcessor(RequestCode.CHECK_TRANSACTION_STATE, this.clientRemotingProcessor, null);
        this.remotingClient.registerProcessor(RequestCode.NOTIFY_CONSUMER_IDS_CHANGED, ...);        // 同上，注册处理器
        this.remotingClient.registerProcessor(RequestCode.RESET_CONSUMER_CLIENT_OFFSET, ...);
        this.remotingClient.registerProcessor(RequestCode.GET_CONSUMER_STATUS_FROM_CLIENT, ...);
        this.remotingClient.registerProcessor(RequestCode.GET_CONSUMER_RUNNING_INFO, ...);
        this.remotingClient.registerProcessor(RequestCode.CONSUME_MESSAGE_DIRECTLY, ...);
        this.remotingClient.registerProcessor(RequestCode.PUSH_REPLY_MESSAGE_TO_CLIENT, ...);
    }

    // sign_m_340  初始化客户端
    public void start() {
        this.remotingClient.start();    // 初始化 Bootstrap，ref: sign_m_350
    }
}
```

- `org.apache.rocketmq.remoting.netty.NettyRemotingClient`
```java
// sign_c_350
public class NettyRemotingClient extends NettyRemotingAbstract implements RemotingClient {
    private final Bootstrap bootstrap = new Bootstrap();    // sign_f_350  客户端 Bootstrap

    // sign_cm_350
    public NettyRemotingClient(final NettyClientConfig nettyClientConfig, final ChannelEventListener channelEventListener) {
        this(nettyClientConfig, channelEventListener, null, null);  // ref: sign_cm_351
    }

    // sign_cm_351
    public NettyRemotingClient(..., final EventLoopGroup eventLoopGroup, final EventExecutorGroup eventExecutorGroup) {
        super(nettyClientConfig.getClientOnewaySemaphoreValue(), nettyClientConfig.getClientAsyncSemaphoreValue());
        this.nettyClientConfig = nettyClientConfig;
        this.channelEventListener = channelEventListener;

        ...
        this.publicExecutor = Executors.newFixedThreadPool(publicThreadNums, ...);
        this.scanExecutor = ThreadUtils.newThreadPoolExecutor(4, 10, 60, TimeUnit.SECONDS, ...);

        ...
            // 创建 Netty 线程池
            this.eventLoopGroupWorker = new NioEventLoopGroup(1, new ThreadFactoryImpl("NettyClientSelector_"));

        ... // TLS 设置
    }

    // sign_m_350  初始化 Netty 客户端 Bootstrap
    @Override
    public void start() {
        ... // 初始化 defaultEventExecutorGroup

        // 初始化客户端 Bootstrap, ref: sign_f_350
        Bootstrap handler = this.bootstrap.group(this.eventLoopGroupWorker).channel(NioSocketChannel.class)
            .option(ChannelOption.TCP_NODELAY, true)
            .option(ChannelOption.SO_KEEPALIVE, false)
            .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, nettyClientConfig.getConnectTimeoutMillis())
            .handler(new ChannelInitializer<SocketChannel>() {
                @Override
                public void initChannel(SocketChannel ch) throws Exception {
                    ChannelPipeline pipeline = ch.pipeline();
                    ... // TSL(SSL) 设置
                    ch.pipeline().addLast(
                        ... defaultEventExecutorGroup,
                        new NettyEncoder(),
                        new NettyDecoder(),
                        new IdleStateHandler(0, 0, nettyClientConfig.getClientChannelMaxIdleTimeSeconds()),
                        new NettyConnectManageHandler(),
                        new NettyClientHandler()
                    );
                }
            });
        ... // 设置 Bootstrap 其他选项

        nettyEventExecutor.start();
        ... // 开启其他定时任务
    }
}
```


### 连接并发送命令
- `org.apache.rocketmq.tools.admin.DefaultMQAdminExt`
```java
// sign_c_410
public class DefaultMQAdminExt extends ClientConfig implements MQAdminExt {

    // sign_m_410  发送指令 (创建或修改 Topic)
    @Override
    public void createAndUpdateTopicConfig(String addr, TopicConfig config) throws ... {
        defaultMQAdminExtImpl.createAndUpdateTopicConfig(addr, config); // 创建或修改 Topic, ref: sign_m_420
    }
}
```

- `org.apache.rocketmq.tools.admin.DefaultMQAdminExtImpl`
```java
// sign_c_420
public class DefaultMQAdminExtImpl implements MQAdminExt, MQAdminExtInner {

    // sign_m_420  创建或修改 Topic
    @Override
    public void createAndUpdateTopicConfig(String addr, TopicConfig config) throws ... {
        this.mqClientInstance.getMQClientAPIImpl()  // 返回 MQClientAPIImpl 实例
            .createTopic(addr, ..., config, ...);   // 创建 Topic, ref: sign_m_430
    }
}
```

- `org.apache.rocketmq.client.impl.MQClientAPIImpl`
```java
// sign_c_430
public class MQClientAPIImpl implements NameServerUpdateCallback {

    // sign_m_430  创建 Topic
    public void createTopic(final String addr, ..., final TopicConfig topicConfig, ...) throws ... {
        CreateTopicRequestHeader requestHeader = new CreateTopicRequestHeader();
        requestHeader.setTopic(topicConfig.getTopicName());
        requestHeader.setPerm(topicConfig.getPerm());
        ... // 将配置设置到请求头
        requestHeader.setAttributes(AttributeParser.parseToString(topicConfig.getAttributes()));

        RemotingCommand request = RemotingCommand.createRequestCommand(RequestCode.UPDATE_AND_CREATE_TOPIC, requestHeader);
        RemotingCommand response = this.remotingClient.invokeSync(... addr, request, ...);  // 发送请求，ref: sign_m_440
        
        ... // 校验响应结果，不成功则抛异常
    }
}
```

- `org.apache.rocketmq.remoting.netty.NettyRemotingClient`
```java
// sign_c_440
public class NettyRemotingClient extends NettyRemotingAbstract implements RemotingClient {  // 继承 ref: sign_c_450

    // sign_m_440  发送请求
    @Override
    public RemotingCommand invokeSync(String addr, final RemotingCommand request, ...) throws ... {
        final Channel channel = this.getAndCreateChannel(addr); // 获取信道，ref: sign_m_441

        if (channel != null && channel.isActive()) {
            try {
                ... // 超时校验
                RemotingCommand response = super.invokeSyncImpl(channel, request, left);    // (父类方法)发送请求，ref: sign_m_450
                ...
                return response;
            } 
            ... // catch
        }   ... // else
    }

    // sign_m_441  获取或创建信道
    private Channel getAndCreateChannel(final String addr) throws InterruptedException {
        ... // 从缓存拿取；没有才进行创建
        return this.createChannel(addr);    // ref: sign_m_442
    }

    // sign_m_442  创建信道
    private Channel createChannel(final String addr) throws InterruptedException {
        ... // 从缓存拿取

        if (this.lockChannelTables.tryLock(LOCK_TIMEOUT_MILLIS, TimeUnit.MILLISECONDS)) {
            try {
                ... // 从缓存拿取

                if (createNewConnection) {
                    String[] hostAndPort = getHostAndPort(addr);        // 将 "127.0.0.1:10911" 解析成 ["127.0.0.1", "10911"]

                    ChannelFuture channelFuture = fetchBootstrap(addr)  // 没有代理连接配置，直接返回 bootstrap, ref: sign_f_350
                        .connect(hostAndPort[0], Integer.parseInt(hostAndPort[1])); // 连接服务器
                    ... // log

                    cw = new ChannelWrapper(addr, channelFuture);
                    ... // 加入到缓存
                }
            } 
            ... // catch 
        }   ... // else

        ...
            return waitChannelFuture(addr, cw); // 等待连接完成，并返回连接信道
    }

}
```

- `org.apache.rocketmq.remoting.netty.NettyRemotingAbstract`
```java
// sign_c_450  远程通信父类
public abstract class NettyRemotingAbstract {
    
    // sign_m_450  发送请求
    public RemotingCommand invokeSyncImpl(final Channel channel, final RemotingCommand request, ...) throws ... {
        try {
            return invokeImpl(channel, request, timeoutMillis)  // 发送请求，ref: sign_m_451
                .thenApply(ResponseFuture::getResponseCommand)
                .get(timeoutMillis, TimeUnit.MILLISECONDS);     // 同步等待
        } 
        ... // catch
    }

    // sign_m_451  发送请求
    public CompletableFuture<ResponseFuture> invokeImpl(final Channel channel, final RemotingCommand request, ...) {
        ... // 前钩子处理
        return invoke0(channel, request, timeoutMillis) // RPC 调用，ref: sign_m_452
                .whenComplete((v, t) -> {
                    ... // 后钩子处理
                });
    }
    
    // sign_m_452  通过 Netty 发送请求 (RPC 调用)
    protected CompletableFuture<ResponseFuture> invoke0(final Channel channel, final RemotingCommand request, ...) {
        CompletableFuture<ResponseFuture> future = new CompletableFuture<>();
        final int opaque = request.getOpaque();

        ... // 获取请求锁 (信号)
        if (acquired) {
            ... // 超时处理
            ... // 设置异步钩子
            try {
                channel.writeAndFlush(request)  // 通过信道发送请求
                    .addListener((ChannelFutureListener) f -> {
                        if (f.isSuccess()) {
                            responseFuture.setSendRequestOK(true);  // 设置成功
                            return;
                        }
                        requestFail(opaque);    // 设置失败
                    });
                return future;
            } 
            ... // catch
        } 
        ...     // else  未获得锁，抛出异常
    }
}
```


### 总结
- 调用链：
```js
SubCommand  -> DefaultMQAdminExt -> DefaultMQAdminExtImpl 
            -> MQClientInstance 
            -> MQClientAPIImpl   -> NettyRemotingClient    (RPC 通信  ->  NettyRemotingAbstract)
```

- 响应结果会通过 `ResponseFuture` 返回
  - `responseFuture.setResponseCommand(cmd);` (设置响应)