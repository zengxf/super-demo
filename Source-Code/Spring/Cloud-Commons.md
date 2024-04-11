# Spring-Cloud-Commons


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
- 单元测试参考：
  - `org.springframework.cloud.bootstrap.BootstrapSourcesOrderingTests`

- `org.springframework.cloud.bootstrap.BootstrapApplicationListener`
  - 参考：[Boot-基础类-ConfigData ConfigDataLocationResolver](Boot-基础类.md#ConfigData)
```java
public class BootstrapApplicationListener implements ApplicationListener<ApplicationEnvironmentPreparedEvent>, Ordered {
    @Override
    public void onApplicationEvent(ApplicationEnvironmentPreparedEvent event) {
        ConfigurableEnvironment environment = event.getEnvironment();
        if (!bootstrapEnabled(environment)          // 是否设置配置属性 spring.cloud.bootstrap.enabled 为 true
            && !useLegacyProcessing(environment)    // 是否存在 Marker 类
        ) {
            return; // 都不是，则返回，不处理
        }
        // 不要监听引导上下文中的事件
        if (environment.getPropertySources().contains("bootstrap")) {
            return;
        }
        ConfigurableApplicationContext context = null;
        // 参考： Boot-基础类-ConfigData ConfigDataLocationResolver
        // 默认配置名用 bootstrap，即查找 bootstrap .yaml .yml .properties 文件
        String configName = environment.resolvePlaceholders("${spring.cloud.bootstrap.name:bootstrap}");
        ...
        if (context == null) {
            context = bootstrapServiceContext(environment, event.getSpringApplication(), configName); // 构建 boot 上下文
            ...
        }

        apply(context, event.getSpringApplication(), environment); // 应用新的上下文部分配置
    }

    // sign_m_120 构建新的上下文
    private ConfigurableApplicationContext bootstrapServiceContext(ConfigurableEnvironment environment,
            final SpringApplication application, String configName
    ) {
        ConfigurableEnvironment bootstrapEnvironment = new AbstractEnvironment() { }; // 创建匿名内部类
        MutablePropertySources bootstrapProperties = bootstrapEnvironment.getPropertySources();
        ...
        // 参考： Boot-基础类-ConfigData ConfigDataLocationResolver
        bootstrapMap.put("spring.config.name", configName); // 设置配置文件名
        ...
        bootstrapProperties.addFirst(new MapPropertySource("bootstrap", bootstrapMap));
        ...
        SpringApplicationBuilder builder = new SpringApplicationBuilder()
                ...
                .web(WebApplicationType.NONE);
        final SpringApplication builderApplication = builder.application();
        ...
        /**
         * 创建（并刷新）上下文。
         * 会读取 bootstrap 配置文件，ref: sign_m_210
         */
        final ConfigurableApplicationContext context = builder.run();
        context.setId("bootstrap");
        ...
        // 合并属性：将 bootstrap 的配置添加到原环境中
        mergeDefaultProperties(environment.getPropertySources(), bootstrapProperties);
        return context;
    }
}
```

#### 使用 bootstrap 配置填充环境
- 参考：https://www.cnblogs.com/qlqwjy/p/17135908.html

- `org.springframework.boot.SpringApplication`
```java
    // sign_m_210 准备环境
    private ConfigurableEnvironment prepareEnvironment(
        SpringApplicationRunListeners listeners,
        DefaultBootstrapContext bootstrapContext, ApplicationArguments applicationArguments
    ) {
        ConfigurableEnvironment environment = getOrCreateEnvironment();
        ...
        listeners.environmentPrepared(bootstrapContext, environment); // ref: sign_m_220
        ...
        return environment;
    }
```

- `org.springframework.boot.context.event.EventPublishingRunListener`
```java
    // sign_m_220 发布环境准备好的事件
    @Override
    public void environmentPrepared(ConfigurableBootstrapContext bootstrapContext,
            ConfigurableEnvironment environment) {
        multicastInitialEvent( // 广播事件，其一监听器处理参考: sign_m_230
                new ApplicationEnvironmentPreparedEvent(bootstrapContext, ...)
        );
    }
```

- `org.springframework.boot.env.EnvironmentPostProcessorApplicationListener`
```java
    // sign_m_230 监听处理
    @Override
    public void onApplicationEvent(ApplicationEvent event) {
        if (event instanceof ApplicationEnvironmentPreparedEvent environmentPreparedEvent) {
            onApplicationEnvironmentPreparedEvent(environmentPreparedEvent); // ref: sign_m_231
        }
        ...
    }

    // sign_m_231 处理环境事件
    private void onApplicationEnvironmentPreparedEvent(ApplicationEnvironmentPreparedEvent event) {
        ConfigurableEnvironment environment = event.getEnvironment();
        SpringApplication application = event.getSpringApplication();
        List<EnvironmentPostProcessor> processors = this.getEnvironmentPostProcessors( // 获取处理器，ref: sign_m_232
            application.getResourceLoader(), event.getBootstrapContext()
        );
        for (EnvironmentPostProcessor postProcessor : processors) {
            postProcessor.postProcessEnvironment(environment, application); // 处理环境，ref: sign_m_240
        }
    }

    // sign_m_232 获取环境后处理器
    List<EnvironmentPostProcessor> getEnvironmentPostProcessors(
        ResourceLoader resourceLoader, ConfigurableBootstrapContext bootstrapContext
    ) {
        ...
        EnvironmentPostProcessorsFactory postProcessorsFactory = this.postProcessorsFactory.apply(classLoader);
        return postProcessorsFactory.getEnvironmentPostProcessors(this.deferredLogs, bootstrapContext);
    }
```

- `org.springframework.boot.context.config.ConfigDataEnvironmentPostProcessor`
```java
    // sign_m_240 处理环境
    @Override
    public void postProcessEnvironment(ConfigurableEnvironment environment, SpringApplication application) {
        postProcessEnvironment(environment, ...); // ref: sign_m_241
    }

    // sign_m_241
    void postProcessEnvironment(ConfigurableEnvironment environment, ResourceLoader resourceLoader,
            Collection<String> additionalProfiles) {
        resourceLoader = ... new DefaultResourceLoader();
        getConfigDataEnvironment(environment, resourceLoader, additionalProfiles)
            .processAndApply(); // ref: sign_m_250
    }
```

- `org.springframework.boot.context.config.ConfigDataEnvironment`
```java
    // sign_m_250 处理环境
    void processAndApply() {
        ...
        // 初始化 (包含解析配置)，ref: sign_m_253
        ConfigDataEnvironmentContributors contributors = processInitial(this.contributors, importer);
        ...
        applyToEnvironment(contributors, activationContext, ...); // 将配置应用到环境，ref: sign_m_251
    }

    // sign_m_251 将配置应用到环境
    private void applyToEnvironment(ConfigDataEnvironmentContributors contributors,
        ConfigDataActivationContext activationContext, Set<ConfigDataLocation> loadedLocations,
        Set<ConfigDataLocation> optionalLocations
    ) {
        ...
        MutablePropertySources propertySources = this.environment.getPropertySources();
        applyContributor(contributors, activationContext, propertySources); // ref: sign_m_252
        ...
    }

    // sign_m_252 将配置应用到环境
    private void applyContributor(ConfigDataEnvironmentContributors contributors,
            ConfigDataActivationContext activationContext, MutablePropertySources propertySources
    ) {
        for (ConfigDataEnvironmentContributor contributor : contributors) {
            PropertySource<?> propertySource = contributor.getPropertySource();
            if (contributor.getKind() == ConfigDataEnvironmentContributor.Kind.BOUND_IMPORT && propertySource != null) {
                if (!contributor.isActive(activationContext)) { ... }
                else {
                    ...
                    // 添加 bootstrap.properties 到环境的配置集
                    // -> OriginTrackedMapPropertySource {name='...[bootstrap.properties]' via location 'optional:classpath:/''}
                    propertySources.addLast(propertySource);
                    ...
                }
            }
        }
    }
    
    // sign_m_253 初始化 (包含解析配置)
    private ConfigDataEnvironmentContributors processInitial(ConfigDataEnvironmentContributors contributors,
            ConfigDataImporter importer) {
        contributors = contributors.withProcessedImports(importer, null); // 解析加载配置文件，ref: sign_m_260
        registerBootstrapBinder(contributors, null, DENY_INACTIVE_BINDING);
        return contributors;
    }
```

- `org.springframework.boot.context.config.ConfigDataEnvironmentContributors`
```java
    // sign_m_260 解析加载配置文件
    ConfigDataEnvironmentContributors withProcessedImports(ConfigDataImporter importer, ...) {
        ...
        while (true) {
            ...
            Map<ConfigDataResolutionResult, ConfigData> imported = importer.resolveAndLoad( // 解析加载配置文件，ref: sign_m_270
                activationContext, locationResolverContext, loaderContext, imports
            );
            ...
        }
    }
```

#### 查找并加载配置文件
- `org.springframework.boot.context.config.ConfigDataImporter`
```java
    // sign_m_270 解析加载配置文件
    Map<ConfigDataResolutionResult, ConfigData> resolveAndLoad( ... ) {
        try {
            ...
            // 从 "./"、"./config/" 和 "./config/*/" 目录下查找 ".xml .yml .yaml .properties" 文件
            // 最终查找出 "./bootstrap.properties" 文件
            // 参考： StandardConfigDataLocationResolver #resolve()
            List<ConfigDataResolutionResult> resolved = resolve(locationResolverContext, profiles, locations);
            return load(loaderContext, resolved); // 解析加载配置文件 (即 bootstrap.properties 文件)，ref: sign_m_271
        } ... // catch
    }

    // sign_m_271 解析加载配置文件
    private Map<ConfigDataResolutionResult, ConfigData> load( ... ) throws IOException {
        Map<ConfigDataResolutionResult, ConfigData> result = new LinkedHashMap<>();
        for (int i = candidates.size() - 1; i >= 0; i--) {
            ConfigDataResolutionResult candidate = candidates.get(i);
            ConfigDataResource resource = candidate.getResource();
            ...
            if (this.loaded.contains(resource)) { ... }
            else {
                try {
                    ConfigData loaded = this.loaders.load(loaderContext, resource); // ref: sign_m_280
                    ...
                } ... // catch
            }
        }
        return Collections.unmodifiableMap(result);
    }
```

- `org.springframework.boot.context.config.ConfigDataLoaders#load`
```java
    // sign_m_280 解析加载配置文件
    <R extends ConfigDataResource> ConfigData load(ConfigDataLoaderContext context, R resource) ... {
        ConfigDataLoader<R> loader = getLoader(context, resource);
        return loader.load(context, resource); // ref: sign_m_290
    }
```

- `org.springframework.boot.context.config.StandardConfigDataLoader`
```java
    // sign_m_290 解析加载配置文件
    @Override
    public ConfigData load(ConfigDataLoaderContext context, StandardConfigDataResource resource) ... {
        ...
        StandardConfigDataReference reference = resource.getReference();
        Resource originTrackedResource = OriginTrackedResource.of(resource.getResource(), ...);
        ...
        List<PropertySource<?>> propertySources = reference.getPropertySourceLoader()
            .load(name, originTrackedResource); // ref: sign_m_2A0
        ...
        return new ConfigData(propertySources, options);
    }
```

- `org.springframework.boot.env.PropertiesPropertySourceLoader`
```java
    // sign_m_2A0 解析加载配置文件
    @Override
    public List<PropertySource<?>> load(String name, Resource resource) ... {
        List<Map<String, ?>> properties = loadProperties(resource); // 解析 *.properties 配置文件
        ...
        List<PropertySource<?>> propertySources = new ArrayList<>(properties.size());
        for (int i = 0; i < properties.size(); i++) {
            String documentNumber = (properties.size() != 1) ? " (document #" + i + ")" : "";
            propertySources.add(
                new OriginTrackedMapPropertySource( // 封装下配置
                    name + documentNumber,
                    Collections.unmodifiableMap(properties.get(i)), 
                    true
                )
            );
        }
        return propertySources;
    }
```


### spring-cloud-commons
#### 自动配置导入
- `../../*.AutoConfiguration.imports`
  ```js
  *.client.CommonsClientAutoConfiguration // 阻塞式-服务发现 (并不创建 DiscoveryClient，只做健康检测等基础处理)
  *.client.ReactiveCommonsClientAutoConfiguration       // 响应式-服务发现
  ...
  *.client.loadbalancer.LoadBalancerAutoConfiguration   // 负载平衡，ref: sign_c_300
  ...
  *.client.serviceregistry.ServiceRegistryAutoConfiguration // 服务注册 Endpoint
  ...
  *.configuration.CompatibilityVerifierAutoConfiguration    // Boot 版本校验
  *.client.serviceregistry.AutoServiceRegistrationAutoConfiguration // 自动注册校验
  ...
  ```
  - **熔断器无配置**

#### 服务注册
- 关键类：
  - **服务注册**接口：`org.springframework.cloud.client.serviceregistry.ServiceRegistry`
  - **服务实例**接口：`org.springframework.cloud.client.ServiceInstance`
  - **注册项**（服务实例子类）接口：`org.springframework.cloud.client.serviceregistry.Registration`
  - **服务注册逻辑**抽象类：`org.springframework.cloud.client.serviceregistry.AbstractAutoServiceRegistration`
- 第三方提供商需实现上面两接口
  - 同时还需提供**自动配置类**，将上面两接口组装到 Context 中
  - 如 Ali 的 `com.alibaba.cloud.nacos.registry.NacosServiceRegistryAutoConfiguration`

#### 服务发现
- 关键类：
  - **服务发现**接口：`org.springframework.cloud.client.discovery.DiscoveryClient`
  - **启动服务发现**注解：`org.springframework.cloud.client.discovery.EnableDiscoveryClient`
  - **服务发现**选择器：`org.springframework.cloud.client.discovery.EnableDiscoveryClientImportSelector`
- 第三方提供商需实现上面的接口
  - 同时还需提供**自动配置类**，将上面的接口组装到 Context 中
  - 如 Ali 的 `com.alibaba.cloud.nacos.discovery.NacosDiscoveryClientConfiguration`

#### 负载均衡
- `org.springframework.cloud.client.loadbalancer.LoadBalancerAutoConfiguration`
```java
// sign_c_300
@AutoConfiguration
...
public class LoadBalancerAutoConfiguration {

    @LoadBalanced // 自定义的 RestTemplate 需加此注解，否则无效
    @Autowired(required = false) // 收集所有的 RestTemplate 实例
    private List<RestTemplate> restTemplates = Collections.emptyList();

    @Bean
    public SmartInitializingSingleton loadBalancedRestTemplateInitializerDeprecated(
            final ObjectProvider<List<RestTemplateCustomizer>> restTemplateCustomizers // 来源： sign_m_320
    ) {
        return () -> restTemplateCustomizers.ifAvailable(customizers -> {
            for (RestTemplate restTemplate : LoadBalancerAutoConfiguration.this.restTemplates) {
                for (RestTemplateCustomizer customizer : customizers) {
                    customizer.customize(restTemplate); // 对每个 RestTemplate 实例进行定制操作，ref: sign_cb_320
                }
            }
        });
    }

    // 拦截器配置
    @Configuration(proxyBeanMethods = false)
    @Conditional(RetryMissingOrDisabledCondition.class)
    static class LoadBalancerInterceptorConfig {
        // sign_m_310  初始化 REST 拦截器
        @Bean
        public LoadBalancerInterceptor loadBalancerInterceptor(
            LoadBalancerClient loadBalancerClient, // 来源： sign_m_420
            LoadBalancerRequestFactory requestFactory
        ) {
            return new LoadBalancerInterceptor(loadBalancerClient, requestFactory); // ref: sign_c_510
        }

        // sign_m_320  初始化 REST 定制器
        @Bean
        @ConditionalOnMissingBean
        public RestTemplateCustomizer restTemplateCustomizer(final LoadBalancerInterceptor loadBalancerInterceptor) {
            return restTemplate -> { // sign_cb_320
                List<ClientHttpRequestInterceptor> list = new ArrayList<>(restTemplate.getInterceptors());
                list.add(loadBalancerInterceptor);  // 添加，来源： sign_m_310
                restTemplate.setInterceptors(list); // 设置进去
            };
        }
    }
}
```


### spring-cloud-loadbalancer
#### 自动配置导入
- `../../*.AutoConfiguration.imports`
  ```js
  *.loadbalancer.config.LoadBalancerAutoConfiguration // 基础配置，ref: sign_c_410
  *.loadbalancer.config.BlockingLoadBalancerClientAutoConfiguration // 客户端配置，ref: sign_c_420
  *.loadbalancer.config.LoadBalancerCacheAutoConfiguration
  *.loadbalancer.security.OAuth2LoadBalancerClientAutoConfiguration
  *.loadbalancer.config.LoadBalancerStatsAutoConfiguration
  ```

#### 自动配置
- `org.springframework.cloud.loadbalancer.config.LoadBalancerAutoConfiguration`
```java
// sign_c_410  基础配置
@Configuration(proxyBeanMethods = false)
@EnableConfigurationProperties({ LoadBalancerClientsProperties.class, LoadBalancerEagerLoadProperties.class })
...
public class LoadBalancerAutoConfiguration {

    // sign_m_410  初始化获取服务实例的工厂
    @ConditionalOnMissingBean
    @Bean
    public LoadBalancerClientFactory loadBalancerClientFactory(LoadBalancerClientsProperties properties,
            ObjectProvider<List<LoadBalancerClientSpecification>> configurations) {
        LoadBalancerClientFactory clientFactory = new LoadBalancerClientFactory(properties); // 获取服务实例
        clientFactory.setConfigurations(configurations.getIfAvailable(Collections::emptyList));
        return clientFactory;
    }
}
```

- `org.springframework.cloud.loadbalancer.config.BlockingLoadBalancerClientAutoConfiguration`
```java
// sign_c_420  客户端配置
@Configuration(proxyBeanMethods = false)
@LoadBalancerClients
...
public class BlockingLoadBalancerClientAutoConfiguration {

    // sign_m_420  初始化客户端
    @Bean
    @ConditionalOnBean(LoadBalancerClientFactory.class)
    @ConditionalOnMissingBean
    public LoadBalancerClient blockingLoadBalancerClient(
        LoadBalancerClientFactory loadBalancerClientFactory // 来源： sign_m_410
    ) {
        return new BlockingLoadBalancerClient(loadBalancerClientFactory); // ref: sign_c_520
    }
}
```

#### 拦截器
- `org.springframework.cloud.client.loadbalancer.LoadBalancerInterceptor`
```java
// sign_c_510  拦截器
public class LoadBalancerInterceptor implements ClientHttpRequestInterceptor {
    // sign_m_510  拦截处理
    @Override
    public ClientHttpResponse intercept(final HttpRequest request, final byte[] body,
            final ClientHttpRequestExecution execution) throws IOException {
        final URI originalUri = request.getURI();
        String serviceName = originalUri.getHost();
        ...
        return this.loadBalancer.execute(serviceName, ...); // 执行请求，ref: sign_m_520
    }
}
```

- `org.springframework.cloud.loadbalancer.blocking.client.BlockingLoadBalancerClient`
```java
// sign_c_520  客户端
public class BlockingLoadBalancerClient implements LoadBalancerClient {

    // sign_m_520  执行请求
    @Override
    public <T> T execute(String serviceId, LoadBalancerRequest<T> request) throws IOException {
        ...
        ServiceInstance serviceInstance = choose(serviceId, lbRequest); // 选出服务实例，ref: sign_m_521
        ...
        return execute(serviceId, serviceInstance, lbRequest); // 进行请求，ref: sign_m_522
    }

    // sign_m_521  均衡算法，选出服务实例
    @Override
    public <T> ServiceInstance choose(String serviceId, Request<T> request) {
        ReactiveLoadBalancer<ServiceInstance> loadBalancer = loadBalancerClientFactory.getInstance(serviceId); // 获取负载均衡器
        ...
        Response<ServiceInstance> loadBalancerResponse = Mono.from(
                loadBalancer.choose(request)        // 使用负载均衡算法，选择出服务实例
            )
            .block();
        ...
        return loadBalancerResponse.getServer();    // 返回服务实例
    }

    // sign_m_522  对选出的服务实例进行请求
    @Override
    public <T> T execute(
        String serviceId, ServiceInstance serviceInstance, LoadBalancerRequest<T> request
    ) throws IOException {
        ...
        try {
            // request 最终为 BlockingLoadBalancerRequest 实例，ref: sign_c_530
            T response = request.apply(serviceInstance); // 请求处理，ref: sign_m_530
            ...
            return response;
        }
        ... // catch
        return null;
    }
}
```

- `org.springframework.cloud.client.loadbalancer.BlockingLoadBalancerRequest`
  - [Web-RestTemplate-请求 sign_m_211](Web-RestTemplate.md#请求)
```java
// sign_c_530
class BlockingLoadBalancerRequest implements HttpRequestLoadBalancerRequest<ClientHttpResponse> {

    // sign_m_530  请求处理
    @Override
    public ClientHttpResponse apply(ServiceInstance instance) throws Exception {
        HttpRequest serviceRequest = new ServiceRequestWrapper(clientHttpRequestData.request, instance, loadBalancer);
        ...
        return clientHttpRequestData.execution // 为 InterceptingClientHttpRequest.InterceptingRequestExecution 实例
            .execute(serviceRequest, clientHttpRequestData.body); // 参考：[Web-RestTemplate-请求 sign_m_211]，没有拦截器
    }
}
```