# Seata-AOP-注解处理
- 处理 `@GlobalTransactional` 注解原理


---
## Spring-Boot-自动配置
- 模块：`seata-spring-boot-starter`
- `./META-INF/spring/*.AutoConfiguration.imports`
```js
io.seata.*.SeataAutoConfiguration // Seata 配置，ref: sign_c_010
...
```

- `io.seata.spring.boot.autoconfigure.SeataAutoConfiguration`
```java
// sign_c_010  Seata 配置
@ConditionalOnProperty(prefix = SEATA_PREFIX, name = "enabled", havingValue = "true", matchIfMissing = true)
...
public class SeataAutoConfiguration {

    // 创建全局事务扫描器 (注解 AOP 处理)，ref: sign_c_110
    @Bean
    ...
    @ConditionalOnMissingBean(GlobalTransactionScanner.class)
    public static GlobalTransactionScanner globalTransactionScanner(SeataProperties seataProperties, ...) {
        ...

        //set accessKey and secretKey
        GlobalTransactionScanner.setAccessKey(seataProperties.getAccessKey());
        GlobalTransactionScanner.setSecretKey(seataProperties.getSecretKey());

        return new GlobalTransactionScanner(..., seataProperties.getTxServiceGroup(), ...); // ref: sign_c_110
    }
}
```


---
## 注解处理器
- `io.seata.integration.tx.api.interceptor.handler.GlobalTransactionalInterceptorHandler`

### 处理器初始化调用栈
```js
// 可在 sign_cm_140 打断点，执行下面的打印
// new RuntimeException("栈跟踪").printStackTrace();

java.lang.RuntimeException: 栈跟踪
    at io.seata.*.handler.GlobalTransactionalInterceptorHandler.<init>(*Handler.java:118) // ref: sign_c_140 | sign_cm_140
    at io.seata.*.parser.GlobalTransactionalInterceptorParser.parserInterfaceToProxy(*Parser.java:54) // ref: sign_c_130 | sign_m_130
    at io.seata.*.parser.DefaultInterfaceParser.parserInterfaceToProxy(DefaultInterfaceParser.java:58) // ref: sign_c_120 | sign_m_120
    at io.seata.*.GlobalTransactionScanner.wrapIfNecessary(GlobalTransactionScanner.java:284) // ref: sign_c_110 | sign_m_110
    at org.springframework.aop.*.AbstractAutoProxyCreator.postProcessAfterInitialization(*Creator.java:293) // Spring Bean 后处理 (AOP 代理初始化处理)
    at org.springframework.beans.*.AbstractAutowireCapableBeanFactory.applyBeanPostProcessorsAfterInitialization(*Factory.java:455)
    at org.springframework.beans.*.AbstractAutowireCapableBeanFactory.initializeBean(*Factory.java:1808)
    at org.springframework.beans.*.AbstractAutowireCapableBeanFactory.doCreateBean(*Factory.java:620)
    at org.springframework.beans.*.AbstractAutowireCapableBeanFactory.createBean(*Factory.java:542)
```

### 处理器初始化原理
- `io.seata.spring.annotation.GlobalTransactionScanner`
```java
// sign_c_110  全局事务扫描器 (AOP 处理)
public class GlobalTransactionScanner extends AbstractAutoProxyCreator
        implements ConfigurationChangeListener, InitializingBean, ApplicationContextAware, DisposableBean 
{

    // sign_m_110
    @Override
    protected Object wrapIfNecessary(Object bean, String beanName, Object cacheKey) {
        ...

        try {
            synchronized (PROXYED_SET) {
                ...
                interceptor = null;
                ProxyInvocationHandler proxyInvocationHandler = DefaultInterfaceParser.get()
                    .parserInterfaceToProxy(bean, beanName); // 获取 Seata 拦截器，ref: sign_m_120
                ...

                // sign_cb_110 创建 AOP 拦截器，ref: sign_cm_210
                interceptor = new AdapterSpringSeataInterceptor(proxyInvocationHandler);

                if (!AopUtils.isAopProxy(bean)) {
                    bean = super.wrapIfNecessary(bean, beanName, cacheKey);
                } else {
                   ...
                }
                PROXYED_SET.add(beanName);
                return bean;
            }
        } ... // catch 
    }

    @Override // 返回给父类方法用，组装 AOP 拦截链
    protected Object[] getAdvicesAndAdvisorsForBean(Class beanClass, String beanName, ...) throws BeansException {
        return new Object[] { interceptor }; // 初始值来自： sign_cb_110
    }
}
```

