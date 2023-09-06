## 参考
- 概念介绍 https://juejin.cn/post/6965732777962668062
- 原理介绍 https://mrbird.cc/深入理解Spring-AOP原理.html


## 介绍
- AOP **分为静态 AOP 和动态 AOP**
  - **静态 AOP 是指 AspectJ 实现的 AOP**，其将切面代码直接编译到 Java 类文件中
  - 动态 AOP 是指将切面代码进行动态织入实现的 AOP
    - **Spring 的 AOP 为动态 AOP**，实现的技术为：JDK 动态代理和 CGLib(Code Generate Libary 字节码生成)


## 专业词（类）
- Advisor 通知器
- Advice 通知、增强
- Pointcut 切点
- PointcutAdvisor 切点通知器（切面）
  - 用来管理`Advice`和`Pointcut`


## 关键类
- `org.springframework.context.annotation.EnableAspectJAutoProxy` **启用注解**
- `org.springframework.aop.framework.DefaultAopProxyFactory` AOP 代理工厂
- `org.springframework.aop.framework.ProxyCreatorSupport` 调用工厂创建代理
- `org.springframework.aop.aspectj.annotation.AnnotationAwareAspectJAutoProxyCreator` 默认的创建者


## 单元测试
- `org.springframework.context.annotation.EnableAspectJAutoProxyTests`
```java
    /*** JDK 代理配置 */
	@ComponentScan("example.scannable")
	@EnableAspectJAutoProxy // 启用 AOP
	static class ConfigWithJdkProxy {
	}

	@Test // 测试 JDK 代理
	void withJdkProxy() {
		ConfigurableApplicationContext ctx = new AnnotationConfigApplicationContext(ConfigWithJdkProxy.class);
        aspectIsApplied(ctx); // 断言相关方法
		assertThat(AopUtils.isJdkDynamicProxy(ctx.getBean(FooService.class))).isTrue();
	}
```


## 原理
### 启用-AOP-原理
- Spring-Boot 里面 `AopAutoConfiguration` 会对 `EnableAspectJAutoProxy` 进行启用
  - **默认是用 CGLib 创建代理**
```java
// org.springframework.boot.autoconfigure.aop.AopAutoConfiguration
@Configuration(proxyBeanMethods = false)
@ConditionalOnProperty(prefix = "spring.aop", name = "auto", havingValue = "true", matchIfMissing = true)
public class AopAutoConfiguration {
    @Configuration(proxyBeanMethods = false)
    @ConditionalOnClass(Advice.class)
    static class AspectJAutoProxyingConfiguration {
        ... // 省略 JDK 代理配置

        @Configuration(proxyBeanMethods = false)
        @EnableAspectJAutoProxy(proxyTargetClass = true) // 在此启用
        @ConditionalOnProperty(prefix = "spring.aop", name = "proxy-target-class", havingValue = "true",
                matchIfMissing = true) // matchIfMissing 表示没有设置此属性，也算匹配上，也就是说默认是用 CGLib 创建代理
        static class CglibAutoProxyConfiguration {
        }
    }
    ... // 省略其他代理配置
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
### 创建-Proxy-调用链路
- `org.springframework.aop.framework.autoproxy.AbstractAutoProxyCreator`
  - 被 `org.springframework.aop.aspectj.annotation.AnnotationAwareAspectJAutoProxyCreator` 继承
```java
    /*** 后处理：Bean 实例化前处理（创建 AOP 代理） */
    @Override
    public Object postProcessBeforeInstantiation(Class<?> beanClass, String beanName) {
        Object cacheKey = getCacheKey(beanClass, beanName);
        ...
        TargetSource targetSource = getCustomTargetSource(beanClass, beanName);
        if (targetSource != null) {
            ...
            // 获取通知器（相当于拦截器）
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
    /*** 查找给定 Bean 的通知器 */
    @Override
    @Nullable
    protected Object[] getAdvicesAndAdvisorsForBean(
            Class<?> beanClass, String beanName, @Nullable TargetSource targetSource) {

        List<Advisor> advisors = findEligibleAdvisors(beanClass, beanName); // 查看合格的通知器
        if (advisors.isEmpty()) {
            return DO_NOT_PROXY;
        }
        return advisors.toArray();
    }

    /*** 查看合格的通知器(Advisor) */
    protected List<Advisor> findEligibleAdvisors(Class<?> beanClass, String beanName) {
        List<Advisor> candidateAdvisors = findCandidateAdvisors(); // 查找通知器
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
    /*** 查找通知器(Advisor) */
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
                return new JdkDynamicAopProxy(config);     // 是接口等等，使用 JDK 动态代理
            }
            return new ObjenesisCglibAopProxy(config);     // 否则，使用 CGLib 创建代理
        }
        else {
            return new JdkDynamicAopProxy(config);         // 默认使用 JDK 动态代理
        }
    }
