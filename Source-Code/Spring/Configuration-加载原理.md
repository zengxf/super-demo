## 主要内容
- `@Configuration` 注解导入
- `@Conditional` 条件过滤

## 单元测试
- `org.springframework.context.annotation.ConfigurationClassWithConditionTests`
```java
// 参考 ConfigurationClassWithConditionTests 写的简单测试类
public class SimpleConfigurationTests {
    @Test
    public void conditionalOnMissingBeanMatch() throws Exception {
        AnnotationConfigApplicationContext ctx = new AnnotationConfigApplicationContext();
        ctx.register(BeanOneConfiguration.class, BeanTwoConfiguration.class);
        ctx.refresh();
        assertThat(ctx.containsBean("bean1")).isTrue();
        assertThat(ctx.containsBean("bean2")).isFalse();
        assertThat(ctx.containsBean("configurationClassWithConditionTests.BeanTwoConfiguration")).isFalse();
    }

    /** 自定义配置类 */
    @Configuration
    static class BeanOneConfiguration { // 无条件实例化
        @Bean
        public ExampleBean bean1() {
            return new ExampleBean();
        }
    }

    /** 自定义配置类 */
    @Configuration
    @Conditional(NoBeanOneCondition.class) // 设置条件（此条件不会实例化）
    static class BeanTwoConfiguration {
        @Bean
        public ExampleBean bean2() {
            return new ExampleBean();
        }
    }

    /** 自定义条件类 */
    static class NoBeanOneCondition implements Condition {
        @Override
        public boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata) {
            System.out.println("\n------------- 进入 --------------\n");
            new RuntimeException("栈跟踪").printStackTrace(System.out);
            return !context.getBeanFactory().containsBeanDefinition("bean1"); // 没有 bean1 才进行配置实例化
        }
    }

    static class ExampleBean {
    }
}
```


## 原理
- 先看调用栈
```java
// ctx.register(Cfg.class);

------------- 进入 --------------

java.lang.RuntimeException: 栈跟踪
    at org.springframework.context.annotation.test_my.SimpleConfigurationTests$NoBeanOneCondition.matches(SimpleConfigurationTests.java:76)
    at org.springframework.context.annotation.ConditionEvaluator.shouldSkip(ConditionEvaluator.java:108)
    at org.springframework.context.annotation.ConditionEvaluator.shouldSkip(ConditionEvaluator.java:88)
    at org.springframework.context.annotation.ConditionEvaluator.shouldSkip(ConditionEvaluator.java:71) // 3
    at org.springframework.context.annotation.AnnotatedBeanDefinitionReader.doRegisterBean(AnnotatedBeanDefinitionReader.java:254)
    at org.springframework.context.annotation.AnnotatedBeanDefinitionReader.registerBean(AnnotatedBeanDefinitionReader.java:147)
    at org.springframework.context.annotation.AnnotatedBeanDefinitionReader.register(AnnotatedBeanDefinitionReader.java:137) // 2
    at org.springframework.context.annotation.AnnotationConfigApplicationContext.register(AnnotationConfigApplicationContext.java:168) // 1
    at org.springframework.context.annotation.test_my.SimpleConfigurationTests.conditionalOnMissingBeanMatch(SimpleConfigurationTests.java:13)



// ctx.refresh();

------------- 进入 --------------

java.lang.RuntimeException: 栈跟踪
    at org.springframework.context.annotation.test_my.SimpleConfigurationTests$NoBeanOneCondition.matches(SimpleConfigurationTests.java:76)
    at org.springframework.context.annotation.ConditionEvaluator.shouldSkip(ConditionEvaluator.java:108) // 5
    at org.springframework.context.annotation.ConfigurationClassParser.processConfigurationClass(ConfigurationClassParser.java:219)
    at org.springframework.context.annotation.ConfigurationClassParser.parse(ConfigurationClassParser.java:196)
    at org.springframework.context.annotation.ConfigurationClassParser.parse(ConfigurationClassParser.java:164) // 4
    at org.springframework.context.annotation.ConfigurationClassPostProcessor.processConfigBeanDefinitions(ConfigurationClassPostProcessor.java:415)
    at org.springframework.context.annotation.ConfigurationClassPostProcessor.postProcessBeanDefinitionRegistry(ConfigurationClassPostProcessor.java:287) // 3
    at org.springframework.context.support.PostProcessorRegistrationDelegate.invokeBeanDefinitionRegistryPostProcessors(PostProcessorRegistrationDelegate.java:344)
    at org.springframework.context.support.PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors(PostProcessorRegistrationDelegate.java:115) // 2
    at org.springframework.context.support.AbstractApplicationContext.invokeBeanFactoryPostProcessors(AbstractApplicationContext.java:771)
    at org.springframework.context.support.AbstractApplicationContext.refresh(AbstractApplicationContext.java:589) // 1
    at org.springframework.context.annotation.test_my.SimpleConfigurationTests.conditionalOnMissingBeanMatch(SimpleConfigurationTests.java:14)
```

