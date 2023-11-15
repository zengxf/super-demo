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


### 编译报错
- ref: https://blog.csdn.net/ibigboy/article/details/119413998
```js
// 执行 MVN 编译，生成 protobuf 类
mvn compile

// 然后可以再重新启动，编译就没问题了
```


### 启动出错
- ref: https://github.com/alibaba/nacos/issues/2902
```java
// 代码设置
System.setProperty("nacos.standalone", "true");

// JVM: -Dnacos.standalone=true
```


### 内容
- [xx](xx.md)