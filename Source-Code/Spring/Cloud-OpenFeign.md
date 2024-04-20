# Spring-Cloud-OpenFeign


## 使用示例
- 服务注册与发现：https://github.com/zengxf/spring-demo/tree/master/cloud-demo/ali-nacos/naming-test-1
- 依赖：
  - `spring-cloud-starter-openfeign`
    - `spring-cloud-openfeign-core`


## 原理
### 配置导入
- `./META-INF/spring/*.AutoConfiguration.imports`
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
  - 一般会使用 `@EnableFeignClients` 进行启用 Feign
```java
// sign_c_500  启用 Feign 注解
...
@Import(FeignClientsRegistrar.class) // 导入注册器，ref: sign_c_510 | sign_m_510
public @interface EnableFeignClients {
}
```

- `org.springframework.cloud.openfeign.FeignClientsRegistrar`
```java
// sign_c_510  Feign 注册器
class FeignClientsRegistrar implements ImportBeanDefinitionRegistrar, ResourceLoaderAware, EnvironmentAware {

    // sign_m_510  注册 Bean 定义
    @Override
    public void registerBeanDefinitions(AnnotationMetadata metadata, BeanDefinitionRegistry registry) {
        registerDefaultConfiguration(metadata, registry);
        registerFeignClients(metadata, registry); // ref: sign_m_511
    }

    // sign_m_511  注册带 @FeignClient 注解的接口
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

    // sign_m_512  注册 FeignClient
    private void registerFeignClient(BeanDefinitionRegistry registry, ..., Map<String, Object> attributes) {
        String className = annotationMetadata.getClassName();
        if (...) { ... } // 非懒加载处理
        else {
            // 注册懒加载式 Bean 定义，ref: sign_m_513
            lazilyRegisterFeignClientBeanDefinition(className, attributes, registry);
        }
    }

    // sign_m_513  注册懒加载式 Bean 定义
    private void lazilyRegisterFeignClientBeanDefinition(String className, Map<String, Object> attributes, BeanDefinitionRegistry registry) {
        ConfigurableBeanFactory beanFactory = registry instanceof ConfigurableBeanFactory ...;
        Class clazz = ClassUtils.resolveClassName(className, null);
        ...
        FeignClientFactoryBean factoryBean = new FeignClientFactoryBean(); // 创建工厂 Bean, ref: sign_c_520
        ...
        factoryBean.setType(clazz);
        BeanDefinitionBuilder definition = BeanDefinitionBuilder.genericBeanDefinition(clazz, // 创建 Bean 定义构造者
            // Bean 提供者
            () -> {
                ...
                Object fallback = attributes.get("fallback");
                if (fallback != null) {
                    factoryBean.setFallback(fallback ...); // 设置回退
                }
                Object fallbackFactory = attributes.get("fallbackFactory");
                if (fallbackFactory != null) {
                    factoryBean.setFallbackFactory(fallbackFactory ...); // 设置回退工厂
                }
                return factoryBean.getObject(); // 创建 Bean, ref: sign_m_520
            }
        );

        ...
        AbstractBeanDefinition beanDefinition = definition.getBeanDefinition(); // 构造 Bean 定义
        
        ...
        BeanDefinitionHolder holder = new BeanDefinitionHolder(beanDefinition, className, qualifiers);
        BeanDefinitionReaderUtils.registerBeanDefinition(holder, registry);     // 注册 Bean 定义
        ...
    }
}
```

- `org.springframework.cloud.openfeign.FeignClientFactoryBean`
```java
// sign_c_520  Feign 工厂 Bean
public class FeignClientFactoryBean
        implements FactoryBean<Object>, InitializingBean, ApplicationContextAware, BeanFactoryAware 
{
    // sign_m_520  创建 Bean 实例
    @Override
    public Object getObject() {
        return getTarget(); // ref: sign_m_521
    }

    // sign_m_521  创建代理对象
    <T> T getTarget() {
        FeignClientFactory feignClientFactory = ... applicationContext.getBean(FeignClientFactory.class);
        Feign.Builder builder = feign(feignClientFactory); // 获取构造者
        if (!StringUtils.hasText(url) && !isUrlAvailableInConfig(contextId)) {
            ...
            if (!name.startsWith("http://") && !name.startsWith("https://")) {
                url = "http://" + name;
            }
            ...
            url += cleanPath();
            return (T) loadBalance(builder, feignClientFactory, ...); // ref: sign_m_522
        }
        ...
    }

    // sign_m_522
    protected <T> T loadBalance(Feign.Builder builder, FeignClientFactory context, HardCodedTarget<T> target) {
        Client client = getOptional(context, Client.class);
        if (client != null) {
            builder.client(client);
            applyBuildCustomizers(context, builder);
            Targeter targeter = get(context, Targeter.class);
            return targeter.target(this, builder, context, target); // 创建代理对象，ref: sign_m_300
        }
        ... // throw
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

    // sign_m_300  创建代理对象
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
                new FeignCircuitBreakerInvocationHandler(...) // JDK 代理处理器，ref: sign_c_320
            );
            return super.build();
        }

    }
}
```

- `org.springframework.cloud.openfeign.FeignCircuitBreakerInvocationHandler`
  - 可参考：[Ali-Sentinel-熔断](../Ali/Spring-Cloud-Alibaba/熔断.md)
```java
// sign_c_320  JDK 代理处理器
class FeignCircuitBreakerInvocationHandler implements InvocationHandler {
    
    private final CircuitBreakerFactory factory;
    private final Target<?> target;
    private final Map<Method, InvocationHandlerFactory.MethodHandler> dispatch;

    // sign_m_320  JDK 代理处理逻辑
    @Override
    public Object invoke(final Object proxy, final Method method, final Object[] args) {
        ... // equals hashCode toString 三方法的处理

        String circuitName = circuitBreakerNameResolver.resolveCircuitBreakerName(feignClientName, target, method);
        CircuitBreaker circuitBreaker = ... factory.create(circuitName); // sign_cb_320  通过工厂创建熔断器
        Supplier<Object> supplier = asSupplier(method, args); // 方法调用提供者，ref: sign_m_321
        if (this.nullableFallbackFactory != null) {
            Function<Throwable, Object> fallbackFunction = throwable -> { ... };
            return circuitBreaker.run(supplier, fallbackFunction); // 带回退的熔断运行
        }
        return circuitBreaker.run(supplier); // 熔断运行。可参考：[Ali-Sentinel-熔断]
    }

    // sign_m_321  相当于提供一个方法调用实现
    private Supplier<Object> asSupplier(final Method method, final Object[] args) {
        final RequestAttributes requestAttributes = RequestContextHolder.getRequestAttributes();
        ...
        return () -> {
            ...
            try {
                ...
                return dispatch.get(method)     // 获取目标方法处理器 MethodHandler
                               .invoke(args);   // 进行调用
            }
            ... // catch finally
        };
    }
}
```

### 总结
- 熔断回退使用 `FeignCircuitBreakerInvocationHandler` JDK 动态代理实现
- 负载均衡使用 `FeignBlockingLoadBalancerClient` 委派底层客户端实现
- 调用顺序是：
  - `熔断回退 -> 负载均衡 -> 底层客户端 (HC5) -> HTTP -> 远程服务`
- 初始化 Bean 顺序是：
  - `负载均衡 -> (传给) -> 熔断回退 -> (组装) -> Builder -> (构建) -> instance`