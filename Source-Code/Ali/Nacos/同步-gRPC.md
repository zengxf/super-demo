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

- 实现类为 `com.alibaba.nacos.core.remote.grpc.GrpcBiStreamRequestAcceptor`


## gRPC-服务-启动
- 参考：
  - [模块介绍-Maven-依赖关系](模块介绍.md#Maven-依赖关系)
  - [控制台启动-入口](控制台启动.md#入口)

### 启动服务
- `com.alibaba.nacos.core.remote.grpc.GrpcSdkServer`
```java
// sign_c_010
@Service    // 跟随 Nacos 控制台启动
public class GrpcSdkServer extends BaseGrpcServer {         // ref: sign_c_020
}
```

- `com.alibaba.nacos.core.remote.grpc.BaseGrpcServer`
```java
// sign_c_020
public abstract class BaseGrpcServer extends BaseRpcServer {    // ref: sign_c_030

    private Server server;  // gRPC 服务类：io.grpc.Server

    // sign_m_021 重写服务启动的钩子函数, ref: sign_m_032
    @Override
    public void startServer() throws Exception {
        ...
        NettyServerBuilder builder = NettyServerBuilder.forPort(getServicePort()).executor(getRpcExecutor());

        ...

        server = builder.maxInboundMessageSize(getMaxInboundMessageSize()).fallbackHandlerRegistry(handlerRegistry)
                ... // KeepAliveTime / KeepAliveTimeout / PermitKeepAliveTime
                .build();

        server.start(); // 启动 gRPC 服务监听
    }

}
```

- `com.alibaba.nacos.core.remote.BaseRpcServer`
```java
// sign_c_030
public abstract class BaseRpcServer {

    // sign_m_031
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