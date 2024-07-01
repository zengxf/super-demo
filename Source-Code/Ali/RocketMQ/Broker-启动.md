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
        start(brokerController);
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
            boolean initResult = controller.initialize();
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