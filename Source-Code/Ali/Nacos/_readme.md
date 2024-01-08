## Nacos
- 源码仓库： https://github.com/alibaba/nacos
- 克隆：`git clone https://github.com/alibaba/nacos.git`
- 切分支：
  ```js
  // 从 Tag 2.2.4 创建分支并切换
  git branch my-study 2.2.4
  git checkout my-study
  ```
- JDK: `17`


### 内容
- [模块介绍](模块介绍.md)
- [控制台启动](控制台启动.md)
  - [启动流程](启动流程.md)
- [新增或更改配置](新增配置.md)
  - [事件通知](事件通知.md)
  - [同步 gRPC 通信](同步-gRPC.md)
  - [客户端同步](客户端同步.md)
  - [服务端推送](服务端推送.md)
- [服务注册和发现](服务注册.md)