### Context 刷新加载原理
- 主要讲 `ctx.refresh();` 加载配置的原理
  - `ctx.register(Cfg.class);` 此原理省略

- `org.springframework.context.support.AbstractApplicationContext`
```java
    @Override
    public void refresh() throws BeansException, IllegalStateException {
        synchronized (this.startupShutdownMonitor) {
            ... // 省略
            try {
                ... // 省略

                // 调用 Bean 工厂后处理器
                invokeBeanFactoryPostProcessors(beanFactory);

                ... // 省略
            }
            ... // 省略
        }
    }

    protected void invokeBeanFactoryPostProcessors(ConfigurableListableBeanFactory beanFactory) {
        PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors(beanFactory, getBeanFactoryPostProcessors());
        ... // 省略
    }
```

- `org.springframework.context.support.PostProcessorRegistrationDelegate`
```java
    /*** 调用 Bean 工厂后处理器 */
    public static void invokeBeanFactoryPostProcessors(
            ConfigurableListableBeanFactory beanFactory, // 默认是 DefaultListableBeanFactory 实例
            List<BeanFactoryPostProcessor> beanFactoryPostProcessors // 测试时为空
    ) {

        Set<String> processedBeans = new HashSet<>();

        if (beanFactory instanceof BeanDefinitionRegistry registry) {
            List<BeanFactoryPostProcessor> regularPostProcessors = new ArrayList<>();
            List<BeanDefinitionRegistryPostProcessor> registryProcessors = new ArrayList<>();

            ... // 遍历 beanFactoryPostProcessors 处理

            List<BeanDefinitionRegistryPostProcessor> currentRegistryProcessors = new ArrayList<>();

            // 只有一个，对应的是 org.springframework.context.annotation.ConfigurationClassPostProcessor
            String[] postProcessorNames =
                    beanFactory.getBeanNamesForType(BeanDefinitionRegistryPostProcessor.class, true, false);
            for (String ppName : postProcessorNames) {
                if (beanFactory.isTypeMatch(ppName, PriorityOrdered.class)) {
                    currentRegistryProcessors.add(beanFactory.getBean(ppName, BeanDefinitionRegistryPostProcessor.class));
                    processedBeans.add(ppName);
                }
            }
            sortPostProcessors(currentRegistryProcessors, beanFactory);
            registryProcessors.addAll(currentRegistryProcessors);
            invokeBeanDefinitionRegistryPostProcessors(currentRegistryProcessors, registry, beanFactory.getApplicationStartup()); // 在此方法调用
            currentRegistryProcessors.clear();
            
            ... // 省略其他处理

            // 调用 Bean 工厂后处理器方法
            invokeBeanFactoryPostProcessors(registryProcessors, beanFactory); // 测试时 registryProcessors 只有一个，即 ConfigurationClassPostProcessor
            invokeBeanFactoryPostProcessors(regularPostProcessors, beanFactory); // 测试时 regularPostProcessors 为空
        }

        ... // 省略其他处理
    }

    /*** Bean 定义注册后处理 */
    private static void invokeBeanDefinitionRegistryPostProcessors(
            Collection<? extends BeanDefinitionRegistryPostProcessor> postProcessors, 
            BeanDefinitionRegistry registry, ApplicationStartup applicationStartup
    ) {
        for (BeanDefinitionRegistryPostProcessor postProcessor : postProcessors) {
            ...
            postProcessor.postProcessBeanDefinitionRegistry(registry); // 调用后处理方法
            ...
        }
    }
```

