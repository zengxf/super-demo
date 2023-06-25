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
						getBean(beanName); // 调用父类方法，实例化
					}
				}
				else {
					getBean(beanName); // 调用父类方法，实例化
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

		String beanName = transformedBeanName(name);
		Object beanInstance;
        ...
		Object sharedInstance = getSingleton(beanName);
		if (sharedInstance != null && args == null) {
			...
			beanInstance = getObjectForBeanInstance(sharedInstance, name, beanName, null);
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
				return (T) parentBeanFactory.getBean(nameToLookup); // 父类处理
			}

			if (!typeCheckOnly) {
				markBeanAsCreated(beanName); // 标识为已创建
			}

			...
			try {
                ...
				RootBeanDefinition mbd = getMergedLocalBeanDefinition(beanName);
				checkMergedBeanDefinition(mbd, beanName, args);

				// Guarantee initialization of beans that the current bean depends on.
				String[] dependsOn = mbd.getDependsOn();
				if (dependsOn != null) {
					for (String dep : dependsOn) {
						if (isDependent(beanName, dep)) {
							throw new BeanCreationException(mbd.getResourceDescription(), beanName,
									"Circular depends-on relationship between '" + beanName + "' and '" + dep + "'");
						}
						registerDependentBean(dep, beanName);
						try {
							getBean(dep);
						}
						catch (NoSuchBeanDefinitionException ex) {
							throw new BeanCreationException(mbd.getResourceDescription(), beanName,
									"'" + beanName + "' depends on missing bean '" + dep + "'", ex);
						}
					}
				}

				// Create bean instance.
				if (mbd.isSingleton()) {
					sharedInstance = getSingleton(beanName, () -> {
						try {
							return createBean(beanName, mbd, args);
						}
						catch (BeansException ex) {
							// Explicitly remove instance from singleton cache: It might have been put there
							// eagerly by the creation process, to allow for circular reference resolution.
							// Also remove any beans that received a temporary reference to the bean.
							destroySingleton(beanName);
							throw ex;
						}
					});
					beanInstance = getObjectForBeanInstance(sharedInstance, name, beanName, mbd);
				}

				else if (mbd.isPrototype()) {
					// It's a prototype -> create a new instance.
					Object prototypeInstance = null;
					try {
						beforePrototypeCreation(beanName);
						prototypeInstance = createBean(beanName, mbd, args);
					}
					finally {
						afterPrototypeCreation(beanName);
					}
					beanInstance = getObjectForBeanInstance(prototypeInstance, name, beanName, mbd);
				}

				else {
					String scopeName = mbd.getScope();
					if (!StringUtils.hasLength(scopeName)) {
						throw new IllegalStateException("No scope name defined for bean '" + beanName + "'");
					}
					Scope scope = this.scopes.get(scopeName);
					if (scope == null) {
						throw new IllegalStateException("No Scope registered for scope name '" + scopeName + "'");
					}
					try {
						Object scopedInstance = scope.get(beanName, () -> {
							beforePrototypeCreation(beanName);
							try {
								return createBean(beanName, mbd, args);
							}
							finally {
								afterPrototypeCreation(beanName);
							}
						});
						beanInstance = getObjectForBeanInstance(scopedInstance, name, beanName, mbd);
					}
					catch (IllegalStateException ex) {
						throw new ScopeNotActiveException(beanName, scopeName, ex);
					}
				}
			}
			catch (BeansException ex) {
				...
				cleanupAfterBeanCreationFailure(beanName);
				throw ex;
			}
			...
		}

		return adaptBeanInstance(name, beanInstance, requiredType);
	}
```