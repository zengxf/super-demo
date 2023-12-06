## 测试
- 模块：`sentinel-dashboard`
  - 先启动 `DashboardApplication`
  - 访问 http://localhost:8080/#/dashboard
    - 登录：`sentinel / sentinel`

- 模块：`sentinel-demo-spring-webmvc`
  - 在 `WebMvcDemoApplication` 类的 `main()` 方法改成如下：
  ```java
      public static void main(String[] args) {
          System.setProperty("csp.sentinel.dashboard.server", "127.0.0.1:8080");
          System.setProperty("project.name", "My-Test-8866");
          SpringApplication.run(WebMvcDemoApplication.class);
      }
  ```

  - 再启动 `WebMvcDemoApplication`
    - 访问 http://localhost:10000/hello
    - dashboard 才会显示


## 原理
- `demo-webmvc` 依赖模块：
  - `sentinel-spring-webmvc-adapter`
    - 用于**链路控制适配**
  - `sentinel-transport-simple-http` (相同的有 `sentinel-transport-netty-http`)
    - 用于**控制台交互和心跳检测**

### 链路控制适配
- `com.alibaba.csp.sentinel.adapter.spring.webmvc.SentinelWebInterceptor`
```java
/** 使用 SpringMVC 拦截器进行拦截，在 WebMvcConfigurer 里进行配置 */
public class SentinelWebInterceptor extends AbstractSentinelInterceptor {

    private final SentinelWebMvcConfig config;

    public SentinelWebInterceptor() {
        this(new SentinelWebMvcConfig());
    }

    public SentinelWebInterceptor(SentinelWebMvcConfig config) {
        super(config);
        ... // 省略
    }

}
```

- `com.alibaba.csp.sentinel.adapter.spring.webmvc.AbstractSentinelInterceptor`
```java
/** Sentinel 拦截器 (做控制逻辑) */
public abstract class AbstractSentinelInterceptor implements HandlerInterceptor {

    // 拦截前处理
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler)
        throws Exception 
    {
        try {
            String resourceName = getResourceName(request);

            ... // resourceName 为空返回 true
            
            if (increaseReferece(request, this.baseWebMvcConfig.getRequestRefName(), 1) != 1) {
                return true;  // 只对首个进行拦截处理
            }
            
            ... // 省略上下文处理
            Entry entry = SphU.entry(resourceName, ResourceTypeConstants.COMMON_WEB, EntryType.IN); // 正式流控
            request.setAttribute(baseWebMvcConfig.getRequestAttributeName(), entry);                // 做记录，方便后面退出处理
            return true;
        } catch (BlockException e) {
            try {
                handleBlockException(request, response, e); // 异常处理 sign_m_010
            } finally {
                ContextUtil.exit();
            }
            return false; // 流控限制
        }
    }
    
    // sign_m_010 异常处理
    protected void handleBlockException(HttpServletRequest request, HttpServletResponse response, BlockException e)
        throws Exception 
    {
        if (baseWebMvcConfig.getBlockExceptionHandler() != null) {
            baseWebMvcConfig.getBlockExceptionHandler().handle(request, response, e);
        } else {
            throw e;
        }
    }

    // 完成后处理
    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) throws Exception 
    {
        if (increaseReferece(request, this.baseWebMvcConfig.getRequestRefName(), -1) != 0) {
            return; // 不在最后一个 (相当于首个) 不处理
        }
        
        Entry entry = getEntryInRequest(request, baseWebMvcConfig.getRequestAttributeName());
        if (entry == null) {
            ... // log warn
            return;
        }
        
        traceExceptionAndExit(entry, ex); // 退出处理
        removeEntryInRequest(request);    // 移除 request 属性
        ContextUtil.exit();
    }

}
```

#### 拦截器添加示例
- `com.alibaba.csp.sentinel.demo.spring.webmvc.config.InterceptorConfig`
```java
// 使用 Spring 配置
@Configuration
public class InterceptorConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        addSpringMvcInterceptor(registry);  
    }

    private void addSpringMvcInterceptor(InterceptorRegistry registry) {
        SentinelWebMvcConfig config = new SentinelWebMvcConfig();
        ... // 省略其他配置
        config.setOriginParser(request -> request.getHeader("S-user"));
        // 添加到拦截器链
        registry.addInterceptor(new SentinelWebInterceptor(config)).addPathPatterns("/**");
    }
}
```

