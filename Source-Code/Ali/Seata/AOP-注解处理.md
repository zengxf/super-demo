# Seata-AOP-注解处理


---
## 注解处理器
- `io.seata.integration.tx.api.interceptor.handler.GlobalTransactionalInterceptorHandler`

### 处理器初始化调用栈
```js
// 可在 sign_cm_140 打断点，执行下面的打印
// new RuntimeException("栈跟踪").printStackTrace();

java.lang.RuntimeException: 栈跟踪
    at io.seata.*.handler.GlobalTransactionalInterceptorHandler.<init>(GlobalTransactionalInterceptorHandler.java:118) // ref: sign_cm_140
    at io.seata.*.parser.GlobalTransactionalInterceptorParser.parserInterfaceToProxy(GlobalTransactionalInterceptorParser.java:54) // ref: sign_m_130
    at io.seata.*.parser.DefaultInterfaceParser.parserInterfaceToProxy(DefaultInterfaceParser.java:58) // ref: sign_m_120
    at io.seata.*.GlobalTransactionScanner.wrapIfNecessary(GlobalTransactionScanner.java:284) // ref: sign_m_110
    at org.springframework.aop.*.AbstractAutoProxyCreator.postProcessAfterInitialization(*Creator.java:293) // Spring Bean 后处理 (AOP 代理初始化处理)
    at org.springframework.beans.*.AbstractAutowireCapableBeanFactory.applyBeanPostProcessorsAfterInitialization(*Factory.java:455)
    at org.springframework.beans.*.AbstractAutowireCapableBeanFactory.initializeBean(*Factory.java:1808)
    at org.springframework.beans.*.AbstractAutowireCapableBeanFactory.doCreateBean(*Factory.java:620)
    at org.springframework.beans.*.AbstractAutowireCapableBeanFactory.createBean(*Factory.java:542)
```

### 处理器初始化原理
- `io.seata.spring.annotation.GlobalTransactionScanner`
```java
// sign_c_110
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
                    .parserInterfaceToProxy(bean, beanName); // ref: sign_m_120
                ...

                interceptor = new AdapterSpringSeataInterceptor(proxyInvocationHandler); // ref: sign_cm_210

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

    @Override
    protected Object[] getAdvicesAndAdvisorsForBean(Class beanClass, String beanName, ...) throws BeansException {
        return new Object[]{interceptor};
    }
}
```

- `io.seata.integration.tx.api.interceptor.parser.DefaultInterfaceParser`
```java
// sign_c_120
public class DefaultInterfaceParser implements InterfaceParser {

    // sign_m_120
    @Override
    public ProxyInvocationHandler parserInterfaceToProxy(Object target, String objectName) throws Exception {
        for (InterfaceParser interfaceParser : ALL_INTERFACE_PARSERS) {
            ProxyInvocationHandler proxyInvocationHandler = interfaceParser.parserInterfaceToProxy(target, objectName); // ref: sign_m_130
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
// sign_c_130
public class GlobalTransactionalInterceptorParser implements InterfaceParser {

    // sign_m_130
    @Override
    public ProxyInvocationHandler parserInterfaceToProxy(Object target, String objectName) throws Exception {
        Class<?> serviceInterface = DefaultTargetClassParser.get().findTargetClass(target);
        Class<?>[] interfacesIfJdk = DefaultTargetClassParser.get().findInterfaces(target);

        if (existsAnnotation(serviceInterface) || existsAnnotation(interfacesIfJdk)) {
            ProxyInvocationHandler proxyInvocationHandler = new GlobalTransactionalInterceptorHandler(...); // ref: sign_cm_140
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
	at org.apache.seata.service.impl.BusinessServiceImpl$$EnhancerBySpringCGLIB$$cb496675.purchase(<generated>) // demo 方法
	at org.apache.seata.SpringbootSeataApplication.lambda$main$0(SpringbootSeataApplication.java:20) // Main
	...
```

- `io.seata.spring.annotation.AdapterSpringSeataInterceptor`
```java
// sign_c_210  AOP 拦截器
public class AdapterSpringSeataInterceptor implements MethodInterceptor, SeataInterceptor, Ordered {

    // sign_cm_210
    public AdapterSpringSeataInterceptor(ProxyInvocationHandler proxyInvocationHandler) {
        ...
        this.proxyInvocationHandler = proxyInvocationHandler;
    }

    // sign_m_210
    @Override
    public Object invoke(@Nonnull MethodInvocation invocation) throws Throwable {
        AdapterInvocationWrapper adapterInvocationWrapper = new AdapterInvocationWrapper(invocation);
        Object result = proxyInvocationHandler.invoke(adapterInvocationWrapper);
        return result;
    }
}
```

- `io.seata.integration.tx.api.interceptor.handler.AbstractProxyInvocationHandler`
```java
public abstract class AbstractProxyInvocationHandler implements ProxyInvocationHandler {

    // sign_m_220
    @Override
    public Object invoke(InvocationWrapper invocation) throws Throwable {
        if (CollectionUtils.isNotEmpty(getMethodsToProxy()) && !getMethodsToProxy().contains(invocation.getMethod().getName())) {
            return invocation.proceed();
        }
        return doInvoke(invocation); // ref: sign_m_230
    }
    
    // 实现参考： sign_m_230
    protected abstract Object doInvoke(InvocationWrapper invocation) throws Throwable;
}
```

- `io.seata.integration.tx.api.interceptor.handler.GlobalTransactionalInterceptorHandler`
```java

public class GlobalTransactionalInterceptorHandler extends AbstractProxyInvocationHandler implements ConfigurationChangeListener {

    // sign_m_230
    @Override
    protected Object doInvoke(InvocationWrapper invocation) throws Throwable {
        Class<?> targetClass = invocation.getTarget().getClass();
        Method specificMethod = ClassUtils.getMostSpecificMethod(invocation.getMethod(), targetClass);
        if (specificMethod != null 
            && !specificMethod.getDeclaringClass().equals(Object.class) // 相当于排除 hashCode equals 等方法
        ) {
            final GlobalTransactional globalTransactionalAnnotation = getAnnotation(specificMethod, targetClass, GlobalTransactional.class);
            boolean localDisable = disable || ...;
            if (!localDisable) {
                if (globalTransactionalAnnotation != null || this.aspectTransactional != null) {
                    AspectTransactional transactional;
                    if (globalTransactionalAnnotation != null) {
                        transactional = new AspectTransactional(
                                globalTransactionalAnnotation.timeoutMills(),
                                globalTransactionalAnnotation.name(), 
                                ...
                                globalTransactionalAnnotation.propagation(), // 传播级别
                                ...
                                globalTransactionalAnnotation.lockStrategyMode() // 锁模式
                            );
                    } ... // else
                    return handleGlobalTransaction(invocation, transactional);
                } ... // else
            }
        }
        return invocation.proceed();
    }
}
```