## 简介
- 实现类为 `org.springframework.context.support.AbstractApplicationContext`
- 方法为 `#refresh()`
- 作用：
  - **启动容器，实例化 Bean**

## 源码
- `org.springframework.context.support.AbstractApplicationContext`
```java
	@Override
	public void refresh() throws BeansException, IllegalStateException {
		synchronized (this.startupShutdownMonitor) {
            ...
			// 刷新前准备
			prepareRefresh();
			// 子类实现：创建 Bean 工厂，并返回
			ConfigurableListableBeanFactory beanFactory = obtainFreshBeanFactory();
            // 初始化 Bean 工厂：设置类加载器、常用 Bean 后处理器等
			prepareBeanFactory(beanFactory);
			try {
				// 钩子函数：给 Bean 工厂添加特定 Bean 后处理器。子类可重写
				postProcessBeanFactory(beanFactory);
				...
				// 调用所有的 Bean 工厂后处理器
				invokeBeanFactoryPostProcessors(beanFactory);
				// 添加（注册到 Bean 工厂的） Bean 后处理器
				registerBeanPostProcessors(beanFactory);
                ...

				// Initialize message source for this context.
				initMessageSource();

				// Initialize event multicaster for this context.
				initApplicationEventMulticaster();

				// Initialize other special beans in specific context subclasses.
				onRefresh();

				// Check for listener beans and register them.
				registerListeners();

				// Instantiate all remaining (non-lazy-init) singletons.
				finishBeanFactoryInitialization(beanFactory);

				// Last step: publish corresponding event.
				finishRefresh();
			}
			catch (BeansException ex) {
                ...
				destroyBeans(); // 如果刷新（启动）出错异常，则销毁 Bean
                ...
				throw ex;
			}
			...
		}
	}

    // 刷新前准备：初始化相关属性；校验环境变量
    protected void prepareRefresh() {
		...
		initPropertySources(); // 钩子函数：初始化属性源。子类可重写
		getEnvironment().validateRequiredProperties(); // 校验环境变量，校验不能为空的属性
        ...
		this.earlyApplicationListeners = new LinkedHashSet<>(this.applicationListeners); // 初始化
        ...
		this.earlyApplicationEvents = new LinkedHashSet<>(); // 初始化
	}

    // 调用所有的 Bean 工厂后处理器
	protected void invokeBeanFactoryPostProcessors(ConfigurableListableBeanFactory beanFactory) {
        // 委派调用（看不懂，表面上看没数据）
		PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors(beanFactory, getBeanFactoryPostProcessors());
        ...
	}

    // 添加 Bean 后处理器
	protected void registerBeanPostProcessors(ConfigurableListableBeanFactory beanFactory) {
        // 委派调用：实例化（注册到 Bean 工厂的）后处理器并添加到 Bean 工厂
		PostProcessorRegistrationDelegate.registerBeanPostProcessors(beanFactory, this);
	}
```