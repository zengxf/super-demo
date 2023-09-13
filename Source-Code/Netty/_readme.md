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


### 原理分解
- ServerBootstrap 监听
- 读写底层原理
- 处理器链
- 处理器回调函数逻辑
- @Skip 跳过原理