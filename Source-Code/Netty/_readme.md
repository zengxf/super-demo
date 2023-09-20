## 总说明
- 源码仓库： https://github.com/netty/netty
- 克隆：`git clone https://github.com/netty/netty.git`
- 切分支（tag）：`git checkout 4.1`
- JDK: `1.8`


### 项目配置
- 改项目根 `pom.xml` 文件
```xml
  <!-- <project> 的直接子节点 -->
  <properties>
    <!-- 改成 1.8 -->
    <maven.compiler.source>1.8</maven.compiler.source>
    <maven.compiler.target>1.8</maven.compiler.target>
    <!-- 其他不变 -->
  </properties>
```

- 改 IDEA Maven 配置
  - **Maven home path**: 选择 `Bundled (Maven 3)`


### 专业词翻译
- `Bootstrap` 引导器
- `Selector` 选择器
- `Channel` 信道
- `Pipeline` 流水线
- `Outbound` 出站
- `EventLoop` 事件轮循 (事件轮循者)
- `Future` 异步结果


### 阅读顺序
1. [简单示例](简单示例.md)
2. [基础类介绍](基础类介绍.md)
    1. [异步工具类](异步工具类.md)
3. [ServerBootstrap-监听](ServerBootstrap-监听.md)
    1. [选择器-监听](选择器-监听.md)
    2. [读写原理](读写原理.md)


### 原理分解
- 处理器链
- 处理器回调函数逻辑
- @Skip-原理