## 关键类
- `org.springframework.transaction.annotation.EnableTransactionManagement`
- `org.springframework.transaction.interceptor.TransactionInterceptor`
- `org.springframework.transaction.annotation.Transactional`

## 单元测试
- 参考：`org.springframework.transaction.annotation.EnableTransactionManagementTests`
```java
	@Configuration
	@EnableTransactionManagement // 启用事务管理
	@Import(PlaceholderConfig.class)
	static class EnableTxConfig {
	}

    /*** 事务测试服务类 */
	@Service
	public static class TransactionalTestBean {
		@Transactional(label = "${myLabel}", timeoutString = "${myTimeout}", readOnly = true)
		public Collection<?> findAllFoos() {
			return null;
		}
	}

    @Test
	public void txManagerIsResolvedOnInvocationOfTransactionalMethod() {
		AnnotationConfigApplicationContext ctx = new AnnotationConfigApplicationContext(
				EnableTxConfig.class, TxManagerConfig.class);
		TransactionalTestBean bean = ctx.getBean(TransactionalTestBean.class);
		CallCountingTransactionManager txManager = ctx.getBean("txManager", CallCountingTransactionManager.class);

		// invoke a transactional method, causing the PlatformTransactionManager bean to be resolved.
		bean.findAllFoos(); // 调用此方法时，会调用事务管理器 CallCountingTransactionManager 里面的方法
		assertThat(txManager.commits).isEqualTo(1);
		assertThat(txManager.rollbacks).isEqualTo(0);
        ... // 省略其他断言

		ctx.close();
	}
```

- `org.springframework.transaction.testfixture.CallCountingTransactionManager`
```java
/*** 单元测试用的自定义-事务管理器 */
public class CallCountingTransactionManager extends AbstractPlatformTransactionManager {
	@Override // 创建并返回事务对象
	protected Object doGetTransaction() {
		return new Object();
	}

	@Override // 开始事务
	protected void doBegin(Object transaction, TransactionDefinition definition) {
	}

	@Override // 提交事务
	protected void doCommit(DefaultTransactionStatus status) {
	}

	@Override // 回滚事务
	protected void doRollback(DefaultTransactionStatus status) {
	}
}
```

## 原理
- `org.springframework.transaction.annotation.EnableTransactionManagement`
```java
/*** 启用事务管理的注解 */
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Import(TransactionManagementConfigurationSelector.class) // 设置导入
public @interface EnableTransactionManagement {
    boolean proxyTargetClass() default false;
    AdviceMode mode() default AdviceMode.PROXY; // 使用 JDK 动态代理
    int order() default Ordered.LOWEST_PRECEDENCE;
}
```

- `org.springframework.transaction.annotation.TransactionManagementConfigurationSelector`
```java
/*** 配置导入选择器 */
public class TransactionManagementConfigurationSelector extends AdviceModeImportSelector<EnableTransactionManagement> {
	@Override
	protected String[] selectImports(AdviceMode adviceMode) {
		return switch (adviceMode) {
			case PROXY -> new String[] {AutoProxyRegistrar.class.getName(),
					ProxyTransactionManagementConfiguration.class.getName()}; // 配置关键类
			case ASPECTJ -> new String[] {determineTransactionAspectClass()};
		};
	}
    ... // 省略 AspectJ 导入类
}
```

- `org.springframework.transaction.annotation.ProxyTransactionManagementConfiguration`
```java
/*** 事务管理配置类 */
@Configuration(proxyBeanMethods = false)
public class ProxyTransactionManagementConfiguration extends AbstractTransactionManagementConfiguration {
	@Bean // 解析 @Transactional 注解中的属性
	public TransactionAttributeSource transactionAttributeSource() {
		return new AnnotationTransactionAttributeSource(false);
	}

	@Bean // AOP 拦截器，相当于增强
	public TransactionInterceptor transactionInterceptor(TransactionAttributeSource transactionAttributeSource) {
		TransactionInterceptor interceptor = new TransactionInterceptor();
		interceptor.setTransactionAttributeSource(transactionAttributeSource);
		if (this.txManager != null) {
			interceptor.setTransactionManager(this.txManager); // 设置事务管理器
		}
		return interceptor;
	}

	// 相当于定义切面
	@Bean(name = TransactionManagementConfigUtils.TRANSACTION_ADVISOR_BEAN_NAME)
	public BeanFactoryTransactionAttributeSourceAdvisor transactionAdvisor(
			TransactionAttributeSource transactionAttributeSource, TransactionInterceptor transactionInterceptor
    ) {
		BeanFactoryTransactionAttributeSourceAdvisor advisor = new BeanFactoryTransactionAttributeSourceAdvisor();
		advisor.setTransactionAttributeSource(transactionAttributeSource);
		advisor.setAdvice(transactionInterceptor);
		... // 省略设置顺序
		return advisor;
	}
}
```

