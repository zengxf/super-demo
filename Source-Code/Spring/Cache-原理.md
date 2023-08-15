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

- `org.springframework.cache.interceptor.CacheInterceptor`
```java
    @Override
    @Nullable
    public Object invoke(final MethodInvocation invocation) throws Throwable {
        Method method = invocation.getMethod();
        // 相当于回调函数：调用真正的方法获取值
        CacheOperationInvoker aopAllianceInvoker = () -> {
            try {
                return invocation.proceed();
            }
            ... // 省略 catch
        };

        Object target = invocation.getThis();
        ...
        try {
            // 调用父类(CacheAspectSupport)方法
            return execute(aopAllianceInvoker, target, method, invocation.getArguments());
        }
        ... // 省略 catch
    }
```

- `org.springframework.cache.interceptor.CacheAspectSupport`
```java
    @Nullable
    protected Object execute(CacheOperationInvoker invoker, Object target, Method method, Object[] args) {
        if (this.initialized) { // 一般是初始好的，会进入 if 分支
            Class<?> targetClass = getTargetClass(target);
            CacheOperationSource cacheOperationSource = getCacheOperationSource();
            if (cacheOperationSource != null) {
                Collection<CacheOperation> operations = cacheOperationSource.getCacheOperations(method, targetClass);
                if (!CollectionUtils.isEmpty(operations)) { // 会进入此分支
                    return execute(invoker, method,
                            new CacheOperationContexts(operations, method, args, target, targetClass));
                }
            }
        }

        return invoker.invoke();
    }

    /*** 缓存处理的核心方法 */
    @Nullable
    private Object execute(final CacheOperationInvoker invoker, Method method, CacheOperationContexts contexts) {
        ... // 省略 sync 处理

        // 处理过期缓存
        processCacheEvicts(contexts.get(CacheEvictOperation.class), true,
                CacheOperationExpressionEvaluator.NO_RESULT);

        // 查找缓存
        Cache.ValueWrapper cacheHit = findCachedItem(contexts.get(CacheableOperation.class));

        List<CachePutRequest> cachePutRequests = new ArrayList<>();
        if (cacheHit == null) { // 没有缓存，则添加个 put 请求
            collectPutRequests(contexts.get(CacheableOperation.class),
                    CacheOperationExpressionEvaluator.NO_RESULT, cachePutRequests);
        }

        Object cacheValue;
        Object returnValue;

        if (cacheHit != null && !hasCachePut(contexts)) { // 有缓存，则直接返回缓存值
            cacheValue = cacheHit.get();
            returnValue = wrapCacheValue(method, cacheValue);
        }
        else { // 没缓存则直接调用原方法（有缓存但其他线程在 put 也会调用）
            returnValue = invokeOperation(invoker);
            cacheValue = unwrapReturnValue(returnValue);
        }

        collectPutRequests(contexts.get(CachePutOperation.class), cacheValue, cachePutRequests);

        // 将原谅法返回的值用于 put 请求：添加到缓存
        for (CachePutRequest cachePutRequest : cachePutRequests) {
            cachePutRequest.apply(cacheValue);
        }

        // 处理过期缓存
        processCacheEvicts(contexts.get(CacheEvictOperation.class), false, cacheValue);

        return returnValue;
    }
```