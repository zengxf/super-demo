## 简介
- 实现类为 `org.springframework.beans.factory.support.DefaultListableBeanFactory`
- 方法为 `#preInstantiateSingletons()`
  - 其在上下文刷新时，调用

## 源码
- `org.springframework.beans.factory.support.DefaultListableBeanFactory`
```java
    /*** 实例化所有的 Bean */
	@Override
	public void preInstantiateSingletons() throws BeansException {
		...
		List<String> beanNames = new ArrayList<>(this.beanDefinitionNames);
		// 触发 Bean 实例化
		for (String beanName : beanNames) {
			RootBeanDefinition bd = getMergedLocalBeanDefinition(beanName); // 获取 Bean 定义
			if (!bd.isAbstract() && bd.isSingleton() && !bd.isLazyInit()) { // 不是抽象、是单例、不是懒加载
				if (isFactoryBean(beanName)) {
					Object bean = getBean(FACTORY_BEAN_PREFIX + beanName);
					if (bean instanceof SmartFactoryBean<?> smartFactoryBean && smartFactoryBean.isEagerInit()) {
						getBean(beanName);  // 实例化（父类 AbstractBeanFactory 的方法）
					}
				}
				else {
					getBean(beanName);      // 实例化（同上）
				}
			}
		}
        ...
	}
```

- `org.springframework.beans.factory.support.AbstractBeanFactory`
```java
    /*** 实例化 */
	@Override
	public Object getBean(String name) throws BeansException {
		return doGetBean(name, null, null, false);
	}

    // 实例化
	protected <T> T doGetBean(
			String name, @Nullable Class<T> requiredType, @Nullable Object[] args, boolean typeCheckOnly)
			throws BeansException {

		String beanName = transformedBeanName(name); // 转换成标准 Bean 名称
		Object beanInstance;
        ...
		Object sharedInstance = getSingleton(beanName); // 获取单例（父类 DefaultSingletonBeanRegistry 的方法）
		if (sharedInstance != null && args == null) {
			...
			beanInstance = getObjectForBeanInstance(sharedInstance, name, beanName, null); // 获取实例对象
		}
		else {
			// 创建中，可能是循环引用，则报出异常
			if (isPrototypeCurrentlyInCreation(beanName)) {
				throw new BeanCurrentlyInCreationException(beanName);
			}

			// 类似双亲委派机制，父类处理
			BeanFactory parentBeanFactory = getParentBeanFactory();
			if (parentBeanFactory != null && !containsBeanDefinition(beanName)) {
				String nameToLookup = originalBeanName(name);
				...
				return (T) parentBeanFactory.getBean(nameToLookup); // 父类去实例化
			}

			...
            
			try {
                ...
				RootBeanDefinition mbd = getMergedLocalBeanDefinition(beanName); // 获取 Bean 定义
                ...
				String[] dependsOn = mbd.getDependsOn(); // 获取 Bean 的依赖项
				if (dependsOn != null) {
					for (String dep : dependsOn) {
						if (isDependent(beanName, dep)) { // 存在循环依赖，抛异常
							throw new BeanCreationException(...);
						}
						registerDependentBean(dep, beanName);
						try {
							getBean(dep); // 实例化依赖的 Bean
						}
						...
					}
				}

				if (mbd.isSingleton()) { // 单例模式
					sharedInstance = getSingleton(beanName, () -> { // 获取单例（父类 DefaultSingletonBeanRegistry 方法），会缓存
						try {
							return createBean(beanName, mbd, args); // 缓存没有才创建
						}
						... // 创建出异常，则销毁
					});
					beanInstance = getObjectForBeanInstance(sharedInstance, name, beanName, mbd); // 获取实例对象
				}
				else if (mbd.isPrototype()) { // 原型模式
					Object prototypeInstance = null;
					try {
                        ...
						prototypeInstance = createBean(beanName, mbd, args); // 每次都创建
					}
					...
					beanInstance = getObjectForBeanInstance(prototypeInstance, name, beanName, mbd); // 获取实例对象
				}
				...
			}
			...
		}

		return adaptBeanInstance(name, beanInstance, requiredType); // 转换成的类型
	}

    // 获取实例对象
    protected Object getObjectForBeanInstance(
			Object beanInstance, String name, String beanName, @Nullable RootBeanDefinition mbd) {

		// 名称是工厂 Bean 名格式（以 & 开头）
		if (BeanFactoryUtils.isFactoryDereference(name)) {
			...
			if (!(beanInstance instanceof FactoryBean)) { // 不是其子类，则抛出异常
				throw new BeanIsNotAFactoryException(beanName, beanInstance.getClass());
			}
			...
			return beanInstance; // 直接返回
		}

		// 如果是普通 Bean 则直接返回
		if (!(beanInstance instanceof FactoryBean<?> factoryBean)) {
			return beanInstance;
		}

		Object object = null;
		...
		if (object == null) {
			// 工厂创建实例，缓存并返回
			...
			object = getObjectFromFactoryBean(factoryBean, beanName, !synthetic); // 从工厂获取实例（父类 FactoryBeanRegistrySupport 的方法）
		}
		return object;
	}

    // 创建 Bean 实例。实现类为： AbstractAutowireCapableBeanFactory
	protected abstract Object createBean(String beanName, RootBeanDefinition mbd, @Nullable Object[] args)
			throws BeanCreationException;
```

