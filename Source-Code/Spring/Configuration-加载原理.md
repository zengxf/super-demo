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

			candidates.clear();
			if (registry.getBeanDefinitionCount() > candidateNames.length) {
				String[] newCandidateNames = registry.getBeanDefinitionNames();
				...
				for (String candidateName : newCandidateNames) {
					if (!oldCandidateNames.contains(candidateName)) {
						BeanDefinition bd = registry.getBeanDefinition(candidateName);
						if (ConfigurationClassUtils.checkConfigurationClassCandidate(bd, this.metadataReaderFactory) &&
								!alreadyParsedClasses.contains(bd.getBeanClassName())) {
							candidates.add(new BeanDefinitionHolder(bd, candidateName)); // 添加到要处理的集合
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