- `org.springframework.context.annotation.ConfigurationClassPostProcessor`
```java
    /*** 后处理方法 */
    @Override
    public void postProcessBeanDefinitionRegistry(BeanDefinitionRegistry registry) {
        int registryId = System.identityHashCode(registry);
        ... // 省略重复处理的校验
        this.registriesPostProcessed.add(registryId);

        processConfigBeanDefinitions(registry); // 后处理
    }

    // 后处理
    public void processConfigBeanDefinitions(BeanDefinitionRegistry registry) {
        List<BeanDefinitionHolder> configCandidates = new ArrayList<>(); // 记录要处理的 @Configuration 集合
        String[] candidateNames = registry.getBeanDefinitionNames();

        ... // 省略查找 @Configuration 类的处理

        // Parse each @Configuration class
        ConfigurationClassParser parser = new ConfigurationClassParser(
                this.metadataReaderFactory, this.problemReporter, this.environment,
                this.resourceLoader, this.componentScanBeanNameGenerator, registry);

        Set<BeanDefinitionHolder> candidates = new LinkedHashSet<>(configCandidates); // 要处理的集合
        ...
        do { // 循环处理
            StartupStep processConfig = this.applicationStartup.start("spring.context.config-classes.parse");
            parser.parse(candidates); // 解析处理
            parser.validate();

            ...
            // reader 为 ConfigurationClassBeanDefinitionReader 实例
            // 加载解析出的 Bean
            this.reader.loadBeanDefinitions(configClasses);
            ...

            candidates.clear();
            if (registry.getBeanDefinitionCount() > candidateNames.length) {
                String[] newCandidateNames = registry.getBeanDefinitionNames();
                ...
                for (String candidateName : newCandidateNames) {
                    if (!oldCandidateNames.contains(candidateName)) {
                        BeanDefinition bd = registry.getBeanDefinition(candidateName);
                        if (ConfigurationClassUtils.checkConfigurationClassCandidate(bd, this.metadataReaderFactory) &&
                                !alreadyParsedClasses.contains(bd.getBeanClassName())) {
                            candidates.add(new BeanDefinitionHolder(bd, candidateName)); // 添加到要处理的集合，以便循环处理
                        }
                    }
                }
                candidateNames = newCandidateNames;
            }
        }
        while (!candidates.isEmpty());

        ... // 省略其他处理
    }
```

- `org.springframework.context.annotation.ConfigurationClassParser`
```java
    /*** 解析配置类 */
    public void parse(Set<BeanDefinitionHolder> configCandidates) {
        for (BeanDefinitionHolder holder : configCandidates) {
            BeanDefinition bd = holder.getBeanDefinition();
            try {
                if (bd instanceof AnnotatedBeanDefinition annotatedBeanDef) {
                    parse(annotatedBeanDef.getMetadata(), holder.getBeanName()); // 测试进入此分支
                }
                else if (bd instanceof AbstractBeanDefinition abstractBeanDef && abstractBeanDef.hasBeanClass()) {
                    parse(abstractBeanDef.getBeanClass(), holder.getBeanName());
                }
                else {
                    parse(bd.getBeanClassName(), holder.getBeanName());
                }
            }
            ... // 省略 catch 语句
        }

        this.deferredImportSelectorHandler.process();
    }

    // 解析配置类
    protected final void parse(AnnotationMetadata metadata, String beanName) throws IOException {
        processConfigurationClass(new ConfigurationClass(metadata, beanName), DEFAULT_EXCLUSION_FILTER);
    }

    protected void processConfigurationClass(ConfigurationClass configClass, Predicate<String> filter) throws IOException {
        if (this.conditionEvaluator.shouldSkip(configClass.getMetadata(), ConfigurationPhase.PARSE_CONFIGURATION)) {
            return; // 判断是否满足条件（@Conditional），不满足条件（shouldSkip 方法返回 true），则跳过（直接返回不处理）
        }

        ConfigurationClass existingClass = this.configurationClasses.get(configClass);
        if (existingClass != null) {
            ... // 省略已存在的处理
        }

        // Recursively process the configuration class and its superclass hierarchy.
        SourceClass sourceClass = asSourceClass(configClass, filter);
        do {
            // 处理配置类，即处理 @PropertySource @ComponentScan @ImportResource @Import 等注解
            //   会递归调用：解析出相关的 Bean 定义，以便后面加载
            sourceClass = doProcessConfigurationClass(configClass, sourceClass, filter);
        }
        while (sourceClass != null);

        this.configurationClasses.put(configClass, configClass);
    }
```

