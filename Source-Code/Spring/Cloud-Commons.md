## Spring-Cloud-Commons


### 使用示例
- 服务注册与发现：https://github.com/zengxf/spring-demo/tree/master/cloud-demo/ali-nacos/naming-test-1
- 依赖：
  - `spring-cloud-starter-alibaba-nacos-discovery`
    - `spring-cloud-context`
    - `spring-cloud-commons`


### 原理
#### spring-cloud-context
##### 自动配置导入
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

##### 新 Context 刷新
- 单元测试参考：
  - `org.springframework.cloud.bootstrap.BootstrapSourcesOrderingTests`

- `org.springframework.cloud.bootstrap.BootstrapApplicationListener`
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
        if (environment.getPropertySources().contains(BOOTSTRAP_PROPERTY_SOURCE_NAME)) {
            return;
        }
        ConfigurableApplicationContext context = null;
        String configName = environment.resolvePlaceholders("${spring.cloud.bootstrap.name:bootstrap}");
        ...
        if (context == null) {
            context = bootstrapServiceContext(environment, event.getSpringApplication(), configName); // 构建 boot 上下文
            ...
        }

        apply(context, event.getSpringApplication(), environment); // 应用新的上下文
    }

    // sign_m_120
    private ConfigurableApplicationContext bootstrapServiceContext(ConfigurableEnvironment environment,
            final SpringApplication application, String configName) {
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
        mergeDefaultProperties(environment.getPropertySources(), bootstrapProperties); // 合并属性
        return context;
    }
}
```

##### 加载 bootstrap 文件
- 参考：https://www.cnblogs.com/qlqwjy/p/17135908.html

- `org.springframework.boot.SpringApplication`
```java
    // sign_m_210
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
    // sign_m_220
    @Override
    public void environmentPrepared(ConfigurableBootstrapContext bootstrapContext,
            ConfigurableEnvironment environment) {
        multicastInitialEvent( // 广播事件，其一监听器处理参考: sign_m_230
                new ApplicationEnvironmentPreparedEvent(bootstrapContext, this.application, this.args, environment)
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

    // sign_m_231
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
    ConfigDataEnvironmentContributors withProcessedImports(ConfigDataImporter importer,
            ConfigDataActivationContext activationContext) {
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

- `org.springframework.boot.context.config.ConfigDataImporter`
```java
    // sign_m_270 解析加载配置文件
    Map<ConfigDataResolutionResult, ConfigData> resolveAndLoad(ConfigDataActivationContext activationContext,
            ConfigDataLocationResolverContext locationResolverContext, ConfigDataLoaderContext loaderContext,
            List<ConfigDataLocation> locations
    ) {
        try {
            ...
            // 从 "/" 和 "/config/" 目录下查找 ".xml .yml .yaml .properties" 文件
            // 最终查找出 "/bootstrap.properties" 文件
            // 参考：StandardConfigDataLocationResolver #resolve()
            List<ConfigDataResolutionResult> resolved = resolve(locationResolverContext, profiles, locations);
            return load(loaderContext, resolved); // 解析加载配置文件 (即 bootstrap.properties 文件)，ref: sign_m_271
        } ... // catch
    }

    // sign_m_271 解析加载配置文件
    private Map<ConfigDataResolutionResult, ConfigData> load(ConfigDataLoaderContext loaderContext,
            List<ConfigDataResolutionResult> candidates
    ) throws IOException {
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
    <R extends ConfigDataResource> ConfigData load(ConfigDataLoaderContext context, R resource) throws IOException {
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
    public List<PropertySource<?>> load(String name, Resource resource) throws IOException {
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


#### spring-cloud-commons
##### 自动配置导入
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
