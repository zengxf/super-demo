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

    // HC5 配置
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

    // 熔断器配置
    @Configuration(proxyBeanMethods = false)
    ...
    protected static class CircuitBreakerPresentFeignTargeterConfiguration {
        ...
    }
}
```

- `org.springframework.cloud.openfeign.loadbalancer.FeignLoadBalancerAutoConfiguration`
```java
// sign_c_110  负载均衡配置
...
@AutoConfigureBefore(FeignAutoConfiguration.class) // 先于"常规配置"，ref: sign_c_100
@Import({ // 导入 HC5 等基础配置
    OkHttpFeignLoadBalancerConfiguration.class, HttpClient5FeignLoadBalancerConfiguration.class, // ref: sign_c_120
    Http2ClientFeignLoadBalancerConfiguration.class, DefaultFeignLoadBalancerConfiguration.class 
})
public class FeignLoadBalancerAutoConfiguration {
    ...
}
```

- `org.springframework.cloud.openfeign.loadbalancer.HttpClient5FeignLoadBalancerConfiguration`
```java
// sign_c_120  HC5 负载均衡配置
@Configuration(proxyBeanMethods = false)
...
@Import(HttpClient5FeignConfiguration.class) // 导入 HC5 的配置
class HttpClient5FeignLoadBalancerConfiguration {

    @Bean
    ...
    public Client feignClient(LoadBalancerClient loadBalancerClient, HttpClient httpClient5, ...) {
        Client delegate = new ApacheHttp5Client(httpClient5);
        return new FeignBlockingLoadBalancerClient(delegate, loadBalancerClient, ...); // ref: sign_c_200
    }
}
```

### 负载均衡
- `org.springframework.cloud.openfeign.loadbalancer.FeignBlockingLoadBalancerClient`
```java
// sign_c_200  负载均衡客户端
public class FeignBlockingLoadBalancerClient implements Client {
    private final Client delegate;
    private final LoadBalancerClient loadBalancerClient;

    @Override
    public Response execute(Request request, Request.Options options) throws IOException {
        final URI originalUri = URI.create(request.url());
        String serviceId = originalUri.getHost();
        ...
        ServiceInstance instance = loadBalancerClient.choose(serviceId, lbRequest); // 筛选出服务实例
        ... // 服务实例为空处理：直接响应 503 错误码
        String reconstructedUrl = loadBalancerClient.reconstructURI(instance, originalUri).toString();
        Request newRequest = buildRequest(request, reconstructedUrl, instance); // 构建新请求
        return executeWithLoadBalancerLifecycleProcessing(delegate, options, newRequest, ...); // 执行请求，ref: sign_m_210
    }
}
```

- `org.springframework.cloud.openfeign.loadbalancer.LoadBalancerUtils`
```java
final class LoadBalancerUtils {
    // sign_m_210  执行请求
    static Response executeWithLoadBalancerLifecycleProcessing(Client feignClient, ...) throws IOException {
        return executeWithLoadBalancerLifecycleProcessing(feignClient, ..., true);
    }

    // sign_m_211
    static Response executeWithLoadBalancerLifecycleProcessing(Client feignClient, ..., boolean loadBalanced) throws IOException {
        ...
        try {
            Response response = feignClient.execute(feignRequest, options); // 底层执行请求
            ...
            return response;
        }
        ... // catch
    }
}
```