- `org.springframework.context.annotation.ConditionEvaluator`
```java
    /*** 判断是不是应该跳过，不加载配置类 */
    public boolean shouldSkip(@Nullable AnnotatedTypeMetadata metadata, @Nullable ConfigurationPhase phase) {
        if (metadata == null || !metadata.isAnnotated(Conditional.class.getName())) {
            return false; // 没有 @Conditional 注解的配置，不跳过，直接加载
        }

        if (phase == null) { // 上下文刷新时，参数 phase 为 PARSE_CONFIGURATION
            if (metadata instanceof AnnotationMetadata annotationMetadata &&
                    ConfigurationClassUtils.isConfigurationCandidate(annotationMetadata)) {
                return shouldSkip(metadata, ConfigurationPhase.PARSE_CONFIGURATION);
            }
            return shouldSkip(metadata, ConfigurationPhase.REGISTER_BEAN);
        }

        // 解析出条件类
        List<Condition> conditions = new ArrayList<>();
        for (String[] conditionClasses : getConditionClasses(metadata)) {
            for (String conditionClass : conditionClasses) {
                Condition condition = getCondition(conditionClass, this.context.getClassLoader());
                conditions.add(condition);
            }
        }

        AnnotationAwareOrderComparator.sort(conditions);

        for (Condition condition : conditions) {
            ConfigurationPhase requiredPhase = null;
            if (condition instanceof ConfigurationCondition configurationCondition) {
                requiredPhase = configurationCondition.getConfigurationPhase();
            }
            if ((requiredPhase == null || requiredPhase == phase) && !condition.matches(this.context, metadata)) {
                return true; // 只要用一个条件没匹配（调用 matches 方法）过，就应跳过处理
            }
        }

        return false;
    }
```

- `org.springframework.context.annotation.ConfigurationClassBeanDefinitionReader`
```java
    /*** 根据配置类加载 Bean */
    public void loadBeanDefinitions(Set<ConfigurationClass> configurationModel) {
        TrackedConditionEvaluator trackedConditionEvaluator = new TrackedConditionEvaluator();
        for (ConfigurationClass configClass : configurationModel) {
            loadBeanDefinitionsForConfigurationClass(configClass, trackedConditionEvaluator);
        }
    }
    
    // 加载 Bean 定义
    private void loadBeanDefinitionsForConfigurationClass(
            ConfigurationClass configClass, TrackedConditionEvaluator trackedConditionEvaluator) {

        ... // 省略跳过的处理

        if (configClass.isImported()) {
            registerBeanDefinitionForImportedConfigurationClass(configClass);
        }
        for (BeanMethod beanMethod : configClass.getBeanMethods()) {
            loadBeanDefinitionsForBeanMethod(beanMethod); // 循环加载配置类里面定义 Bean 的方法（有 @Bean 注解的方法）
        }

        loadBeanDefinitionsFromImportedResources(configClass.getImportedResources()); // 处理 @ImportResource
        loadBeanDefinitionsFromRegistrars(configClass.getImportBeanDefinitionRegistrars()); // 处理 @Import 导入的 Bean
    }

    // 加载 @Bean 注解的方法
    private void loadBeanDefinitionsForBeanMethod(BeanMethod beanMethod) {
        ConfigurationClass configClass = beanMethod.getConfigurationClass();
        MethodMetadata metadata = beanMethod.getMetadata();
        String methodName = metadata.getMethodName();

        ... // 省略是否应跳过的处理

        ... // 省略别名处理

        ... // 省略已存在的处理

        // 创建 Bean 定义
        ConfigurationClassBeanDefinition beanDef = new ConfigurationClassBeanDefinition(configClass, metadata, beanName);
        beanDef.setSource(this.sourceExtractor.extractSource(metadata, configClass.getResource()));

        ... // 省略 beanDef 的其他填充

        // Replace the original bean definition with the target one, if necessary
        BeanDefinition beanDefToRegister = beanDef;
        ... // 省略 @Scope 处理

        ... // 省略 log
        this.registry.registerBeanDefinition(beanName, beanDefToRegister); // 注册 bean
    }
```