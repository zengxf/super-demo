# RocketMQ-Broker-启动


---
## main
- `org.apache.rocketmq.broker.BrokerStartup`
```java
public class BrokerStartup {

    public static void main(String[] args) {
        String home = "D:\\Install\\Java\\Ali\\rocketmq\\rocketmq-all-5.2.0-bin-release";
        System.setProperty(MixAll.ROCKETMQ_HOME_PROPERTY, home);    // 手动设置下变量，否则启动不了

        args = new String[]{"-n localhost:9876"};   // 手动设置命名服务地址
        BrokerController brokerController = createBrokerController(args);   // 创建控制器，ref: sign_sm_110
        start(brokerController);    // 启动控制器，ref: sign_m_210
    }
}
```


---
## 初始化控制器
- `org.apache.rocketmq.broker.BrokerStartup`
```java
// sign_c_110
public class BrokerStartup {

    // sign_sm_110  创建控制器
    public static BrokerController createBrokerController(String[] args) {
        try {
            BrokerController controller = buildBrokerController(args);  // 构建控制器，ref: sign_sm_111
            boolean initResult = controller.initialize();               // 控制器初始化，ref: sign_m_120
            ... // 校验、加钩子
            return controller;
        } ... // catch
        return null;
    }

    // sign_sm_111  构建控制器
    public static BrokerController buildBrokerController(String[] args) throws Exception {
        ...

        final BrokerConfig brokerConfig = new BrokerConfig();
        final NettyServerConfig nettyServerConfig = new NettyServerConfig();
        ... // nettyClientConfig messageStoreConfig
        nettyServerConfig.setListenPort(10911); // 设置默认监听端口
        ...

        Options options = ServerUtil.buildCommandlineOptions(new Options());
        CommandLine commandLine = ServerUtil.parseCmdLine("mqbroker", args, buildCommandlineOptions(options), new DefaultParser());
        ...
        ... // 将 properties 填充到各 config

        MixAll.properties2Object(ServerUtil.commandLine2Properties(commandLine), brokerConfig);
        ... // check

        // 校验并记录命名服务地址
        String namesrvAddr = brokerConfig.getNamesrvAddr();
        if (StringUtils.isNotBlank(namesrvAddr)) {
            try {
                String[] addrArray = namesrvAddr.split(";");
                for (String addr : addrArray) {
                    NetworkUtil.string2SocketAddress(addr);
                }
            } ... // catch
        }
        ...

        ... // 根据主从角色设置 broker ID
        ... // check
        ... // 根据 broker 配置设置系统配置
        ... // 命令行 -p; -m 的打印
        ... // log

        final BrokerController controller = new BrokerController(...Config);
        controller.getConfiguration().registerConfig(properties);   // 合并配置，将 properties 合并到 configuration 中
        return controller;
    }
}
```

