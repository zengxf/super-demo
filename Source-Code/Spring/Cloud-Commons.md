## 使用示例
- 服务注册与发现：https://github.com/zengxf/spring-demo/tree/master/cloud-demo/ali-nacos/naming-test-1
- 依赖：
  - `spring-cloud-starter-alibaba-nacos-discovery`
    - `spring-cloud-commons`
    - `spring-cloud-context`


## 原理
### spring-cloud-context
- 自动配置导入
  - `../../*.AutoConfiguration.imports`
    ```js
    *.ConfigurationPropertiesRebinderAutoConfiguration // 环境改变
    *.LifecycleMvcEndpointAutoConfiguration // 环境更新
    *.RefreshAutoConfiguration // 刷新配置
    ...
    ```
  - `../../spring.factories`
    ```js
    org.springframework.context.ApplicationListener=\
    org.springframework.cloud.bootstrap.BootstrapApplicationListener,\ // 读取 bootstrap.properties 配置
    ...
    ```