## 参考
- 概念介绍 https://juejin.cn/post/6965732777962668062
- 原理介绍 https://mrbird.cc/深入理解Spring-AOP原理.html

## 介绍
- AOP **分为静态 AOP 和动态 AOP**
  - **静态 AOP 是指 AspectJ 实现的 AOP**，其将切面代码直接编译到 Java 类文件中
  - 动态 AOP 是指将切面代码进行动态织入实现的 AOP
    - **Spring 的 AOP 为动态 AOP**，实现的技术为：JDK 动态代理和 CGLib(Code Generate Libary 字节码生成)

## 关键类
- `org.springframework.context.annotation.EnableAspectJAutoProxy` 启用注解
- `org.springframework.aop.framework.DefaultAopProxyFactory` AOP 代理工厂
- `org.springframework.aop.framework.ProxyCreatorSupport` 调用工厂创建代理
- `org.springframework.aop.aspectj.annotation.AnnotationAwareAspectJAutoProxyCreator` 默认的创建者

## 原理
- Spring-Boot 里面 `AopAutoConfiguration` 会对 `EnableAspectJAutoProxy` 进行启用
```java
// org.springframework.boot.autoconfigure.aop.AopAutoConfiguration
@Configuration(proxyBeanMethods = false)
@ConditionalOnProperty(prefix = "spring.aop", name = "auto", havingValue = "true", matchIfMissing = true)
public class AopAutoConfiguration {
	@Configuration(proxyBeanMethods = false)
	@ConditionalOnClass(Advice.class)
	static class AspectJAutoProxyingConfiguration {
        ... // JDK 代理配置
		@Configuration(proxyBeanMethods = false)
		@EnableAspectJAutoProxy(proxyTargetClass = true) // 在此启用
		@ConditionalOnProperty(prefix = "spring.aop", name = "proxy-target-class", havingValue = "true",
				matchIfMissing = true)
		static class CglibAutoProxyConfiguration {

		}
    }
    ... // 其他代理配置
}
```

- `org.springframework.context.annotation.EnableAspectJAutoProxy`
```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Import(AspectJAutoProxyRegistrar.class) // 导入 AspectJAutoProxyRegistrar
public @interface EnableAspectJAutoProxy {
    ...
}
```

- `org.springframework.context.annotation.AspectJAutoProxyRegistrar`
```java
class AspectJAutoProxyRegistrar implements ImportBeanDefinitionRegistrar {

	@Override
	public void registerBeanDefinitions(
			AnnotationMetadata importingClassMetadata, BeanDefinitionRegistry registry) {

		AopConfigUtils.registerAspectJAnnotationAutoProxyCreatorIfNecessary(registry); // 注册代理创建者

		... // 根据注解 @EnableAspectJAutoProxy 的相关配置设置代理创建者属性
	}

}
```

- `org.springframework.aop.config.AopConfigUtils`
```java
	@Nullable
	public static BeanDefinition registerAspectJAnnotationAutoProxyCreatorIfNecessary(BeanDefinitionRegistry registry) {
		return registerAspectJAnnotationAutoProxyCreatorIfNecessary(registry, null);
	}

	@Nullable
	public static BeanDefinition registerAspectJAnnotationAutoProxyCreatorIfNecessary(
			BeanDefinitionRegistry registry, @Nullable Object source) {

		// 使用 AnnotationAwareAspectJAutoProxyCreator 作为创建者
		return registerOrEscalateApcAsRequired(AnnotationAwareAspectJAutoProxyCreator.class, registry, source);
	}

	@Nullable
	private static BeanDefinition registerOrEscalateApcAsRequired(
			Class<?> cls, BeanDefinitionRegistry registry, @Nullable Object source) {

		...

		RootBeanDefinition beanDefinition = new RootBeanDefinition(cls);
		beanDefinition.setSource(source);
		beanDefinition.getPropertyValues().add("order", Ordered.HIGHEST_PRECEDENCE);
		beanDefinition.setRole(BeanDefinition.ROLE_INFRASTRUCTURE);
		registry.registerBeanDefinition(AUTO_PROXY_CREATOR_BEAN_NAME, beanDefinition); // 注册 Bean 定义
		return beanDefinition;
	}
```

- `org.springframework.aop.aspectj.annotation.AnnotationAwareAspectJAutoProxyCreator`
  - **是 Bean 后处理器**

