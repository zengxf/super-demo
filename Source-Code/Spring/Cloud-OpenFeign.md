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

    // 初始化工厂，ref: sign_c_140
    // 相当于创建分层 Context；
    // 并导入 FeignClientsConfiguration 配置类，ref: sign_c_130
    @Bean
    public FeignClientFactory feignContext() {
        FeignClientFactory context = new FeignClientFactory(); // ref: sign_cm_140
        context.setConfigurations(this.configurations);
        return context;
    }

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
    @ConditionalOnClass(CircuitBreaker.class) // 要有熔断器类
    @ConditionalOnProperty(value = "spring.cloud.openfeign.circuitbreaker.enabled", havingValue = "true") // 且启用
    protected static class CircuitBreakerPresentFeignTargeterConfiguration {
        @Bean
        @ConditionalOnMissingBean(CircuitBreakerFactory.class) // 没有此实例用默认的处理
        public Targeter defaultFeignTargeter() {
            return new DefaultTargeter(); // 默认什么都不做，只是转用
        }

        @Bean
        @ConditionalOnMissingBean // 上面的默认没生效
        @ConditionalOnBean(CircuitBreakerFactory.class) // 且有此实例 (引入 spring-cloud-circuitbreaker-sentinel 模块就会有此实例)
        public Targeter circuitBreakerFeignTargeter(CircuitBreakerFactory circuitBreakerFactory, ...) {
            return new FeignCircuitBreakerTargeter(circuitBreakerFactory, ...); // 创建熔断处理实例，ref: sign_c_300
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

- `org.springframework.cloud.openfeign.FeignClientsConfiguration`
```java
// sign_c_130  客户端配置
@Configuration(proxyBeanMethods = false)
public class FeignClientsConfiguration {

    // 熔断回退配置
    @Configuration(proxyBeanMethods = false)
    ...
    protected static class CircuitBreakerPresentFeignBuilderConfiguration {

        @Bean
        ...
        public Feign.Builder circuitBreakerFeignBuilder() {
            return FeignCircuitBreaker.builder(); // 创建 Builder, ref: sign_c_310 | sign_m_310
        }
    }
}
```

- `org.springframework.cloud.openfeign.FeignClientFactory`
  - 参考：[Spring-Cloud-Commons-分层-Context sign_c_240 | sign_m_2404](Cloud-Commons.md#分层-Context)
```java
// sign_c_140  
public class FeignClientFactory extends NamedContextFactory<FeignClientSpecification> {

    // sign_cm_140
    public FeignClientFactory() {
        this(new HashMap<>());  // ref: sign_cm_141
    }

    // sign_cm_141
    public FeignClientFactory(
        Map<String, ApplicationContextInitializer<GenericApplicationContext>> applicationContextInitializers
    ) {
        super( // 参考：[Spring-Cloud-Commons-分层-Context sign_c_240 | sign_m_2404]
            FeignClientsConfiguration.class, // 要导入的配置类，ref: sign_c_130
            ..., applicationContextInitializers
        );
    }
}
```

### 创建-Feign-Bean
- `org.springframework.cloud.openfeign.EnableFeignClients`
```java
// sign_c_500  启用 Feign 注解
...
@Import(FeignClientsRegistrar.class) // ref: sign_c_510
public @interface EnableFeignClients {
}
```

- `org.springframework.cloud.openfeign.FeignClientsRegistrar`
```java
// sign_c_510
class FeignClientsRegistrar implements ImportBeanDefinitionRegistrar, ResourceLoaderAware, EnvironmentAware {

    @Override
    public void registerBeanDefinitions(AnnotationMetadata metadata, BeanDefinitionRegistry registry) {
        registerDefaultConfiguration(metadata, registry);
        registerFeignClients(metadata, registry);
    }

    public void registerFeignClients(AnnotationMetadata metadata, BeanDefinitionRegistry registry) {
        ...

        for (BeanDefinition candidateComponent : candidateComponents) {
            if (candidateComponent instanceof AnnotatedBeanDefinition beanDefinition) {
                ...

                // 读取 @FeignClient 注解
                Map<String, Object> attributes = annotationMetadata
                        .getAnnotationAttributes(FeignClient.class.getCanonicalName());

                ...
                registerFeignClient(registry, annotationMetadata, attributes);
            }
        }
    }

    private void registerFeignClient(BeanDefinitionRegistry registry, ..., Map<String, Object> attributes) {
        String className = annotationMetadata.getClassName();
        if (...) { ... } // 非懒加载处理
        else {
            // 懒加载处理
            lazilyRegisterFeignClientBeanDefinition(className, attributes, registry);
        }
    }

    private void lazilyRegisterFeignClientBeanDefinition(String className, Map<String, Object> attributes, BeanDefinitionRegistry registry) {
        ConfigurableBeanFactory beanFactory = registry instanceof ConfigurableBeanFactory ...;
        Class clazz = ClassUtils.resolveClassName(className, null);
        ...
        FeignClientFactoryBean factoryBean = new FeignClientFactoryBean(); // 创建工厂 Bean
        ...
        factoryBean.setType(clazz);
        BeanDefinitionBuilder definition = BeanDefinitionBuilder.genericBeanDefinition(clazz, () -> {
            ...
            Object fallback = attributes.get("fallback");
            if (fallback != null) {
                factoryBean.setFallback(fallback ...); // 设置回退
            }
            Object fallbackFactory = attributes.get("fallbackFactory");
            if (fallbackFactory != null) {
                factoryBean.setFallbackFactory(fallbackFactory ...); // 设置回退工厂
            }
            return factoryBean.getObject();
        });

        ...
        AbstractBeanDefinition beanDefinition = definition.getBeanDefinition(); // 获取 Bean 定义
        
        ...
        BeanDefinitionHolder holder = new BeanDefinitionHolder(beanDefinition, className, qualifiers);
        BeanDefinitionReaderUtils.registerBeanDefinition(holder, registry);     // 注册 Bean
        ...
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

### 熔断与回退
- `org.springframework.cloud.openfeign.FeignCircuitBreakerTargeter`
```java
// sign_c_300  熔断回退代理创建器
class FeignCircuitBreakerTargeter implements Targeter {
    private final CircuitBreakerFactory circuitBreakerFactory;

    // sign_m_300
    @Override // 在 FeignClientFactoryBean 里面调用
    public <T> T target(FeignClientFactoryBean factory, Feign.Builder feign, FeignClientFactory context,
            Target.HardCodedTarget<T> target) {
        ...
        String name = !StringUtils.hasText(factory.getContextId()) ? factory.getName() : factory.getContextId();
        Class<?> fallback = factory.getFallback();
        if (fallback != void.class) {
            return targetWithFallback(name, context, target, builder, fallback); // ref: sign_m_301
        }
        ...
    }

    // sign_m_301  生成熔断回退代理对象
    private <T> T targetWithFallback(String feignClientName, FeignClientFactory context, ...) {
        T fallbackInstance = getFromContext("fallback", feignClientName, ...); // 获取回退处理实例
        return builder(feignClientName, builder)    // 填充 Builder，ref: sign_m_302
            .target(target, fallbackInstance);      // 创建代理，ref: sign_m_311
    }

    // sign_m_302  填充 Builder
    private FeignCircuitBreaker.Builder builder(String feignClientName, FeignCircuitBreaker.Builder builder) {
        return builder.circuitBreakerFactory(circuitBreakerFactory) ...;
    }
}
```

- `org.springframework.cloud.openfeign.FeignCircuitBreaker`
```java
// sign_c_310  熔断回退代理 Builder
public final class FeignCircuitBreaker {

    // sign_m_310  创建 Builder
    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder extends Feign.Builder {

        // sign_m_311  创建代理
        public <T> T target(Target<T> target, T fallback) {
            return build(... new FallbackFactory.Default<>(fallback) ...) // ref: sign_m_312
                .newInstance(target); // 创建代理
        }

        // sign_m_312  设置熔断回退处理
        public Feign build(final FallbackFactory<?> nullableFallbackFactory) {
            super.invocationHandlerFactory((target, dispatch) -> 
                new FeignCircuitBreakerInvocationHandler(...)
            );
            return super.build();
        }

    }
}
```