### 控制台交互和心跳检测
- 以 `sentinel-transport-netty-http` 模块做示例

#### 交互服务启动
- SPI 设置 `CommandCenter` 的实现为 `NettyHttpCommandCenter`

- 启动栈示例：
```js
java.lang.RuntimeException: 栈跟踪
    at com.alibaba.csp.sentinel.transport.command.NettyHttpCommandCenter.start(NettyHttpCommandCenter.java:46)    // sign_m_204
    at com.alibaba.csp.sentinel.transport.init.CommandCenterInitFunc.init(CommandCenterInitFunc.java:40)
    at com.alibaba.csp.sentinel.init.InitExecutor.doInit(InitExecutor.java:53)
    at com.alibaba.csp.sentinel.Env.<clinit>(Env.java:36)
    at com.alibaba.csp.sentinel.SphU.entry(SphU.java:294)
    at com.alibaba.csp.sentinel.adapter.spring.webmvc.AbstractSentinelInterceptor.preHandle(AbstractSentinelInterceptor.java:105)
    ... // 来自 HTTP 处理链
```

- `com.alibaba.csp.sentinel.transport.command.NettyHttpCommandCenter`
```java
@Spi(order = Spi.ORDER_LOWEST - 100)
public class NettyHttpCommandCenter implements CommandCenter {

    private final HttpServer server = new HttpServer();

    @Override
    public void beforeStart() throws Exception {
        // sign_use_010  SPI 加载实例
        Map<String, CommandHandler> handlers = CommandHandlerProvider.getInstance().namedHandlers();
        server.registerCommands(handlers);  // 注册命令处理器
    }

    // sign_m_204
    @Override
    public void start() throws Exception {
        new RuntimeException("栈跟踪").printStackTrace();
        pool.submit(new Runnable() {
            @Override
            public void run() {
                try {
                    server.start(); // sign_m_205
                } ... // catch
            }
        });
    }
}
```

- `com.alibaba.csp.sentinel.transport.command.netty.HttpServer`
```java
public final class HttpServer {

    private static final int DEFAULT_PORT = 8719;

    // sign_m_205
    public void start() throws Exception {
        ... // EventLoopGroup
        try {
            ServerBootstrap b = new ServerBootstrap();
            b.group(bossGroup, workerGroup)
                .channel(NioServerSocketChannel.class)
                .childHandler(new HttpServerInitializer()); // 增加 HttpServerHandler 到双向处理链，ref: sign_c_205
            int port;
            ... // 读取 port
            
            int retryCount = 0;
            ChannelFuture channelFuture = null;
            while (true) {
                int newPort = getNewPort(port, retryCount); // 尝试 3 次才端口递增 1
                try {
                    channelFuture = b.bind(newPort).sync();
                    ... // log
                    break;
                } catch (Exception e) {
                    TimeUnit.MILLISECONDS.sleep(30);
                    ... // log
                    retryCount ++;
                }
            }
            ... // channel 赋值
        } ...   // finally
    }

}
```

- `com.alibaba.csp.sentinel.transport.command.netty.HttpServerHandler`
```java
// sign_c_205 Netty 入站处理器
public class HttpServerHandler extends SimpleChannelInboundHandler<Object> {
    @Override
    protected void channelRead0(ChannelHandlerContext ctx, Object msg) throws Exception {
        FullHttpRequest httpRequest = (FullHttpRequest)msg;
        try {
            CommandRequest request = parseRequest(httpRequest);             // 组装消息
            if (StringUtil.isBlank(HttpCommandUtils.getTarget(request))) {
                writeErrorResponse(BAD_REQUEST.code(), "Invalid command", ctx);
                return;
            }
            handleRequest(request, ctx, HttpUtil.isKeepAlive(httpRequest)); // 处理请求 sign_m_210
        } ... // catch
    }

    // sign_m_210 处理请求
    private void handleRequest(CommandRequest request, ChannelHandlerContext ctx, boolean keepAlive)
        throws Exception 
    {
        String commandName = HttpCommandUtils.getTarget(request);
        CommandHandler<?> commandHandler = getHandler(commandName);         // 查找处理器
        if (commandHandler != null) {
            CommandResponse<?> response = commandHandler.handle(request);   // sign_use_100  处理命令
            writeResponse(response, ctx, keepAlive);
        } else {
            writeErrorResponse(BAD_REQUEST.code(), String.format("Unknown command \"%s\"", commandName), ctx);
        }
    }
}
```

