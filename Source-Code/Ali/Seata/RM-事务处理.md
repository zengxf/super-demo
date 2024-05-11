# Seata-RM-事务处理


---
## Spring-Boot-自动配置
- 模块：`seata-spring-boot-starter`
- `./META-INF/spring/*.AutoConfiguration.imports`
```js
...
io.seata.*.SeataDataSourceAutoConfiguration // Seata 数据源(连接池)配置，ref: sign_c_010
...
```

- `io.seata.spring.boot.autoconfigure.SeataDataSourceAutoConfiguration`
```java
// sign_c_010  Seata 数据源(连接池)配置
@ConditionalOnBean(DataSource.class)
...
public class SeataDataSourceAutoConfiguration {

    // 返回连接池 (如：HikariDataSource) AOP 处理类，ref: sign_c_110
    @Bean(...)
    @ConditionalOnMissingBean(SeataAutoDataSourceProxyCreator.class)
    public static SeataAutoDataSourceProxyCreator seataAutoDataSourceProxyCreator(SeataProperties seataProperties) {
        return new SeataAutoDataSourceProxyCreator(...); // ref: sign_cm_110
    }

}
```


---
## 事务处理
- 通过 AOP 控制连接池，进而代理连接，在代理连接中对事务相关方法进行控制

- `io.seata.spring.annotation.datasource.SeataAutoDataSourceProxyCreator`
```java
// sign_c_110  连接池 AOP 处理
public class SeataAutoDataSourceProxyCreator extends AbstractAutoProxyCreator {

    // sign_cm_110
    public SeataAutoDataSourceProxyCreator(..., String dataSourceProxyMode) {
        ...
        this.advisors = buildAdvisors(dataSourceProxyMode); // ref: sign_m_105
    }

    // sign_m_105
    private Object[] buildAdvisors(String dataSourceProxyMode) {
        Advice advice = new SeataAutoDataSourceProxyAdvice(dataSourceProxyMode); // ref: sign_c_210
        return new Object[]{ new DefaultIntroductionAdvisor(advice) };
    }

    @Override // 返回给父类方法用，组装 AOP 拦截链
    protected Object[] getAdvicesAndAdvisorsForBean(Class<?> beanClass, String beanName, TargetSource customTargetSource) {
        return advisors; // 初始值来自： sign_m_105
    }

    // sign_m_110  构建代理
    // 调用源：
    //   at *.aop.*.AbstractAutoProxyCreator.postProcessAfterInitialization(*Creator.java:293) // Spring Bean 后处理 (AOP 代理初始化处理)
    @Override
    protected Object wrapIfNecessary(Object bean, String beanName, Object cacheKey) {
        ... // 非 DataSource 对象返回

        if (!(bean instanceof SeataDataSourceProxy)) { // 当这个 Bean 只是一个简单的 DataSource，而不是 SeataDataSourceProxy 时，进行代理处理
            Object enhancer = super.wrapIfNecessary(bean, beanName, cacheKey);
            if (bean == enhancer) { // 这意味着该 bean 要么被用户排除，要么之前已被代理过
                return bean;
            }
            // 否则，构建代理，将 <origin, proxy> 放入持有者并返回增强器
            DataSource origin = (DataSource) bean;
            SeataDataSourceProxy proxy = buildProxy(origin, dataSourceProxyMode); // 构建连接池代理，ref: sign_m_111
            DataSourceProxyHolder.put(origin, proxy); // sign_cb_110  存放，AOP 增强时用
            ...
            return enhancer;
        }

        ... // 是 SeataDataSourceProxy 对象的处理
    }

    // sign_m_111  构建连接池代理
    SeataDataSourceProxy buildProxy(DataSource origin, String proxyMode) {
        if (BranchType.AT.name().equalsIgnoreCase(proxyMode)) {
            return new DataSourceProxy(origin); // ref: sign_c_220
        }
        if (BranchType.XA.name().equalsIgnoreCase(proxyMode)) {
            return new DataSourceProxyXA(origin);
        }
        throw new IllegalArgumentException(...);
    }

}
```


---
## AOP-处理
- 增强连接池对象，返回连接代理