```


### AopContext.currentProxy() 原理
- `org.springframework.aop.framework.JdkDynamicAopProxy`
```java
    @Override // 实现 JDK InvocationHandler 方法
    @Nullable
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        Object oldProxy = null;
        boolean setProxyContext = false;

        TargetSource targetSource = this.advised.targetSource;
        Object target = null;

        try {
            ... // 省略不需代理的方法

            Object retVal;

            if (this.advised.exposeProxy) {
                // 设置当前代理到线程变量；并记录旧值用于恢复
                oldProxy = AopContext.setCurrentProxy(proxy);
                setProxyContext = true;
            }

            target = targetSource.getTarget();
            Class<?> targetClass = (target != null ? target.getClass() : null);

            // 获取方法拦截器链路
            List<Object> chain = this.advised.getInterceptorsAndDynamicInterceptionAdvice(method, targetClass);

            if (chain.isEmpty()) { // 链路为空
                // 直接方法调用
                Object[] argsToUse = AopProxyUtils.adaptArgumentsIfNecessary(method, args);
                retVal = AopUtils.invokeJoinpointUsingReflection(target, method, argsToUse);
            }
            else {
                // 链路调用
                MethodInvocation invocation =
                        new ReflectiveMethodInvocation(proxy, target, method, args, targetClass, chain);
                retVal = invocation.proceed();
            }

            ... // 省略 return this 处理
            return retVal;
        }
        finally {
            ...
            if (setProxyContext) {
                // 恢复旧值
                AopContext.setCurrentProxy(oldProxy);
            }
        }
    }
```

- `org.springframework.aop.framework.CglibAopProxy.DynamicAdvisedInterceptor`
```java
        @Override // 实现 CGLib MethodInterceptor 方法
        @Nullable
        public Object intercept(Object proxy, Method method, Object[] args, MethodProxy methodProxy) throws Throwable {
            Object oldProxy = null;
            boolean setProxyContext = false;
            Object target = null;
            TargetSource targetSource = this.advised.getTargetSource();
            try {
                if (this.advised.exposeProxy) {
                    // 设置当前代理到线程变量；并记录旧值用于恢复
                    oldProxy = AopContext.setCurrentProxy(proxy); 
                    setProxyContext = true;
                }
                ... // 省略方法调用
                return processReturnType(proxy, target, method, retVal);
            }
            finally {
                ...
                if (setProxyContext) {
                    // 设置旧值
                    AopContext.setCurrentProxy(oldProxy);
                }
            }
        }
```

### 方法类型单元测试
- 测试`包可见`的方法
  - `org.springframework.aop.framework.CglibProxyTests #testPackageMethodInvocation`
- 测试`可继承`的方法
  - `org.springframework.aop.framework.CglibProxyTests #testProtectedMethodInvocation`

#### AOP-调用链
```js
org.springframework.aop.framework.CglibAopProxy.DynamicAdvisedInterceptor #intercept // 开始 AOP 链路调用
org.springframework.aop.framework.CglibAopProxy.CglibMethodInvocation #proceed
org.springframework.aop.framework.ReflectiveMethodInvocation #proceed // 测试，只调用一次

org.aopalliance.intercept.MethodInterceptor #invoke // unit test -> NopInterceptor #invoke
org.springframework.aop.framework.CglibAopProxy.CglibMethodInvocation #proceed
org.springframework.aop.framework.ReflectiveMethodInvocation #proceed
org.springframework.aop.framework.ReflectiveMethodInvocation #invokeJoinpoint // 最后一个连接点才执行
org.springframework.aop.support.AopUtils #invokeJoinpointUsingReflection
java.lang.reflect.Method #invoke // 反射执行目标类的方法
```