#### 命令处理器
- 接口为 `com.alibaba.csp.sentinel.command.CommandHandler`
- SPI 加载参考：[交互服务启动 sign_use_010](#交互服务启动)
  - 具体实现为：`com.alibaba.csp.sentinel.command.CommandHandlerProvider #namedHandlers`
- 使用者参考：[交互服务启动 sign_use_100](#交互服务启动)

#### 发送心跳
- SPI 设置 `HeartbeatSender` 的实现为 `HttpHeartbeatSender`

- 启动栈示例：
```js
java.lang.RuntimeException: 心跳启动栈跟踪
	at com.alibaba.csp.sentinel.transport.init.HeartbeatSenderInitFunc.scheduleHeartbeatTask(HeartbeatSenderInitFunc.java:87)   // sign_m_310
	at com.alibaba.csp.sentinel.transport.init.HeartbeatSenderInitFunc.init(HeartbeatSenderInitFunc.java:61)
	at com.alibaba.csp.sentinel.init.InitExecutor.doInit(InitExecutor.java:53)
	at com.alibaba.csp.sentinel.Env.<clinit>(Env.java:36)
	at com.alibaba.csp.sentinel.SphU.entry(SphU.java:294)
	at com.alibaba.csp.sentinel.adapter.spring.webmvc.AbstractSentinelInterceptor.preHandle(AbstractSentinelInterceptor.java:105)
    ... // 来自 HTTP 处理链
```

- `com.alibaba.csp.sentinel.transport.init.HeartbeatSenderInitFunc`
```java
    // sign_m_310 开启心跳定时任务
    private void scheduleHeartbeatTask(final HeartbeatSender sender, long interval) {
        new RuntimeException("心跳启动栈跟踪").printStackTrace();
        pool.scheduleAtFixedRate(new Runnable() {
            @Override
            public void run() {
                try {
                    sender.sendHeartbeat(); // 发心跳 sign_m_320
                } ... // catch
            }
        }, 5000, interval, TimeUnit.MILLISECONDS);
        ... // log
    }
```

- `com.alibaba.csp.sentinel.transport.heartbeat.HttpHeartbeatSender`
```java
@Spi(order = Spi.ORDER_LOWEST - 100)
public class HttpHeartbeatSender implements HeartbeatSender {

    private final Protocol consoleProtocol; // 控制台通信协议
    private final String consoleHost;       // 控制台 IP
    private final int consolePort;          // 控制台端口

    // sign_m_320 发心跳
    @Override
    public boolean sendHeartbeat() throws Exception {
        if (StringUtil.isEmpty(consoleHost)) {
            return false;
        }
        URIBuilder uriBuilder = new URIBuilder();
        uriBuilder.setScheme(consoleProtocol.getProtocol()).setHost(consoleHost).setPort(consolePort)
            // setPath() 默认用 "/registry/machine" (相当于注册，这也是为什么要请求后控制台才显示)
            // 处理方法为 MachineRegistryController #receiveHeartBeat()
            .setPath(TransportConfig.getHeartbeatApiPath())
            .setParameter("app", AppNameUtil.getAppName())
            .setParameter("app_type", String.valueOf(SentinelConfig.getAppType()))
            .setParameter("v", Constants.SENTINEL_VERSION)
            .setParameter("version", String.valueOf(System.currentTimeMillis()))
            .setParameter("hostname", HostNameUtil.getHostName())
            .setParameter("ip", TransportConfig.getHeartbeatClientIp())
            .setParameter("port", TransportConfig.getPort())
            .setParameter("pid", String.valueOf(PidUtil.getPid()));

        HttpGet request = new HttpGet(uriBuilder.build());
        request.setConfig(requestConfig);
        // Send heartbeat request.
        CloseableHttpResponse response = client.execute(request);
        response.close();
        ... // 省略状态判断
    }

}
```

#### 总结
- 要有请求，才会去注册
- 控制台才会显示服务