- `io.seata.spring.annotation.datasource.SeataAutoDataSourceProxyAdvice`
```java
// sign_c_210  断言（增强）
public class SeataAutoDataSourceProxyAdvice implements MethodInterceptor, IntroductionInfo {

    @Override
    public Object invoke(MethodInvocation invocation) throws Throwable {
        ... // 不需要全局锁，或没有全局事务 (xid)，或不是 AT XA 环境，则原方法调用

        Method method = invocation.getMethod();
        String name = method.getName();
        Class<?>[] parameterTypes = method.getParameterTypes();

        Method declared;
        try {
            declared = DataSource.class.getDeclaredMethod(name, parameterTypes);
        } ... // catch

        // 将方法调用切换到其代理
        DataSource origin = (DataSource) invocation.getThis();
        SeataDataSourceProxy proxy = DataSourceProxyHolder.get(origin); // 存放参考： sign_cb_110
        Object[] args = invocation.getArguments();
        return declared.invoke(proxy, args); // ref: sign_m_220
    }

}
```

- `io.seata.rm.datasource.DataSourceProxy`
```java
// sign_c_220  连接池代理
public class DataSourceProxy extends AbstractDataSourceProxy implements Resource {

    // sign_m_220  获取连接
    @Override
    public ConnectionProxy getConnection() throws SQLException {
        Connection targetConnection = targetDataSource.getConnection(); // 通过目标对象连接真正的连接
        return new ConnectionProxy(this, targetConnection); // 对连接进行代理，返回。ref: sign_c_310
    }

}
```


---
## 事务代理处理
- 通过连接代理进行事务处理

- `io.seata.rm.datasource.ConnectionProxy`
```java
// sign_c_310  连接代理
public class ConnectionProxy extends AbstractConnectionProxy {

    // sign_m_310  提交
    @Override
    public void commit() throws SQLException {
        try {
            lockRetryPolicy.execute(() -> { // 使用重试策略进行提交
                doCommit(); // ref: sign_m_311
            });
        } ... // catch
    }

    // sign_m_315  回滚
    @Override
    public void rollback() throws SQLException {
        targetConnection.rollback(); // 目标连接回滚
        report(false); // 上报结果
        ...
    }

    // sign_m_311  提交处理
    private void doCommit() throws SQLException {
        if (context.inGlobalTransaction()) {
            processGlobalTransactionCommit(); // ref: sign_m_312
        }
        ...
    }

    // sign_m_312  AT 事务提交处理
    private void processGlobalTransactionCommit() throws SQLException {
        try {
            register(); // 注册事务分支，ref: sign_m_313
        } ... // catch
        try {
            UndoLogManagerFactory.getUndoLogManager(this.getDbType()).flushUndoLogs(this);
            targetConnection.commit(); // 目标连接提交
        } ... // catch
        report(false); // 上报结果
        ...
    }

    // sign_m_313  向 TC 服务注册事务分支
    private void register() throws TransactionException {
        ...
        Long branchId = DefaultResourceManager.get()
            .branchRegister( // 注册事务分支
                BranchType.AT, getDataSourceProxy().getResourceId(),
                null, context.getXid(), context.getApplicationData(),
                context.buildLockKeys()
            );
        context.setBranchId(branchId);
    }
}
```

- `io.seata.rm.datasource.AbstractConnectionProxy`
```java
// sign_c_320
public abstract class AbstractConnectionProxy implements Connection {

    @Override
    public PreparedStatement prepareStatement(String sql) throws SQLException {
        ...
        PreparedStatement targetPreparedStatement = null;
        ...
        if (targetPreparedStatement == null) {
            targetPreparedStatement = getTargetConnection().prepareStatement(sql);
        }
        return new PreparedStatementProxy(this, targetPreparedStatement, sql);
    }

}
```


---
## JDBC-模板
- 业务代码用常规 `JdbcTemplate` 即可自动使用 AT 事务

- `org.springframework.jdbc.core.JdbcTemplate`
```java
public class JdbcTemplate extends JdbcAccessor implements JdbcOperations {
	@Nullable
	private <T> T execute(PreparedStatementCreator psc, ...) throws DataAccessException {
		...

		Connection con = DataSourceUtils.getConnection(obtainDataSource()); // 相当于 dataSource.getConnection(); ref: sign_m_220
		PreparedStatement ps = null;
		try {
			ps = psc.createPreparedStatement(con); // 相当于 con.prepareStatement(this.sql);
			T result = action.doInPreparedStatement(ps); // 相当于 int rows = ps.executeUpdate();
			...
			return result;
		}
		... // catch
		finally {
            ...
            DataSourceUtils.releaseConnection(con, getDataSource());
		}
	}
}
```