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
                case 0: // 打印帮助 (输出所有的子命令 -> 指令和描述)
                    printHelp();
                    break;
                case 2:
                    if (args[0].equals("help")) {
                        // 打印子命令的帮助信息
                        SubCommand cmd = findSubCommand(args[1]);   // 查找对应的子命令
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
                    SubCommand cmd = findSubCommand(args[0]);       // 查找对应的子命令
                    if (cmd != null) {
                        String[] subargs = parseSubArgs(args);      // 解析子命令参数

                        Options options = ServerUtil.buildCommandlineOptions(new Options());
                        final CommandLine commandLine = ServerUtil.parseCmdLine(
                            "mqadmin " + cmd.commandName(), subargs, 
                            cmd.buildCommandlineOptions(options),
                            new DefaultParser()
                        );
                        ... // 校验

                        if (commandLine.hasOption('n')) {   // -n 命令参数指定命令服务；此处逻辑是记录命令服务地址
                            String namesrvAddr = commandLine.getOptionValue('n');
                            System.setProperty(MixAll.NAMESRV_ADDR_PROPERTY, namesrvAddr);
                        }

                        ...
                            cmd.execute(commandLine, options, AclUtils.getAclRPCHook(..._FILE));    // 执行具体命令
                    } 
                    ... // else
                    break;
            }
        } ... // catch
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