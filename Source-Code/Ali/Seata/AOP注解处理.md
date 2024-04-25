# Seata-AOP-注解处理

## 注解处理器
- `io.seata.integration.tx.api.interceptor.handler.GlobalTransactionalInterceptorHandler`

### 其初始化调用栈
```js
// 可在 sign_cm_190 打断点，执行下面的打印
// new RuntimeException("栈跟踪").printStackTrace();

java.lang.RuntimeException: 栈跟踪
    at io.seata.*.handler.GlobalTransactionalInterceptorHandler.<init>(GlobalTransactionalInterceptorHandler.java:118) // ref: sign_cm_190
    at io.seata.*.parser.GlobalTransactionalInterceptorParser.parserInterfaceToProxy(GlobalTransactionalInterceptorParser.java:54)
    at io.seata.*.parser.DefaultInterfaceParser.parserInterfaceToProxy(DefaultInterfaceParser.java:58)
    at io.seata.*.GlobalTransactionScanner.wrapIfNecessary(GlobalTransactionScanner.java:284) // ref: sign_m_110
    at org.springframework.aop.*.AbstractAutoProxyCreator.postProcessAfterInitialization(*Creator.java:293) // Spring Bean 后处理 (AOP 代理初始化处理)
    at org.springframework.beans.*.AbstractAutowireCapableBeanFactory.applyBeanPostProcessorsAfterInitialization(*Factory.java:455)
    at org.springframework.beans.*.AbstractAutowireCapableBeanFactory.initializeBean(*Factory.java:1808)
    at org.springframework.beans.*.AbstractAutowireCapableBeanFactory.doCreateBean(*Factory.java:620)
    at org.springframework.beans.*.AbstractAutowireCapableBeanFactory.createBean(*Factory.java:542)
```

### 其初始化原理
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
                ProxyInvocationHandler proxyInvocationHandler = DefaultInterfaceParser.get().parserInterfaceToProxy(bean, beanName);
                ...

                interceptor = new AdapterSpringSeataInterceptor(proxyInvocationHandler);

                if (!AopUtils.isAopProxy(bean)) {
                    bean = super.wrapIfNecessary(bean, beanName, cacheKey);
                } else {
                    AdvisedSupport advised = SpringProxyUtils.getAdvisedSupport(bean);
                    Advisor[] advisor = buildAdvisors(beanName, getAdvicesAndAdvisorsForBean(null, null, null));
                    int pos;
                    for (Advisor avr : advisor) {
                        // Find the position based on the advisor's order, and add to advisors by pos
                        pos = findAddSeataAdvisorPosition(advised, avr);
                        advised.addAdvisor(pos, avr);
                    }
                }
                PROXYED_SET.add(beanName);
                return bean;
            }
        } ... // catch 
    }
}
```

- `io.seata.integration.tx.api.interceptor.handler.GlobalTransactionalInterceptorHandler`
```java
// sign_c_190
public class GlobalTransactionalInterceptorHandler extends AbstractProxyInvocationHandler implements ConfigurationChangeListener {
    private final TransactionalTemplate transactionalTemplate = new TransactionalTemplate();
    private final GlobalLockTemplate globalLockTemplate = new GlobalLockTemplate();

    // sign_cm_190
    public GlobalTransactionalInterceptorHandler(FailureHandler failureHandler, Set<String> methodsToProxy) {
        this.failureHandler = failureHandler == null ? FailureHandlerHolder.getFailureHandler() : failureHandler;
        this.methodsToProxy = methodsToProxy;
        ...
    }
}
```