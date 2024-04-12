# Spring-Cloud-OpenFeign


## 使用示例
- 服务注册与发现：https://github.com/zengxf/spring-demo/tree/master/cloud-demo/ali-nacos/naming-test-1
- 依赖：
  - `spring-cloud-starter-openfeign`
    - `spring-cloud-openfeign-core`


## 原理
### 自动配置导入
- `../../*.AutoConfiguration.imports`
  ```js
  ...
  *.openfeign.FeignAutoConfiguration // 常规配置，ref: sign_c_100
  *.openfeign.encoding.FeignAcceptGzipEncodingAutoConfiguration
  ...
  *.openfeign.loadbalancer.FeignLoadBalancerAutoConfiguration // 负载均衡配置，ref: sign_c_110
  ```

### 自动配置
- `org.springframework.cloud.openfeign.FeignAutoConfiguration`
```java
// sign_c_100  常规配置
@Configuration(proxyBeanMethods = false)
...
public class FeignAutoConfiguration {

    @Configuration(proxyBeanMethods = false)
    @ConditionalOnClass(ApacheHttp5Client.class)
    @ConditionalOnMissingBean(org.apache.hc.client5.http.impl.classic.CloseableHttpClient.class)  // 防止重复
    ...
    @Import(org.springframework.cloud.openfeign.clientconfig.HttpClient5FeignConfiguration.class) // 导入 HC5 的配置
    protected static class HttpClient5FeignConfiguration {

        @Bean
        @ConditionalOnMissingBean(Client.class) // 没有 Client 实例时，才创建
        public Client feignClient(org.apache.hc.client5.http.impl.classic.CloseableHttpClient httpClient5) {
            return new ApacheHttp5Client(httpClient5);
        }
    }
}
```

- `org.springframework.cloud.openfeign.loadbalancer.FeignLoadBalancerAutoConfiguration`
```java
// sign_c_110  负载均衡配置
...
@AutoConfigureBefore(FeignAutoConfiguration.class) // 先于"常规配置"，ref: sign_c_100
@Import({ // 导入 HC5 等基础配置
    OkHttpFeignLoadBalancerConfiguration.class, HttpClient5FeignLoadBalancerConfiguration.class,
    Http2ClientFeignLoadBalancerConfiguration.class, DefaultFeignLoadBalancerConfiguration.class 
})
public class FeignLoadBalancerAutoConfiguration {

    @Bean
    @ConditionalOnBean(LoadBalancerClientFactory.class)
    @ConditionalOnMissingBean(XForwardedHeadersTransformer.class)
    public XForwardedHeadersTransformer xForwarderHeadersFeignTransformer(LoadBalancerClientFactory factory) {
        return new XForwardedHeadersTransformer(factory);
    }

}
```