## Spring-Boot 原理

### Spring-Boot 条件注解
#### 单元测试
```java
public class MyPropertyTest {
    @Test
    void test() {
        ConfigurableEnvironment environment = new StandardEnvironment();
        TestPropertyValues.of(
                        "simple.my-property: test"
                )
                .applyTo(environment);
        ConfigurableApplicationContext context = new SpringApplicationBuilder(MyConfig.class)
                .environment(environment)
                .web(WebApplicationType.NONE)
                .run();
        System.out.println("contains-foo: " + context.containsBean("foo"));
        System.out.println("contains-foo1: " + context.containsBean("foo1"));
        System.out.println("contains-one: " + context.containsBean("one"));
        System.out.println("contains-two: " + context.containsBean("two"));
        System.out.println("contains-three: " + context.containsBean("three"));
        System.out.println("contains-three1: " + context.containsBean("three1"));
        System.out.println("contains-three2: " + context.containsBean("three2"));
    }

    @Configuration(proxyBeanMethods = false)
    static class MyConfig {
        @Bean // 配置值与 havingValue 值不匹配，不创建
        @ConditionalOnProperty(prefix = "simple", name = "my-property", havingValue = "1111", matchIfMissing = true)
        String foo() {
            return "foo";
        }

        @Bean // 配置值与 havingValue 值匹配，创建
        @ConditionalOnProperty(prefix = "simple", name = "my-property", havingValue = "test", matchIfMissing = true)
        String foo1() {
            return "foo1";
        }

        @Bean // 有 my-property 配置 key 且配置的值不为 false，创建。与 matchIfMissing 无关
        @ConditionalOnProperty(prefix = "simple", name = "my-property", matchIfMissing = false)
        String one() {
            return "one";
        }

        @Bean // 有 my-property 配置 key 且配置的值不为 false，创建。与 matchIfMissing 无关
        @ConditionalOnProperty(prefix = "simple", name = "my-property", matchIfMissing = true)
        String two() {
            return "two";
        }

        @Bean // 配置值与 havingValue 值匹配，创建
        @ConditionalOnProperty(prefix = "simple", name = "my-property", havingValue = "test")
        String three() {
            return "three";
        }

        @Bean // 没有 my-property2 配置 key 且 matchIfMissing 为 true，创建
        @ConditionalOnProperty(prefix = "simple", name = "my-property2", matchIfMissing = true)
        String three1() {
            return "three1";
        }

        @Bean // 没有 my-property2 配置 key 且 matchIfMissing 为 false，不创建
        @ConditionalOnProperty(prefix = "simple", name = "my-property2", matchIfMissing = false)
        String three2() {
            return "three2";
        }
    }
}
```

