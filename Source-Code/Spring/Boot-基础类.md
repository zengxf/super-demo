# Spring-Boot-基础类

---
## Binder
- 类全名：`org.springframework.boot.context.properties.bind.Binder`

### 单元测试
- 参考：`org.springframework.boot.context.properties.bind.BinderTests`

```java
    private final List<ConfigurationPropertySource> sources = new ArrayList<>();
    private Binder binder = new Binder(this.sources);

    @Test
    void bindToValueShouldReturnConvertedPropertyValue() {
        this.sources.add(new MockConfigurationPropertySource("foo", "123"));
        // 读取 foo 配置值，并转换成 Integer 类型
        BindResult<Integer> result = this.binder.bind("foo", Bindable.of(Integer.class));
        assertThat(result.get()).isEqualTo(123);
    }
```

### 说明
- 相当于一个容器对象，解析里面的 `ConfigurationPropertySource` 属性值


---
## ConfigData
- **配置数据**，
  - 从 `ConfigDataResource` 加载出来，可能最终为 Spring 的环境提供属性源。

### 相关类
- **配置数据源** `ConfigDataResource`
  - 可以从中加载出单个 `ConfigData`
- **配置数据加载器** `ConfigDataLoader`
  - 接口类，加载数据源，加载出 `ConfigData` 对象
- **配置数据加载器集合封装** `ConfigDataLoaders`
  - 封装一组加载器，用于加载不同类型的数据源，加载出 `ConfigData` 对象
- **配置数据位置** `ConfigDataLocation`
  - 可以解析为一个或多个配置数据源 `ConfigDataResource`
    - 是字符串值的简单包装
  - 由前缀和路径组成的类似于 URL 的语法
    - 例如，`crypt:somehost/somepath`
    - 位置可以是强制性的，也可以是可选的
      - 可选位置以 `optional:` 为前缀
- **配置数据位置解析器** `ConfigDataLocationResolver`
  - 接口类，将位置解析为多个数据源 `ConfigDataResource`
  - 子类 `StandardConfigDataLocationResolver` 默认查找 `application` 名称相关配置
    - 可通过 `Binder` 查找 key 为 `spring.config.name` 指定名称的相关配置
- **配置数据位置解析器集合封装** `ConfigDataLocationResolvers`
  - 封装一组解析器，用于解析不同类型的数据位置，解析出数据源

### 单元测试
- 测试 1 (**加载器**)
  - 参考：`org.springframework.boot.context.config.StandardConfigDataLoaderTests`
```yml
# 配置文件 configdata/yaml/application.yml
foo: bar
---
hello: world
```
```java
    private final StandardConfigDataLoader loader = new StandardConfigDataLoader();
    private final ConfigDataLoaderContext loaderContext = mock(ConfigDataLoaderContext.class);

    @Test
    void loadWhenLocationResultsInMultiplePropertySourcesAddsAllToConfigData() throws IOException {
        ClassPathResource resource = new ClassPathResource("configdata/yaml/application.yml");
        StandardConfigDataReference reference = new StandardConfigDataReference(..., "yml", new YamlPropertySourceLoader());
        StandardConfigDataResource location = new StandardConfigDataResource(reference, resource); // 创建：配置数据源
        ConfigData configData = this.loader.load(this.loaderContext, location);     // 加载
        PropertySource<?> source1 = configData.getPropertySources().get(0);         // 获取配置
        PropertySource<?> source2 = configData.getPropertySources().get(1);
        assertThat(source1.getProperty("foo")).isEqualTo("bar");                    // 查找属性
        assertThat(source2.getProperty("hello")).isEqualTo("world");
    }
```

- 测试 2 (**加载器集**)
  - 参考：`org.springframework.boot.context.config.ConfigDataLoadersTests`
```java
    private final DeferredLogFactory logFactory = Supplier::get;
    private final DefaultBootstrapContext bootstrapContext = new DefaultBootstrapContext();
    private final ConfigDataLoaderContext context = mock(ConfigDataLoaderContext.class);

    @Test
    void loadWhenGenericTypeDoesNotMatchSkipsLoader() throws Exception {
        MockSpringFactoriesLoader springFactoriesLoader = new MockSpringFactoriesLoader();
        springFactoriesLoader.add(
            ConfigDataLoader.class,
            OtherConfigDataLoader.class, SpecificConfigDataLoader.class         // 设置 2 个加载器
        );
        ConfigDataLoaders loaders = new ConfigDataLoaders(this.logFactory, this.bootstrapContext, springFactoriesLoader);
        TestConfigDataResource location = new TestConfigDataResource("test");   // 配置数据源
        ConfigData loaded = loaders.load(this.context, location);               // 加载
        ...
    }
```

- 测试 3 (**解析器**)
  - 参考：`org.springframework.boot.context.config.StandardConfigDataLocationResolverTests`
```java
    private MockEnvironment environment;
    private Binder environmentBinder;
    private final ResourceLoader resourceLoader = new DefaultResourceLoader();
    private StandardConfigDataLocationResolver resolver;

    @BeforeEach
    void setup() {
        this.environment = new MockEnvironment();
        this.environmentBinder = Binder.get(this.environment);
        this.resolver = new StandardConfigDataLocationResolver(..., this.environmentBinder, this.resourceLoader);
    }

    @Test
    void resolveWhenLocationIsDirectoryResolvesAllMatchingFilesInDirectory() {
        ConfigDataLocation location = ConfigDataLocation.of("classpath:/configdata/properties/");
        List<StandardConfigDataResource> locations = this.resolver.resolve(this.context, location);
        ((ClassPathResource) locations.get(0).getResource()).getPath(); // 查找出文件为: ./configdata/properties/application.properties
    }
```