- `io.seata.integration.tx.api.interceptor.parser.DefaultInterfaceParser`
```java
// sign_c_120  默认解析器 (可理解为对 SPI 的封装)
public class DefaultInterfaceParser implements InterfaceParser {

    // sign_m_120  获取 Seata 拦截器
    @Override
    public ProxyInvocationHandler parserInterfaceToProxy(Object target, String objectName) throws Exception {
        for (InterfaceParser interfaceParser : ALL_INTERFACE_PARSERS) {
            // 获取 Seata 拦截器，ref: sign_m_130
            ProxyInvocationHandler proxyInvocationHandler = interfaceParser.parserInterfaceToProxy(target, objectName);
            if (proxyInvocationHandler != null) {
                return proxyInvocationHandler;
            }
        }
        return null;
    }
}
```

- `io.seata.integration.tx.api.interceptor.parser.GlobalTransactionalInterceptorParser`
```java
// sign_c_130  全局事务拦截解析器 (SPI 默认提供此实现)
public class GlobalTransactionalInterceptorParser implements InterfaceParser {

    // sign_m_130  
    @Override
    public ProxyInvocationHandler parserInterfaceToProxy(Object target, String objectName) throws Exception {
        Class<?> serviceInterface = DefaultTargetClassParser.get().findTargetClass(target);
        Class<?>[] interfacesIfJdk = DefaultTargetClassParser.get().findInterfaces(target);

        if (existsAnnotation(serviceInterface) || existsAnnotation(interfacesIfJdk)) {
            // 获取 Seata 拦截器 (即：注解处理器)，ref: sign_cm_140
            ProxyInvocationHandler proxyInvocationHandler = new GlobalTransactionalInterceptorHandler(...);
            ConfigurationCache.addConfigListener(ConfigurationKeys.DISABLE_GLOBAL_TRANSACTION, ... proxyInvocationHandler);
            return proxyInvocationHandler;
        }

        return null;
    }
}
```

- `io.seata.integration.tx.api.interceptor.handler.GlobalTransactionalInterceptorHandler`
```java
// sign_c_140  注解处理器
public class GlobalTransactionalInterceptorHandler extends AbstractProxyInvocationHandler implements ConfigurationChangeListener {
    private final TransactionalTemplate transactionalTemplate = new TransactionalTemplate();
    private final GlobalLockTemplate globalLockTemplate = new GlobalLockTemplate();

    // sign_cm_140
    public GlobalTransactionalInterceptorHandler(FailureHandler failureHandler, Set<String> methodsToProxy) {
        this.failureHandler = failureHandler == null ? FailureHandlerHolder.getFailureHandler() : failureHandler;
        this.methodsToProxy = methodsToProxy;
        ...
    }
}
```


---
## AOP-事务处理
### 处理调用栈
```js
java.lang.RuntimeException: 栈跟踪
	at io.seata.*.handler.GlobalTransactionalInterceptorHandler.doInvoke(GlobalTransactionalInterceptorHandler.java:144)
	at io.seata.*.handler.AbstractProxyInvocationHandler.invoke(AbstractProxyInvocationHandler.java:35) // ref: sign_m_220
	at io.seata.spring.annotation.AdapterSpringSeataInterceptor.invoke(AdapterSpringSeataInterceptor.java:45) // ref: sign_m_210
	at org.springframework.aop.*.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:186) // Spring AOP 处理
	at org.springframework.aop.*.CglibAopProxy$CglibMethodInvocation.proceed(CglibAopProxy.java:763)
	at org.springframework.aop.*.CglibAopProxy$DynamicAdvisedInterceptor.intercept(CglibAopProxy.java:708)
	at org.apache.seata.service.impl.BusinessServiceImpl$$EnhancerBySpringCGLIB$$cb496675.purchase(<generated>) // demo 业务方法
	at org.apache.seata.SpringbootSeataApplication.lambda$main$0(SpringbootSeataApplication.java:20) // main 方法
	...
```

