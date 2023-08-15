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
            // 刷新前准备：初始化相关属性；校验环境变量
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
                // 初始化消息源
                initMessageSource();
                // 初始化事件组播器
                initApplicationEventMulticaster();
                // 钩子函数，子类根据需要可重写
                onRefresh();
                // 注册事件监听器
                registerListeners();

                // 实例化剩余（非 lazy）单例
                finishBeanFactoryInitialization(beanFactory);
                
                // 刷新完成后处理：清缓存、发送刷新完成事件
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
        // 委派调用：实例化（注册到 Bean 工厂的）Bean 后处理器并添加到 Bean 工厂
        PostProcessorRegistrationDelegate.registerBeanPostProcessors(beanFactory, this);
    }

    // 初始化消息源
    protected void initMessageSource() {
        ConfigurableListableBeanFactory beanFactory = getBeanFactory();
        if (beanFactory.containsLocalBean(MESSAGE_SOURCE_BEAN_NAME)) { // 如果 Bean 工厂存在，就用其里面的
            this.messageSource = beanFactory.getBean(MESSAGE_SOURCE_BEAN_NAME, MessageSource.class); // 会初始化并返回
            ...
        }
        else { // 设置默认的消息源，并注册到 Bean 工厂
            DelegatingMessageSource dms = new DelegatingMessageSource();
            dms.setParentMessageSource(getInternalParentMessageSource());
            this.messageSource = dms;
            beanFactory.registerSingleton(MESSAGE_SOURCE_BEAN_NAME, this.messageSource);
            ...
        }
    }

    // 初始化事件组播器
    protected void initApplicationEventMulticaster() {
        ConfigurableListableBeanFactory beanFactory = getBeanFactory();
        if (beanFactory.containsLocalBean(APPLICATION_EVENT_MULTICASTER_BEAN_NAME)) { // 如果 Bean 工厂存在，就用其里面的
            this.applicationEventMulticaster =
                    beanFactory.getBean(APPLICATION_EVENT_MULTICASTER_BEAN_NAME, ApplicationEventMulticaster.class); // 会初始化并返回
            ...
        }
        else { // 设置默认的，并注册到 Bean 工厂
            this.applicationEventMulticaster = new SimpleApplicationEventMulticaster(beanFactory);
            beanFactory.registerSingleton(APPLICATION_EVENT_MULTICASTER_BEAN_NAME, this.applicationEventMulticaster);
            ...
        }
    }

    // 注册事件监听器；发送事件
    protected void registerListeners() {
        // 将监听器注册到事件组播器里面去
        for (ApplicationListener<?> listener : getApplicationListeners()) {
            getApplicationEventMulticaster().addApplicationListener(listener);
        }
        String[] listenerBeanNames = getBeanNamesForType(ApplicationListener.class, true, false);
        for (String listenerBeanName : listenerBeanNames) {
            getApplicationEventMulticaster().addApplicationListenerBean(listenerBeanName);
        }
        // 发送事件
        Set<ApplicationEvent> earlyEventsToProcess = this.earlyApplicationEvents;
        this.earlyApplicationEvents = null;
        if (!CollectionUtils.isEmpty(earlyEventsToProcess)) {
            for (ApplicationEvent earlyEvent : earlyEventsToProcess) {
                getApplicationEventMulticaster().multicastEvent(earlyEvent);
            }
        }
    }

    // 实例化剩余单例
    protected void finishBeanFactoryInitialization(ConfigurableListableBeanFactory beanFactory) {
        // 初始化转换器
        if (beanFactory.containsBean(CONVERSION_SERVICE_BEAN_NAME) &&
                beanFactory.isTypeMatch(CONVERSION_SERVICE_BEAN_NAME, ConversionService.class)) {
            beanFactory.setConversionService(
                    beanFactory.getBean(CONVERSION_SERVICE_BEAN_NAME, ConversionService.class));
        }
        ...
        // Bean 工厂实例化剩余单例
        beanFactory.preInstantiateSingletons();
    }

    // 刷新完成后处理：清缓存、发送刷新完成事件
    protected void finishRefresh() {
        // 清缓存
        clearResourceCaches();
        ...
        // 调用所有注册的 Lifecycle 的 start() 方法
        getLifecycleProcessor().onRefresh();
        // 发送刷新完成事件
        publishEvent(new ContextRefreshedEvent(this));
    }
```