![UML](https://s1.ax1x.com/2023/07/14/pC4Jzp4.png)


---
### 调用链路
- `org.springframework.aop.framework.autoproxy.AbstractAutoProxyCreator`
  - 被 `org.springframework.aop.aspectj.annotation.AnnotationAwareAspectJAutoProxyCreator` 继承
```java
	/*** 后处理：Bean 实例化前处理 */
	@Override
	public Object postProcessBeforeInstantiation(Class<?> beanClass, String beanName) {
		Object cacheKey = getCacheKey(beanClass, beanName);
		...
		TargetSource targetSource = getCustomTargetSource(beanClass, beanName);
		if (targetSource != null) {
			...
			// 获取通知者（相当于拦截器）
			Object[] specificInterceptors = getAdvicesAndAdvisorsForBean(beanClass, beanName, targetSource);
			Object proxy = createProxy(beanClass, beanName, specificInterceptors, targetSource); // 创建代理
			this.proxyTypes.put(cacheKey, proxy.getClass());
			return proxy;
		}

		return null;
	}

	/*** 创建代理 */
	protected Object createProxy(Class<?> beanClass, @Nullable String beanName,
			@Nullable Object[] specificInterceptors, TargetSource targetSource) {

		return buildProxy(beanClass, beanName, specificInterceptors, targetSource, false);
	}

	/*** 构建代理 */
	private Object buildProxy(Class<?> beanClass, @Nullable String beanName,
			@Nullable Object[] specificInterceptors, TargetSource targetSource, boolean classOnly) {
		...
		ProxyFactory proxyFactory = new ProxyFactory(); // 其父类是 ProxyCreatorSupport
		...

		Advisor[] advisors = buildAdvisors(beanName, specificInterceptors);
		proxyFactory.addAdvisors(advisors);
		proxyFactory.setTargetSource(targetSource);

		...

		ClassLoader classLoader = getProxyClassLoader();
		...
		// classOnly 为 false，会调用 getProxy 方法
		return (classOnly ? proxyFactory.getProxyClass(classLoader) : proxyFactory.getProxy(classLoader));
	}
```

- `org.springframework.aop.framework.autoproxy.AbstractAdvisorAutoProxyCreator`
```java
	/*** 查找给定 Bean 的通知者 */
	@Override
	@Nullable
	protected Object[] getAdvicesAndAdvisorsForBean(
			Class<?> beanClass, String beanName, @Nullable TargetSource targetSource) {

		List<Advisor> advisors = findEligibleAdvisors(beanClass, beanName); // 查看合格的通知者
		if (advisors.isEmpty()) {
			return DO_NOT_PROXY;
		}
		return advisors.toArray();
	}

	/*** 查看合格的通知者(Advisor) */
	protected List<Advisor> findEligibleAdvisors(Class<?> beanClass, String beanName) {
		List<Advisor> candidateAdvisors = findCandidateAdvisors(); // 查找通知者
		List<Advisor> eligibleAdvisors = findAdvisorsThatCanApply(candidateAdvisors, beanClass, beanName); // 过滤
		extendAdvisors(eligibleAdvisors);
		if (!eligibleAdvisors.isEmpty()) {
			eligibleAdvisors = sortAdvisors(eligibleAdvisors); // 排序
		}
		return eligibleAdvisors;
	}
```

- `org.springframework.aop.aspectj.annotation.AnnotationAwareAspectJAutoProxyCreator`
```java
	/*** 查找通知者(Advisor) */
	@Override
	protected List<Advisor> findCandidateAdvisors() {
		// 添加父类的
		List<Advisor> advisors = super.findCandidateAdvisors();
		// 添加构建器的
		if (this.aspectJAdvisorsBuilder != null) {
			advisors.addAll(this.aspectJAdvisorsBuilder.buildAspectJAdvisors());
		}
		return advisors;
	}
```

- `org.springframework.aop.framework.ProxyFactory`
```java
	/*** 创建代理 */
	public Object getProxy(@Nullable ClassLoader classLoader) {
		return createAopProxy().getProxy(classLoader);
	}

	// 父类：org.springframework.aop.framework.ProxyCreatorSupport

	/*** ProxyCreatorSupport：创建 AOP 代理 */
	protected final synchronized AopProxy createAopProxy() {
		...
		return getAopProxyFactory().createAopProxy(this); // 使用 DefaultAopProxyFactory
	}

	public AopProxyFactory getAopProxyFactory() {
		return this.aopProxyFactory; // （一般）返回默认的工厂
	}

	public ProxyCreatorSupport() {
		this.aopProxyFactory = new DefaultAopProxyFactory(); // 构造器里：使用的是默认的工厂
	}
```

- `org.springframework.aop.framework.DefaultAopProxyFactory`
```java
	/*** 创建 AopProxy */
	@Override
	public AopProxy createAopProxy(AdvisedSupport config) throws AopConfigException {
		if (config.isOptimize() || config.isProxyTargetClass() || hasNoUserSuppliedProxyInterfaces(config)) {
			Class<?> targetClass = config.getTargetClass();
			... // 空校验
			if (targetClass.isInterface() || Proxy.isProxyClass(targetClass) || ClassUtils.isLambdaClass(targetClass)) {
				return new JdkDynamicAopProxy(config); 	// 是接口等等，使用 JDK 动态代理
			}
			return new ObjenesisCglibAopProxy(config); 	// 否则，使用 CGLib 创建代理
		}
		else {
			return new JdkDynamicAopProxy(config); 		// 默认使用 JDK 动态代理
		}
	}
```