#### 原理
- 参考：[Configuration-加载原理-条件解析](Configuration-加载原理.md#条件解析)
- `org.springframework.boot.autoconfigure.condition.ConditionalOnProperty`
```java
/*** 属性配置条件注解 */
@Retention(RetentionPolicy.RUNTIME)
@Target({ ElementType.TYPE, ElementType.METHOD })
@Conditional(OnPropertyCondition.class) // 设置条件解析类
public @interface ConditionalOnProperty {
    /*** 前缀 */
    String prefix() default "";
    /*** 名称（属性 key） */
    String[] name() default {};
    /*** 条件值（如果没设置，则配置值不能为 false，否则算为不匹配） */
    String havingValue() default "";
    /*** true: 没有设置对应的属性，也表示为匹配上 */
    boolean matchIfMissing() default false;
}
```

- `org.springframework.boot.autoconfigure.condition.OnPropertyCondition`
```java
/*** 属性配置条件注解解析类 */
@Order(Ordered.HIGHEST_PRECEDENCE + 40)
class OnPropertyCondition extends SpringBootCondition {
    /*** 实现父类的钩子函数 */
    @Override
    public ConditionOutcome getMatchOutcome(ConditionContext context, AnnotatedTypeMetadata metadata) {
        List<AnnotationAttributes> allAnnotationAttributes = metadata.getAnnotations()
            .stream(ConditionalOnProperty.class.getName()) // 只解析 @ConditionalOnProperty 注解
            .filter(MergedAnnotationPredicates.unique(MergedAnnotation::getMetaTypes)) // 去重
            .map(MergedAnnotation::asAnnotationAttributes)
            .toList();
        List<ConditionMessage> noMatch = new ArrayList<>();
        List<ConditionMessage> match = new ArrayList<>();
        for (AnnotationAttributes annotationAttributes : allAnnotationAttributes) {
            ConditionOutcome outcome = determineOutcome(annotationAttributes, context.getEnvironment()); // 获取单个匹配结果
            (outcome.isMatch() ? match : noMatch).add(outcome.getConditionMessage()); // 匹配上就加入到已匹配集合，否则就加入到未匹配集合
        }
        if (!noMatch.isEmpty()) { // 只要有一个没匹配上，就返回无匹配（noMatch）
            return ConditionOutcome.noMatch(ConditionMessage.of(noMatch));
        }
        return ConditionOutcome.match(ConditionMessage.of(match)); // 返回有匹配（match）
    }

    // 进行单个匹配
    private ConditionOutcome determineOutcome(AnnotationAttributes annotationAttributes, PropertyResolver resolver) {
        Spec spec = new Spec(annotationAttributes);
        List<String> missingProperties = new ArrayList<>();     // 缺失的属性
        List<String> nonMatchingProperties = new ArrayList<>(); // 未匹配到值的属性
        // 进行匹配计算处理
        spec.collectProperties(resolver, missingProperties, nonMatchingProperties);
        if (!missingProperties.isEmpty()) { // 存在“缺失的属性”，返回匹配失败
            return ConditionOutcome.noMatch(ConditionMessage.forCondition(ConditionalOnProperty.class, spec);
        }
        if (!nonMatchingProperties.isEmpty()) { // 存在“未匹配到值的属性”，返回匹配失败
            return ConditionOutcome.noMatch(ConditionMessage.forCondition(ConditionalOnProperty.class, spec);
        }
        // 以上条件都未满足（没有"缺失的属性"及"未匹配到值的属性"），就相当于匹配成功
        return ConditionOutcome
            .match(ConditionMessage.forCondition(ConditionalOnProperty.class, spec).because("matched"));
    }

    /*** 内部类封装注解属性 */
    private static class Spec {
        ...
        // 匹配计算
        private void collectProperties(PropertyResolver resolver, List<String> missing, List<String> nonMatching) {
            for (String name : this.names) {
                String key = this.prefix + name;
                if (resolver.containsProperty(key)) { // 存在属性值
                    if (!isMatch(resolver.getProperty(key), this.havingValue)) { // 进入匹配计算
                        nonMatching.add(name);     // 属性值不匹配
                    }
                }
                else {
                    if (!this.matchIfMissing) {    // 不存在属性，且 @ConditionalOnProperty 的 matchIfMissing 值为 false
                        missing.add(name);        // 属性值缺失
                    }
                }
            }
        }

        // 属性值匹配计算
        private boolean isMatch(String value, String requiredValue) {
            if (StringUtils.hasLength(requiredValue)) { // @ConditionalOnProperty 的 havingValue 值不为空
                return requiredValue.equalsIgnoreCase(value); // 进行值匹配
            }
            return !"false".equalsIgnoreCase(value); // 注解的 havingValue 值为空，且配置的值不为 false，表示匹配成功，否则匹配失败
        }
    }
}
```

- `org.springframework.boot.autoconfigure.condition.SpringBootCondition`
  - 参考：[Configuration-加载原理-条件解析](Configuration-加载原理.md#条件解析)
```java
/*** Spring-Boot 条件注解解析父类 */
public abstract class SpringBootCondition implements Condition {
    @Override
    public final boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata) {
        ...
        try {
            ConditionOutcome outcome = getMatchOutcome(context, metadata); // 调用子类钩子函数
            ...
            return outcome.isMatch(); // 返回是否匹配
        }
        ... // 省略 catch
    }

    /*** 获取匹配结果（具体匹配结果，由子类实现） */
    public abstract ConditionOutcome getMatchOutcome(ConditionContext context, AnnotatedTypeMetadata metadata);
}
```

##### 其他条件注解
- `@ConditionalOnBean`
- `@ConditionalOnClass`
- `@ConditionalOnExpression`
- `@ConditionalOnResource`
- `@ConditionalOnWebApplication`
- ... 省略


### Spring-Boot 加载类
#### 关键类
- `org.springframework.boot.autoconfigure.SpringBootApplication`
- `org.springframework.boot.autoconfigure.EnableAutoConfiguration`
- `org.springframework.boot.autoconfigure.AutoConfigurationImportSelector`
- `org.springframework.boot.context.annotation.ImportCandidates`

#### 单元测试
- 参考：
  - `org.springframework.boot.context.annotation.ImportCandidatesTests`
  - `org.springframework.boot.autoconfigure.SpringBootApplicationTests`

- 自定义测试：
```java
// 在 spring-boot-smoke-test-quartz 项目里创建测试类
@SpringBootApplication
public class MyQuartzAppTest {
    @Test
    public void test() {
        SpringApplication app = new SpringApplication(MyQuartzAppTest.class); // App 类会记录在 primarySources 属性里
        ConfigurableApplicationContext ctx = app.run();
        System.out.println("fa: " + ctx.containsBean("fa"));
    }

    @Bean
    public String fa() {
        return "fa";
    }
}
```

#### 原理
- 上下文刷新参考：[Context-刷新原理](Context-刷新原理.md#原理)

- `org.springframework.boot.SpringApplication`
```java
    /*** 启动 Spring 应用 */
    public ConfigurableApplicationContext run(String... args) {
        ... // 省略其他处理
        try {
            ... // 省略其他处理
            context = createApplicationContext(); // 创建上下文
            context.setApplicationStartup(this.applicationStartup);
            prepareContext(bootstrapContext, context, environment, listeners, applicationArguments, printedBanner); // 准备上下文
            refreshContext(context); // 刷新上下文
            ... // 省略其他处理
        }
        ... // 省略 catch 和其他处理
        return context;
    }
    
    // 准备上下文（相当于初始化上下文）
    private void prepareContext(DefaultBootstrapContext bootstrapContext, ConfigurableApplicationContext context,
            ConfigurableEnvironment environment, SpringApplicationRunListeners listeners,
            ApplicationArguments applicationArguments, Banner printedBanner) {
        context.setEnvironment(environment);
        ... // 省略其他
        if (!AotDetector.useGeneratedArtifacts()) { // 调试时会进入 if 语句
            Set<Object> sources = getAllSources();
            load(context, sources.toArray(new Object[0])); // 相当于将 App 类注册到 context
        }
        ...
    }

    // 获取源
    public Set<Object> getAllSources() {
        Set<Object> allSources = new LinkedHashSet<>();
        if (!CollectionUtils.isEmpty(this.primarySources)) {
            allSources.addAll(this.primarySources); // 相当于返回 App 类
        }
        ...
        return Collections.unmodifiableSet(allSources);
    }
```

- `org.springframework.boot.autoconfigure.SpringBootApplication`
```java
/*** Spring 应用关键注解 */
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Inherited
@SpringBootConfiguration // 内部有 @Configuration 注解，使其有配置类的功能
@EnableAutoConfiguration // 关键注解，导入自动配置类
@ComponentScan(excludeFilters = { @Filter(type = FilterType.CUSTOM, classes = TypeExcludeFilter.class),
        @Filter(type = FilterType.CUSTOM, classes = AutoConfigurationExcludeFilter.class) })
public @interface SpringBootApplication {
    ... // 省略属性定义
}
```

- `org.springframework.boot.autoconfigure.EnableAutoConfiguration`
```java
/*** 自动配置的注解 */
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Inherited
@AutoConfigurationPackage // 略
@Import(AutoConfigurationImportSelector.class) // 导入自动配置类
public @interface EnableAutoConfiguration {
    ... // 省略属性定义
}
```

##### 导入原理
- 调用参考：[Import-原理](Import-原理.md#原理)

- `org.springframework.boot.autoconfigure.AutoConfigurationImportSelector`
```java
/*** 自动配置导入选择器 */
public class AutoConfigurationImportSelector implements DeferredImportSelector, BeanClassLoaderAware,
        ResourceLoaderAware, BeanFactoryAware, EnvironmentAware, Ordered {

    /*** 实现 ImportSelector 导入方法 */
    @Override
    public String[] selectImports(AnnotationMetadata annotationMetadata) {
        if (!isEnabled(annotationMetadata)) { // 如果未启用，则不导入
            return NO_IMPORTS;
        }
        AutoConfigurationEntry autoConfigurationEntry = getAutoConfigurationEntry(annotationMetadata); // 查找...
        return StringUtils.toStringArray(autoConfigurationEntry.getConfigurations());
    }

    // 获取要导入的自动配置类
    protected AutoConfigurationEntry getAutoConfigurationEntry(AnnotationMetadata annotationMetadata) {
        ... // 省略未启用判断处理
        AnnotationAttributes attributes = getAttributes(annotationMetadata); // 获取 @EnableAutoConfiguration 注解属性
        List<String> configurations = getCandidateConfigurations(annotationMetadata, attributes); // 获取配置类
        ... // 省略去重、排除、过滤、发送事件的处理
        return new AutoConfigurationEntry(configurations, exclusions);
    }

    /**
     * 获取配置类。
     * 读取类路径下所有的 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports 文件
     *     Spring-Boot 2.7 之后的改动（不再使用 spring.factories 定义自动配置类）
     */
    protected List<String> getCandidateConfigurations(AnnotationMetadata metadata, AnnotationAttributes attributes) {
        List<String> configurations = ImportCandidates.load(AutoConfiguration.class, getBeanClassLoader())
            .getCandidates();
        ... // 省略断言
        return configurations;
    }
}
```