- `org.springframework.transaction.interceptor.TransactionInterceptor`
```java
/*** 事务方法-拦截器 */
public class TransactionInterceptor extends TransactionAspectSupport implements MethodInterceptor, Serializable {
	@Override
	@Nullable
	public Object invoke(MethodInvocation invocation) throws Throwable {
		Class<?> targetClass = (invocation.getThis() != null ? AopUtils.getTargetClass(invocation.getThis()) : null);
        // 调用父类 TransactionAspectSupport 方法
		return invokeWithinTransaction(invocation.getMethod(), targetClass, new CoroutinesInvocationCallback() {
			... // 回调方法省略
		});
	}
}
```

- `org.springframework.transaction.interceptor.TransactionAspectSupport`
```java
/*** 事务切面支持（事务拦截器父类） */
public abstract class TransactionAspectSupport implements BeanFactoryAware, InitializingBean {
    @Nullable
	protected Object invokeWithinTransaction(Method method, @Nullable Class<?> targetClass,
			final InvocationCallback invocation) throws Throwable {

		// If the transaction attribute is null, the method is non-transactional.
		TransactionAttributeSource tas = getTransactionAttributeSource(); // 事务属性解析器（相当于上面配置类的注解解析器）
		final TransactionAttribute txAttr = (tas != null ? tas.getTransactionAttribute(method, targetClass) : null); // 解析出事务属性
		final TransactionManager tm = determineTransactionManager(txAttr); // 根据事务属性返回事务管理器（非默认则根据 Bean 工厂查找指定的）

		... // 省略响应式事务处理

		PlatformTransactionManager ptm = asPlatformTransactionManager(tm);
		final String joinpointIdentification = methodIdentification(method, targetClass, txAttr);

		if (txAttr == null || !(ptm instanceof CallbackPreferringPlatformTransactionManager cpptm)) { // 一般进入此逻辑
			// Standard transaction demarcation with getTransaction and commit/rollback calls.
            // 创建事务对象
			TransactionInfo txInfo = createTransactionIfNecessary(ptm, txAttr, joinpointIdentification);

			Object retVal;
			try {
				// This is an around advice: Invoke the next interceptor in the chain.
				// This will normally result in a target object being invoked.
				retVal = invocation.proceedWithInvocation();
			}
			catch (Throwable ex) {
				// target invocation exception
				completeTransactionAfterThrowing(txInfo, ex);
				throw ex;
			}
			finally {
				cleanupTransactionInfo(txInfo);
			}

			if (retVal != null && vavrPresent && VavrDelegate.isVavrTry(retVal)) {
				// Set rollback-only in case of Vavr failure matching our rollback rules...
				TransactionStatus status = txInfo.getTransactionStatus();
				if (status != null && txAttr != null) {
					retVal = VavrDelegate.evaluateTryFailure(retVal, txAttr, status);
				}
			}

			commitTransactionAfterReturning(txInfo);
			return retVal;
		}

		else {
			... // 省略事务处理
			... // 省略 catch
			... // 省略异常传递
			return result;
		}
	}
    // 创建事务对象
	protected TransactionInfo createTransactionIfNecessary(@Nullable PlatformTransactionManager tm,
			@Nullable TransactionAttribute txAttr, final String joinpointIdentification) {
		... // 省略无关逻辑
		TransactionStatus status = null;
		if (txAttr != null) {
			if (tm != null) {
				status = tm.getTransaction(txAttr); // 通过事务管理器创建事务对象
			}
			... // 省略无关逻辑
		}
        // 创建 TransactionInfo，并绑定到线程变量
        // 将线程中旧的对象，关联到 oldTransactionInfo 属性里（相当于创建单向链）
		return prepareTransactionInfo(tm, txAttr, joinpointIdentification, status);
	}
}
```