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


## 客户端
- 参考：[客户端更新-gRPC-通信](客户端更新.md#grpc-通信)


## gRPC-服务-启动
com.alibaba.nacos.core.remote.grpc.BaseGrpcServer
com.alibaba.nacos.core.remote.grpc.BaseGrpcServer#startServer
com.alibaba.nacos.core.remote.grpc.GrpcSdkServer