### 测试 AOP 生成类
- 测试源码： https://github.com/zengxf/spring-demo/tree/master/aop/aop-principle
- (CGLib)生成的类如下：
```java
package cn.zxf.spring_aop.spring_dump_test; // 与父类同包

// 继承要代理的类
public class DemoMethodService$$SpringCGLIB$$0 extends DemoMethodService implements SpringProxy, Advised, Factory {
    static {
        CGLIB$STATICHOOK4();
    }
    // 类初始化时，获取对应的方法
    static void CGLIB$STATICHOOK4() {
        ...
        CGLIB$add$0$Proxy = MethodProxy.create(var1, var0, "()V", "add", "CGLIB$add$0");
        CGLIB$testProtected$1$Proxy = MethodProxy.create(var1, var0, "()V", "testProtected", "CGLIB$testProtected$1");
        CGLIB$testPackage$2$Proxy = MethodProxy.create(var1, var0, "()V", "testPackage", "CGLIB$testPackage$2");
        CGLIB$equals$3$Proxy = MethodProxy.create(var1, var0, "(Ljava/lang/Object;)Z", "equals", "CGLIB$equals$3");
        CGLIB$toString$4$Proxy = MethodProxy.create(var1, var0, "()Ljava/lang/String;", "toString", "CGLIB$toString$4");
        CGLIB$hashCode$5$Proxy = MethodProxy.create(var1, var0, "()I", "hashCode", "CGLIB$hashCode$5");
    }
    // 设置回调（可搜索关键字：CGLIB$SET_THREAD_CALLBACKS 查看源码生成）
    // 在 org.springframework.cglib.proxy.Enhancer.EnhancerFactoryData #setThreadCallbacks() 里调用
    public static void CGLIB$SET_THREAD_CALLBACKS(Callback[] var0) {
        CGLIB$THREAD_CALLBACKS.set(var0);
    }

    public DemoMethodService$$SpringCGLIB$$0() {
        CGLIB$BIND_CALLBACKS(this);
    }
    // 实例初始化时，设置对应的回调
    private static final void CGLIB$BIND_CALLBACKS(Object var0) {
        DemoMethodService$$SpringCGLIB$$0 var1 = (DemoMethodService$$SpringCGLIB$$0)var0;
        if (!var1.CGLIB$BOUND) {
            var1.CGLIB$BOUND = true;
            Object var10000 = CGLIB$THREAD_CALLBACKS.get();
            ...
            Callback[] var10001 = (Callback[])var10000;
            ...
            // 相当于：org.springframework.aop.framework.CglibAopProxy.DynamicAdvisedInterceptor 实例
            var1.CGLIB$CALLBACK_0 = (MethodInterceptor)var10001[0];
        }
    }
    final void testPackage() {
        MethodInterceptor var10000 = this.CGLIB$CALLBACK_0;
        ...
        if (var10000 != null) {
            var10000.intercept(this, CGLIB$testPackage$2$Method, CGLIB$emptyArgs, CGLIB$testPackage$2$Proxy);
        } else {
            super.testPackage(); // 与父类是同一个包，可以直接调用父类
        }
    }
    protected final void testProtected() {
        MethodInterceptor var10000 = this.CGLIB$CALLBACK_0;
        ...
        if (var10000 != null) {
            // org.springframework.cglib.proxy.MethodInterceptor #intercept
            var10000.intercept(this, CGLIB$testProtected$1$Method, CGLIB$emptyArgs, CGLIB$testProtected$1$Proxy);
        } else {
            super.testProtected(); // 调用父类方法
        }
    }
    // 只能重写 package、protected、public，不能重写 public final、private
}
```

### 总结
- 创建代理
- 调用代理方法时，会调用 AOP 增强链
  - `CglibAopProxy.DynamicAdvisedInterceptor #intercept` 会调用增强链
  - `CglibAopProxy.CglibMethodInvocation #proceed` 调用每一个（自定义）增强
    - 这里的增强，相当于 `org.springframework.cglib.proxy.MethodInterceptor` 拦截器子类
    - 拦截器子类封装增强操作
- 调用完增强链后，（相当于最后一步）反射调用目标方法


---
## AOP 注解处理
- 增强注解对应的拦截器：
  - `@Before                MethodBeforeAdviceInterceptor            MethodBeforeAdvice`
  - `@Around                AspectJAroundAdvice`
  - `@After                 AspectJAfterAdvice`
  - `@AfterThrowing         AspectJAfterThrowingAdvice`
  - `@AfterReturning        AfterReturningAdviceInterceptor         AspectJAfterReturningAdvice`

### 原理
- 测试源码： https://github.com/zengxf/spring-demo/tree/master/aop/aop-principle
- 最后调用类 `org.springframework.aop.aspectj.AbstractAspectJAdvice`
```java
    /*** 反射调用自定义的增强方法 */
    protected Object invokeAdviceMethodWithGivenArgs(Object[] args) throws Throwable {
        ...
        try {
            ReflectionUtils.makeAccessible(this.aspectJAdviceMethod);
            // 其会反射调用增强的方法
            // aspectJAdviceMethod 相当于是
            //   => public void cn.zxf.spring_aop.spring_dump_test.AopAspect.methodBefore(JoinPoint)
            // aspectInstanceFactory.getAspectInstance() 相当于是 
            //   => cn.zxf.spring_aop.spring_dump_test.AopAspect 实例
            return this.aspectJAdviceMethod.invoke(this.aspectInstanceFactory.getAspectInstance(), actualArgs);
        }
        ... // 省略 catch
    }
```