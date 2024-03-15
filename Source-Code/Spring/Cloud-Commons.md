- Spring-Cloud-Commons


## 使用示例
- 服务注册与发现：https://github.com/zengxf/spring-demo/tree/master/cloud-demo/ali-nacos/naming-test-1
- 依赖：
  - `spring-cloud-starter-alibaba-nacos-discovery`
    - `spring-cloud-context`
    - `spring-cloud-commons`


## 原理
### spring-cloud-context
#### 自动配置导入
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

#### 新 Context 刷新
- TODO


### spring-cloud-commons
#### 自动配置导入
- `../../*.AutoConfiguration.imports`
  ```js
  *.client.CommonsClientAutoConfiguration // 阻塞式-服务发现
  *.client.ReactiveCommonsClientAutoConfiguration // 响应式-服务发现
  ...
  *.client.loadbalancer.LoadBalancerAutoConfiguration // 负载平衡
  ...
  *.client.serviceregistry.ServiceRegistryAutoConfiguration // 服务注册 Endpoint
  ...
  *.configuration.CompatibilityVerifierAutoConfiguration // Boot 版本校验
  *.client.serviceregistry.AutoServiceRegistrationAutoConfiguration // 自动注册校验
  ...
  ```
  - **熔断器无配置**