- `org.apache.rocketmq.broker.BrokerController`
  - 远程服务端参考：[命名服务启动-启动控制器 sign_cm_220](./命名服务启动.md#启动控制器)
```java
// sign_c_120  Broker-控制器
public class BrokerController {

    // sign_m_120  初始化
    public boolean initialize() throws CloneNotSupportedException {
        boolean result = this.initializeMetadata(); // 初始化元数据，ref: sign_m_121
        ... // check

        result = this.initializeMessageStore();     // 初始化消息存储，ref: sign_m_122
        ... // check

        return this.recoverAndInitService();        // 恢复和初始化服务，ref: sign_m_123
    }
    
    // sign_m_121  初始化元数据
    public boolean initializeMetadata() {
        boolean result = this.topicConfigManager.load();            // 从缓存文件中加载配置
        result = result && this.topicQueueMappingManager.load();
        result = result && this.consumerOffsetManager.load();
        result = result && this.subscriptionGroupManager.load();
        result = result && this.consumerFilterManager.load();
        result = result && this.consumerOrderInfoManager.load();
        return result;
    }
    
    // sign_m_122  初始化消息存储
    public boolean initializeMessageStore() {
        boolean result = true;
        try {
            DefaultMessageStore defaultMessageStore;
            if (this.messageStoreConfig.isEnableRocksDBStore()) {
                defaultMessageStore = new RocksDBMessageStore(this.messageStoreConfig, ...);
            } else {
                defaultMessageStore = new DefaultMessageStore(this.messageStoreConfig, ...);
            }
            ...

            // Load store plugin
            MessageStorePluginContext context = new MessageStorePluginContext(messageStoreConfig, ...);
            this.messageStore = MessageStoreFactory.build(context, defaultMessageStore);    // 构建消息存储实例
            ...
            if (messageStoreConfig.isTimerWheelEnable()) {
                this.timerCheckpoint = new TimerCheckpoint(...);    // 停机时保存检测点
                ...
                this.timerMessageStore = new TimerMessageStore(...);// 定时存储处理
                ...
                this.messageStore.setTimerMessageStore(this.timerMessageStore);
            }
        } ... // catch
        return result;
    }

    // sign_m_123  恢复和初始化服务
    public boolean recoverAndInitService() throws CloneNotSupportedException {
        boolean result = true;

        ... // 加载配置文件和索引文件

        if (result) {
            initializeRemotingServer(); // 初始化远程监听 (Netty) 服务，ref: sign_m_124
            initializeResources();      // 初始化线程池
            registerProcessor();        // 注册处理器
            initializeScheduledTasks(); // 开启各种定时任务
            initialTransaction();       // 初始化事务管理
            initialAcl();               // 初始化访问控制
            initialRpcHooks();          // 初始化 RPC 钩子

            if (TlsSystemConfig.tlsMode != TlsMode.DISABLED) {
                // Register a listener to reload SslContext
                try {
                    fileWatchService = new FileWatchService(
                        ... // 监听证书文件
                    );
                } ... // catch
            }
        }

        return result;
    }

    // sign_m_124  初始化远程监听 (Netty) 服务
    protected void initializeRemotingServer() throws CloneNotSupportedException {
        this.remotingServer = new NettyRemotingServer(this.nettyServerConfig, ...); // 创建远程服务。参考：[命名服务启动-启动控制器 sign_cm_220]
        NettyServerConfig fastConfig = (NettyServerConfig) this.nettyServerConfig.clone();

        int listeningPort = nettyServerConfig.getListenPort() - 2;
        ...
        fastConfig.setListenPort(listeningPort);

        this.fastRemotingServer = new NettyRemotingServer(fastConfig, ...);         // 创建远程服务。参考：[命名服务启动-启动控制器 sign_cm_220]
    }
}
```


---
## 启动控制器
- `org.apache.rocketmq.broker.BrokerStartup`
```java
// sign_c_210
public class BrokerStartup {
    
    // sign_m_210  启动控制器
    public static BrokerController start(BrokerController controller) {
        try {
            controller.start();     // 启动，ref: sign_m_220
            ... // log
            return controller;
        } 
        ... // catch { exit(-1) }
    }
}
```

- `org.apache.rocketmq.broker.BrokerController`
  - 服务端启动参考：[命名服务启动-启动控制器 sign_m_220](./命名服务启动.md#启动控制器)
```java
// sign_c_220
public class BrokerController {

    // sign_m_220  启动
    public void start() throws Exception {
        ...
            this.brokerOuterAPI.start();

        startBasicService();    // 启动基础服务，ref: sign_m_221
        ...

        // 开启定时任务
            BrokerController.this.registerBrokerAll(true, false, brokerConfig.isForceRegister());
            BrokerController.this.sendHeartbeat();
            BrokerController.this.syncBrokerMemberGroup();
            ScheduleMessageService.this.persist(); // this.scheduleMessageService.start(); // startServiceWithoutCondition();
            this.transactionalMessageCheckService.start(); // startServiceWithoutCondition();
            BrokerController.this.brokerOuterAPI.refreshMetadata();
    }

    // sign_m_221  启动基础服务
    protected void startBasicService() throws Exception {
        ...
            this.messageStore.start();
            this.timerMessageStore.start();
            this.replicasManager.start();
            this.remotingServer.start();        // 服务端启动参考：[命名服务启动-启动控制器 sign_m_220]
            ...
            this.fastRemotingServer.start();    // 服务端启动参考：[命名服务启动-启动控制器 sign_m_220]

        ...

        for (BrokerAttachedPlugin brokerAttachedPlugin : brokerAttachedPlugins) {
            if (brokerAttachedPlugin != null) {
                brokerAttachedPlugin.start();
            }
        }

        if (this.popMessageProcessor != null) {
            this.popMessageProcessor.getPopLongPollingService().start();
            this.popMessageProcessor.getPopBufferMergeService().start();
            this.popMessageProcessor.getQueueLockManager().start();
        }
        ...

            this.ackMessageProcessor.startPopReviveService();
            this.notificationProcessor.getPopLongPollingService().start();
            this.topicQueueMappingCleanService.start();
            this.fileWatchService.start();
            this.pullRequestHoldService.start();
            this.clientHousekeepingService.start();
            this.brokerStatsManager.start();
            this.brokerFastFailure.start();
            this.broadcastOffsetManager.start();
            this.escapeBridge.start();
            this.topicRouteInfoManager.start();
            this.brokerPreOnlineService.start();
            this.coldDataPullRequestHoldService.start();
            this.coldDataCgCtrService.start();
    }
}
```