### 处理实现
- `io.seata.spring.annotation.AdapterSpringSeataInterceptor`
```java
// sign_c_210  AOP 拦截器
public class AdapterSpringSeataInterceptor implements MethodInterceptor, SeataInterceptor, Ordered {

    // sign_cm_210
    public AdapterSpringSeataInterceptor(ProxyInvocationHandler proxyInvocationHandler) {
        ...
        this.proxyInvocationHandler = proxyInvocationHandler;
    }

    // sign_m_210  AOP 调用
    @Override
    public Object invoke(@Nonnull MethodInvocation invocation) throws Throwable {
        AdapterInvocationWrapper adapterInvocationWrapper = new AdapterInvocationWrapper(invocation);
        Object result = proxyInvocationHandler.invoke(adapterInvocationWrapper); // 拦截处理，ref: sign_m_220
        return result;
    }
}
```

- `io.seata.integration.tx.api.interceptor.handler.AbstractProxyInvocationHandler`
```java
public abstract class AbstractProxyInvocationHandler implements ProxyInvocationHandler {

    // sign_m_220  拦截处理
    @Override
    public Object invoke(InvocationWrapper invocation) throws Throwable {
        if (CollectionUtils.isNotEmpty(getMethodsToProxy()) && !getMethodsToProxy().contains(invocation.getMethod().getName())) {
            return invocation.proceed();
        }
        return doInvoke(invocation); // (事务处理), ref: sign_m_230
    }
    
    // 实现参考： sign_m_230
    protected abstract Object doInvoke(InvocationWrapper invocation) throws Throwable;
}
```

- `io.seata.integration.tx.api.interceptor.handler.GlobalTransactionalInterceptorHandler`
  - 参考：[TM-事务处理-事务控制 sign_m_110](./事务处理.md#事务处理)
```java
// sign_c_140  注解处理器
public class GlobalTransactionalInterceptorHandler extends AbstractProxyInvocationHandler implements ConfigurationChangeListener {

    // sign_m_230  拦截处理 (即：具体的事务处理)
    @Override
    protected Object doInvoke(InvocationWrapper invocation) throws Throwable {
        Class<?> targetClass = invocation.getTarget().getClass();
        Method specificMethod = ClassUtils.getMostSpecificMethod(invocation.getMethod(), targetClass);
        if (specificMethod != null 
            && !specificMethod.getDeclaringClass().equals(Object.class) // 相当于排除 hashCode equals 等方法
        ) {
            // 获取注解
            final GlobalTransactional globalTransactionalAnnotation = getAnnotation(specificMethod, targetClass, GlobalTransactional.class);
            boolean localDisable = disable || ...;
            if (!localDisable) {
                if (globalTransactionalAnnotation != null || this.aspectTransactional != null) {
                    AspectTransactional transactional;
                    if (globalTransactionalAnnotation != null) {
                        transactional = new AspectTransactional( // 组装事务配置对象
                                ...
                                globalTransactionalAnnotation.name(), 
                                globalTransactionalAnnotation.propagation(), // 传播级别
                                globalTransactionalAnnotation.lockStrategyMode() // 锁模式
                            );
                    } ... // else
                    return handleGlobalTransaction(invocation, transactional); // 处理事务，ref: sign_m_231
                } ... // else
            }
        }
        return invocation.proceed();
    }

    // sign_m_231  处理事务
    Object handleGlobalTransaction(
        final InvocationWrapper methodInvocation, 
        final AspectTransactional aspectTransactional
    ) throws Throwable {
        boolean succeed = true;
        try {
            // 执行事务处理，参考：[TM-事务处理-事务控制 sign_m_110]
            // sign_cb_231  事务处理调用源
            return transactionalTemplate.execute(new TransactionalExecutor() {
                @Override
                public Object execute() throws Throwable {
                    return methodInvocation.proceed();
                }

                @Override
                public TransactionInfo getTransactionInfo() {
                    ...

                    TransactionInfo transactionInfo = new TransactionInfo();
                    ... // 组装事务信息
                    transactionInfo.setPropagation(aspectTransactional.getPropagation());
                    return transactionInfo;
                }
            });
        }
        ... // catch { 处理异常，并继续抛出异常 }
        ... // finally { }
    }
}
```