- `org.springframework.beans.factory.support.DefaultSingletonBeanRegistry`
```java
    /*** 获取单例 */
	@Override
	@Nullable
	public Object getSingleton(String beanName) {
		return getSingleton(beanName, true); // 允许早期引用
	}

    // 获取单例
	@Nullable
	protected Object getSingleton(String beanName, boolean allowEarlyReference) {
		Object singletonObject = this.singletonObjects.get(beanName);
		if (singletonObject == null && isSingletonCurrentlyInCreation(beanName)) { // 为空且当前正在创建
			singletonObject = this.earlySingletonObjects.get(beanName); // 从 2 级缓存中取
			if (singletonObject == null && allowEarlyReference) { // 还为空且允许早期引用
				synchronized (this.singletonObjects) { // 加锁，保证一致性
					singletonObject = this.singletonObjects.get(beanName); // 再获取一次
					if (singletonObject == null) {
						singletonObject = this.earlySingletonObjects.get(beanName); // 为空，再从 2 级缓存中取
						if (singletonObject == null) {
							ObjectFactory<?> singletonFactory = this.singletonFactories.get(beanName); // 从工厂里面取
							if (singletonFactory != null) {
								singletonObject = singletonFactory.getObject(); // 工厂创建并返回
								this.earlySingletonObjects.put(beanName, singletonObject); // 加入到 2 级缓存
								this.singletonFactories.remove(beanName);
							}
						}
					}
				}
			}
		}
		return singletonObject;
	}
```

- `org.springframework.beans.factory.support.FactoryBeanRegistrySupport`
```java
    // 从工厂获取实例对象
	protected Object getObjectFromFactoryBean(FactoryBean<?> factory, String beanName, boolean shouldPostProcess) {
		if (factory.isSingleton() && containsSingleton(beanName)) { // 是单例
			synchronized (getSingletonMutex()) { // 加锁（父类 DefaultSingletonBeanRegistry 方法）
				Object object = this.factoryBeanObjectCache.get(beanName); // 先从缓存中获取
				if (object == null) {
					object = doGetObjectFromFactoryBean(factory, beanName); // 调用 factory.getObject() 创建实例
                    ...
					else {
						if (shouldPostProcess) { // 需要后处理
							... // 创建前做下校验
							try {
                                // 对象后处理，默认直接返回
                                // 子类 AbstractAutowireCapableBeanFactory 会重写
								object = postProcessObjectFromFactoryBean(object, beanName);
							}
                            ...  // 创建后做下校验
						}
						if (containsSingleton(beanName)) { // 包含单例，则缓存
							this.factoryBeanObjectCache.put(beanName, object);
						}
					}
				}
				return object;
			}
		}
		else {
			Object object = doGetObjectFromFactoryBean(factory, beanName); // 直接调用 factory.getObject() 创建实例
			if (shouldPostProcess) { // 需要后处理
                ...
				object = postProcessObjectFromFactoryBean(object, beanName);
				...
			}
			return object;
		}
	}
```

- `org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory`
```java
    // 创建 Bean 实例
	@Override
	protected Object createBean(String beanName, RootBeanDefinition mbd, @Nullable Object[] args)
			throws BeanCreationException {

		...
		RootBeanDefinition mbdToUse = mbd;

		...

		try {
			// 先让后处理器 BeanPostProcessors 处理（可能有缓存等）
			Object bean = resolveBeforeInstantiation(beanName, mbdToUse);
			if (bean != null) {
				return bean;
			}
		}
		... // 传递异常

		try {
			Object beanInstance = doCreateBean(beanName, mbdToUse, args); // 创建实例
			...
			return beanInstance;
		}
		... // 传递异常
	}

    // 创建实例（填充属性、初始化等处理）
	protected Object doCreateBean(String beanName, RootBeanDefinition mbd, @Nullable Object[] args)
			throws BeanCreationException {

		BeanWrapper instanceWrapper = null;
		...
		if (instanceWrapper == null) {
			instanceWrapper = createBeanInstance(beanName, mbd, args);
		}
		Object bean = instanceWrapper.getWrappedInstance();
		Class<?> beanType = instanceWrapper.getWrappedClass();
        ...
		synchronized (mbd.postProcessingLock) {
			if (!mbd.postProcessed) {
				try {
					applyMergedBeanDefinitionPostProcessors(mbd, beanType, beanName);
				}
				... // 传递异常
			}
		}

		// Eagerly cache singletons to be able to resolve circular references
		// even when triggered by lifecycle interfaces like BeanFactoryAware.
		boolean earlySingletonExposure = (mbd.isSingleton() && this.allowCircularReferences &&
				isSingletonCurrentlyInCreation(beanName));
		if (earlySingletonExposure) {
			...
			addSingletonFactory(beanName, () -> getEarlyBeanReference(beanName, mbd, bean));
		}

		// Initialize the bean instance.
		Object exposedObject = bean;
		try {
			populateBean(beanName, mbd, instanceWrapper);
			exposedObject = initializeBean(beanName, exposedObject, mbd);
		}
		... // 传递异常

		if (earlySingletonExposure) {
			Object earlySingletonReference = getSingleton(beanName, false);
			if (earlySingletonReference != null) {
				if (exposedObject == bean) {
					exposedObject = earlySingletonReference;
				}
				else if (!this.allowRawInjectionDespiteWrapping && hasDependentBean(beanName)) {
					String[] dependentBeans = getDependentBeans(beanName);
					Set<String> actualDependentBeans = new LinkedHashSet<>(dependentBeans.length);
					for (String dependentBean : dependentBeans) {
						if (!removeSingletonIfCreatedForTypeCheckOnly(dependentBean)) {
							actualDependentBeans.add(dependentBean);
						}
					}
					... // 校验
				}
			}
		}

		// Register bean as disposable.
		try {
			registerDisposableBeanIfNecessary(beanName, bean, mbd);
		}
		... // 传递异常

		return exposedObject;
	}
```