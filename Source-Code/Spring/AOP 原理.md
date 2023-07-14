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
- `org.springframework.aop.framework.DefaultAopProxyFactory` 创建 AOP 代理
- `org.springframework.aop.framework.ProxyCreatorSupport` 调用代理工厂创建代理
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
  - 即是 Bean 后处理器，又继承了 `ProxyCreatorSupport`

![UML](https://s1.ax1x.com/2023/07/14/pC4Jzp4.png)