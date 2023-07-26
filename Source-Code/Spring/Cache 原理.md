## 参考
- https://www.cnblogs.com/bjlhx/p/9168078.html


## 单元测试
- 参考：`org.springframework.cache.CacheReproTests`
```java
	@Configuration
	@EnableCaching // 启用缓存
	public static class Spr11124Config {
		@Bean
		public CacheManager cacheManager() {
			return new ConcurrentMapCacheManager();
		}
        ...
	}
```


## 原理
- `org.springframework.cache.annotation.EnableCaching`
```java
... // 省略其他元注解
@Import(CachingConfigurationSelector.class) // 导入配置关键类
public @interface EnableCaching {
    /*** 是否使用 CGLib 子类代理，此会影响全局代理方式。默认不使用 */
    boolean proxyTargetClass() default false;

    /*** 代理方式。默认使用 JDK 动态代理 */
    AdviceMode mode() default AdviceMode.PROXY;

    /*** 切面顺序。默认最低级 */
	int order() default Ordered.LOWEST_PRECEDENCE;
}
```

- `org.springframework.cache.annotation.CachingConfigurationSelector`
```java
public class CachingConfigurationSelector extends AdviceModeImportSelector<EnableCaching> {
	@Override // 实现父类抽象方法
	public String[] selectImports(AdviceMode adviceMode) {
		return switch (adviceMode) {
			case PROXY -> getProxyImports(); // JDK 方式
			case ASPECTJ -> getAspectJImports();
		};
	}

    /*** 要导入的类 */
	private String[] getProxyImports() {
		List<String> result = new ArrayList<>(3);
		result.add(AutoProxyRegistrar.class.getName());
		result.add(ProxyCachingConfiguration.class.getName()); // 主要的配置
		if (jsr107Present && jcacheImplPresent) {
			result.add(PROXY_JCACHE_CONFIGURATION_CLASS);
		}
		return StringUtils.toStringArray(result);
	}
}
```

- `org.springframework.cache.annotation.ProxyCachingConfiguration`
```java
@Configuration(proxyBeanMethods = false)
public class ProxyCachingConfiguration extends AbstractCachingConfiguration {

	@Bean // 注解过滤器（主要用于获取注解里面的属性 CacheOperation）
	public CacheOperationSource cacheOperationSource() {
		return new AnnotationCacheOperationSource(false);
	}

	@Bean // AOP 拦截器，相当于增强
	public CacheInterceptor cacheInterceptor(CacheOperationSource cacheOperationSource) {
		CacheInterceptor interceptor = new CacheInterceptor();
		...
		interceptor.setCacheOperationSource(cacheOperationSource);
		return interceptor;
	}

    // 相当于定义切面
	@Bean(name = CacheManagementConfigUtils.CACHE_ADVISOR_BEAN_NAME)
	public BeanFactoryCacheOperationSourceAdvisor cacheAdvisor(
			CacheOperationSource cacheOperationSource, CacheInterceptor cacheInterceptor) {

		BeanFactoryCacheOperationSourceAdvisor advisor = new BeanFactoryCacheOperationSourceAdvisor();
		advisor.setCacheOperationSource(cacheOperationSource);
		advisor.setAdvice(cacheInterceptor);
		...
		return advisor;
	}

}
```