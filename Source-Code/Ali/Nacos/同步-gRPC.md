## 关联参考
- 参考：[模块介绍](模块介绍.md)
- 参考：[客户端同步-gRPC-通信](客户端同步.md#grpc-通信)
- 参考：[服务端推送-gRPC-连接](服务端推送.md#gRPC-连接)


## Proto-定义
- `nacos_grpc_service.proto`
```js
syntax = "proto3";              // 使用 V3 版本
option java_package = "com.alibaba.nacos.api.grpc.auto";

message Metadata {
  string type = 3;
  string clientIp = 8;
  map<string, string> headers = 7;
}

message Payload {
  Metadata metadata = 2;
  google.protobuf.Any body = 3; // byte[] (byte 数组)
}

service Request {
  // sign_rm_110 定义 gRPC 服务接口 (通用请求)
  rpc request (Payload) returns (Payload) {
  }
}

service BiRequestStream {
  // sign_rm_120 定义 gRPC 服务接口 (入参、出参都是 stream 声明，相当于双向通信)
  rpc requestBiStream (stream Payload) returns (stream Payload) {
  }
}
```

- `BiRequestStream` 实现类为 `com.alibaba.nacos.core.remote.grpc.GrpcBiStreamRequestAcceptor`
  - ref: `sign_c_210`


## gRPC-服务-启动
- 参考：
  - [模块介绍-Maven-依赖关系](模块介绍.md#Maven-依赖关系)
  - [控制台启动-入口 sign_c_010](控制台启动.md#入口)

### 启动服务
- `com.alibaba.nacos.core.remote.grpc.GrpcSdkServer`
```java
// sign_c_010
@Service    // 跟随 Nacos 控制台启动，参考：[控制台启动-入口 sign_c_010]
public class GrpcSdkServer extends BaseGrpcServer {         // ref: sign_c_020
}
```

- `com.alibaba.nacos.core.remote.grpc.BaseGrpcServer`
```java
// sign_c_020
public abstract class BaseGrpcServer extends BaseRpcServer {    // ref: sign_c_030

    private Server server;  // gRPC 服务类：io.grpc.Server
    
    @Autowired
    private GrpcRequestAcceptor grpcCommonRequestAcceptor;  // gRPC 服务接口实现, ref: sign_rm_110
    @Autowired
    private GrpcBiStreamRequestAcceptor grpcBiStreamRequestAcceptor;    // gRPC 服务接口实现, ref: sign_rm_120

    // sign_m_021 重写服务启动的钩子函数, ref: sign_m_032
    // 调用入口参考： sign_m_031
    @Override
    public void startServer() throws Exception {
        final MutableHandlerRegistry handlerRegistry = new MutableHandlerRegistry();
        addServices(handlerRegistry, new GrpcConnectionInterceptor());  // 注册服务, ref: sign_m_022
        NettyServerBuilder builder = NettyServerBuilder.forPort(getServicePort()).executor(getRpcExecutor());

        ...

        // 构建 gRPC 服务
        server = builder.maxInboundMessageSize(getMaxInboundMessageSize()).fallbackHandlerRegistry(handlerRegistry)
                ... // KeepAliveTime / KeepAliveTimeout / PermitKeepAliveTime
                .build();

        server.start(); // 启动 gRPC 服务监听
    }

    // sign_m_022 注册服务
    private void addServices(MutableHandlerRegistry handlerRegistry, ServerInterceptor... serverInterceptor) {
        ...

        final ServerCallHandler<Payload, Payload> payloadHandler = ServerCalls
                .asyncUnaryCall((request, responseObserver) -> grpcCommonRequestAcceptor.request(request, responseObserver));

        ...
        // 注册
        handlerRegistry.addService(ServerInterceptors.intercept(serviceDefOfUnaryPayload, serverInterceptor));

        final ServerCallHandler<Payload, Payload> biStreamHandler = ServerCalls.asyncBidiStreamingCall(
                (responseObserver) -> grpcBiStreamRequestAcceptor.requestBiStream(responseObserver));

        ...
        // 注册
        handlerRegistry.addService(ServerInterceptors.intercept(serviceDefOfBiStream, serverInterceptor));
    }
}
```

- `com.alibaba.nacos.core.remote.BaseRpcServer`
```java
// sign_c_030
public abstract class BaseRpcServer {

    // sign_m_031  Spring 钩子函数
    @PostConstruct
    public void start() throws Exception {
        ...

        startServer();  // 子类实现, ref: sign_m_032
    
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            try {
                BaseRpcServer.this.stopServer();    // ref: sign_m_033
            } ... // catch
        }));
    }

    // sign_m_032 服务启动的钩子函数
    public abstract void startServer() throws Exception;

    // sign_m_033
    public final void stopServer() throws Exception {
        shutdownServer();   // 子类实现, ref: sign_m_034
    }

    // sign_m_034 停服务的钩子函数
    @PreDestroy
    public abstract void shutdownServer();
}
```


## gRPC-服务实现
- `com.alibaba.nacos.core.remote.grpc.GrpcBiStreamRequestAcceptor`
  - [服务端推送-gRPC-通知器 sign_m_301](服务端推送.md#gRPC-通知器)
```java
// sign_c_210 服务实现类
@Service
public class GrpcBiStreamRequestAcceptor extends BiRequestStreamGrpc.BiRequestStreamImplBase {

    // sign_m_210  gRPC-服务接口实现。接口定义参考： sign_rm_120
    @Override
    public StreamObserver<Payload> requestBiStream(StreamObserver<Payload> responseObserver) {
        
        StreamObserver<Payload> streamObserver = new StreamObserver<Payload>() {
            
            final String connectionId = GrpcServerConstants.CONTEXT_KEY_CONN_ID.get();
            final Integer localPort = GrpcServerConstants.CONTEXT_KEY_CONN_LOCAL_PORT.get();
            final int remotePort = GrpcServerConstants.CONTEXT_KEY_CONN_REMOTE_PORT.get();
            String remoteIp = GrpcServerConstants.CONTEXT_KEY_CONN_REMOTE_IP.get();
            String clientIp = "";
            
            @Override
            public void onNext(Payload payload) {
                
                clientIp = payload.getMetadata().getClientIp();
                traceDetailIfNecessary(payload);
                
                Object parseObj;
                try {
                    parseObj = GrpcUtils.parse(payload);
                } ... // catch ... return;
                
                ... // parseObj == null ... return;

                if (parseObj instanceof ConnectionSetupRequest) {
                    ConnectionSetupRequest setUpRequest = (ConnectionSetupRequest) parseObj;
                    Map<String, String> labels = setUpRequest.getLabels();
                    ...
                    
                    ConnectionMeta metaInfo = new ConnectionMeta(...);
                    metaInfo.setTenant(setUpRequest.getTenant());

                    // 创建 gRPC 连接
                    // 类全称： com.alibaba.nacos.core.remote.grpc.GrpcConnection
                    // ref: sign_c_310 | sign_cm_310
                    Connection connection = new GrpcConnection(metaInfo, responseObserver, GrpcServerConstants.CONTEXT_KEY_CHANNEL.get());
                    connection.setAbilities(setUpRequest.getAbilities());
                    boolean rejectSdkOnStarting = metaInfo.isSdkSource() && !ApplicationUtils.isStarted();
                    
                    // sign_cb_301  connectionManager.register -> 注册连接，ref: [服务端推送-gRPC-通知器 sign_m_301]
                    if (rejectSdkOnStarting || !connectionManager.register(connectionId, connection)) {
                        // 如果当前服务器正在启动或注册失败，则关闭。
                        try {
                            connection.request(new ConnectResetRequest(), 3000L);   // 重置连接
                            connection.close();
                        } ... // catch ... log
                    }
                } else if (parseObj instanceof Response) {
                    ...
                } ... // else 仅日志打印
            }
            
            @Override
            public void onError(Throwable t) {
                ...
                responseObserver.onCompleted();
                ...
            }
            
            @Override
            public void onCompleted() {
                ...
                responseObserver.onCompleted();
                ...
            }
        };
        
        return streamObserver;
    }
}
```

## gRPC-连接
- `com.alibaba.nacos.core.remote.grpc.GrpcConnection`
  - 异步请求-调用方参考：[服务端推送-gRPC-通知器 sign_m_290](服务端推送.md#gRPC-通知器)
```java
// sign_c_310  gRPC-连接
public class GrpcConnection extends Connection {

    private StreamObserver streamObserver;  // 相当于响应流
    private Channel channel;                // 相当于连接通道
    
    // sign_cm_310
    public GrpcConnection(ConnectionMeta metaInfo, StreamObserver streamObserver, Channel channel) {
        super(metaInfo);
        this.streamObserver = streamObserver;
        this.channel = channel;
    }

    // sign_m_310 异步请求。调用方参考：[服务端推送-gRPC-通知器 sign_m_290](服务端推送.md#gRPC-通知器)
    @Override
    public void asyncRequest(Request request, RequestCallBack requestCallBack) throws NacosException {
        sendRequestInner(request, requestCallBack); // 发送请求, ref: sign_m_311
    }

    // sign_m_311 发送请求
    private DefaultRequestFuture sendRequestInner(Request request, RequestCallBack callBack) throws NacosException {
        final String requestId = String.valueOf(PushAckIdGenerator.getNextId());
        request.setRequestId(requestId);
        
        DefaultRequestFuture defaultPushFuture = ... // 设置回调

        sendRequestNoAck(request);  // gRPC 发送请求, ref: sign_m_312
        return defaultPushFuture;
    }

    // sign_m_312 gRPC 发送请求
    private void sendRequestNoAck(Request request) throws NacosException {
        try {
            // StreamObserver #onNext() 不是线程安全的，需要同步以避免直接内存泄漏
            synchronized (streamObserver) {
                Payload payload = GrpcUtils.convert(request);
                traceIfNecessary(payload);
                streamObserver.onNext(payload); // gRPC 响应 client，接口定义参考： sign_rm_120
            }
        } ... // catch
    }
}
```