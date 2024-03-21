## Spring
### 总说明
- **Spring-Framework**
  - 源码仓库： https://github.com/spring-projects/spring-framework
  - 克隆：`git clone https://github.com/spring-projects/spring-framework.git`
  - 切分支：`git checkout 6.0.x`
- **Spring-Boot**
  - 源码仓库： https://github.com/spring-projects/spring-boot
  - 克隆：`git clone https://github.com/spring-projects/spring-boot.git`
  - 切分支：`git checkout 3.1.x`
- **Spring-Cloud-Commons**
  - 源码仓库： https://github.com/spring-cloud/spring-cloud-commons
  - 克隆：`git clone https://github.com/spring-cloud/spring-cloud-commons.git`
  - 切分支：
    ```js
    git branch my-study v4.1.1
    git checkout my-study
    ```
- JDK: `17`


### UML
- Context-UML: https://www.processon.com/view/link/648532c4320a4e3425972722
- BeanFactory-UML: https://www.processon.com/view/link/648b3146516ce3025f4e850d


### 内容
- Spring
  - [Context-刷新原理](Context-刷新原理.md)
  - [Bean-实例化原理](Bean-实例化原理.md)
  - [AOP-原理](AOP-原理.md)
    - [Cache-原理](Cache-原理.md)
    - [Transaction-原理](Transaction-原理.md)
  - [Configuration-加载原理](Configuration-加载原理.md)
    - [Ann-注解测试](Ann-注解测试.md)
    - [Import-原理](Import-原理.md)
- Spring-Boot
  - [Spring-Boot-加载原理](Boot-加载原理.md)
  - [Spring-Boot-基础类](Boot-基础类.md)
- Spring-Cloud
  - [Spring-Cloud-Commons](Cloud-Commons.md)