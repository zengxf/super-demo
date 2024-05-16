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
  - 保存 undo 日志参考：[RM-undo-日志及操作-持久化 sign_m_220](./RM-undo-日志及操作.md#持久化)
```java
// sign_c_310  连接代理
public class ConnectionProxy extends AbstractConnectionProxy { // ref: sign_c_320

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
        targetConnection.rollback(); // 调用原连接进行回滚
        report(false); // 上报结果，ref: sign_m_314
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
            // sign_cb_312 保存 undo 日志
            UndoLogManagerFactory.getUndoLogManager(this.getDbType()) // 返回 MySQLUndoLogManager 实例
                .flushUndoLogs(this);   // 参考：[RM-undo-日志及操作-持久化 sign_m_220]
            targetConnection.commit();  // 调用原连接进行提交
        } ... // catch
        report(false); // 上报结果，ref: sign_m_314
        ...
    }

    // sign_m_313  向 TC 服务注册事务分支
    private void register() throws TransactionException {
        ...
        Long branchId = DefaultResourceManager.get()
            .branchRegister( // 注册事务分支 (RPC 请求，底层通信跟 TM 一样)
                BranchType.AT, *.getResourceId(), ..., context.getXid(), ...
            );
        context.setBranchId(branchId);
    }

    // sign_m_314  向 TC 服务上报结果
    private void report(boolean commitDone) throws SQLException {
        ...
        int retry = REPORT_RETRY_COUNT;
        while (retry > 0) {
            try {
                DefaultResourceManager.get()
                .branchReport( // 上报事务结果 (RPC 请求，底层通信跟 TM 一样)
                    BranchType.AT, context.getXid(), context.getBranchId(), ...
                );
                return;
            }
            ... // catch
        }
    }
}
```

- `io.seata.rm.datasource.AbstractConnectionProxy`
```java
// sign_c_320
public abstract class AbstractConnectionProxy implements Connection {

    // sign_m_320  创建 Statement
    @Override
    public PreparedStatement prepareStatement(String sql) throws SQLException {
        ...
        PreparedStatement targetPreparedStatement = null;
        ...
        if (targetPreparedStatement == null) {
            targetPreparedStatement = getTargetConnection().prepareStatement(sql); // 调用原连接创建底层 Statement
        }
        return new PreparedStatementProxy(this, targetPreparedStatement, sql); // 对 Statement 进行代理
    }

}
```

- `io.seata.rm.datasource.PreparedStatementProxy`
```java
// sign_c_330  Statement 代理
public class PreparedStatementProxy extends AbstractPreparedStatementProxy implements PreparedStatement, ParametersHolder {

    // sign_m_330  执行修改操作
    @Override
    public int executeUpdate() throws SQLException {
        // SQL 执行，ref: sign_m_510
        return ExecuteTemplate.execute(
            this,
            (statement, args) -> statement.executeUpdate() // sign_cb_330  底层 Statement 执行
        );
    }

}
```


---
## JDBC-模板
- 业务代码用常规 `JdbcTemplate` 即可自动使用 AT 事务

- `org.springframework.jdbc.core.JdbcTemplate`
```java
// sign_c_410  JDBC 模板
public class JdbcTemplate extends JdbcAccessor implements JdbcOperations {
    @Nullable
    private <T> T execute(PreparedStatementCreator psc, ...) throws DataAccessException {
        ...

        Connection con = DataSourceUtils.getConnection( // 相当于 dataSource.getConnection(); ref: sign_m_220
            obtainDataSource() // 返回的是连接池代理，ref: sign_c_220
        );
        PreparedStatement ps = null;
        try {
            ps = psc.createPreparedStatement(con); // 相当于 con.prepareStatement(this.sql); ref: sign_m_320
            T result = action.doInPreparedStatement(ps); // 相当于 int rows = ps.executeUpdate(); ref: sign_m_330
            ...
            return result;
        }
        ... // catch
        ... // finally
    }
}
```


---
## 执行-SQL
- `io.seata.rm.datasource.exec.ExecuteTemplate`
```java
// sign_c_510  执行模板
public class ExecuteTemplate {

    // sign_m_510
    public static <T, S extends Statement> T execute(
        StatementProxy<S> statementProxy, StatementCallback<T, S> statementCallback, ...
    ) throws SQLException {
        return execute(null, statementProxy, statementCallback, args); // ref: sign_m_511
    }
    
    // sign_m_511  具体执行（查找对应执行器）
    public static <T, S extends Statement> T execute(
        ..., StatementProxy<S> statementProxy, StatementCallback<T, S> statementCallback, ...
    ) throws SQLException {
        ... // 不是全局性且不是 AT，原语句执行

        String dbType = statementProxy.getConnectionProxy().getDbType();

        ... // 
        else {
            if (sqlRecognizers.size() == 1) {
                SQLRecognizer sqlRecognizer = sqlRecognizers.get(0);
                switch (sqlRecognizer.getSQLType()) {
                    case INSERT:
                        executor = EnhancedServiceLoader.load(InsertExecutor.class, dbType, ...);
                        break;
                    case UPDATE:
                        ...
                        else {
                            // 修改执行器，ref: sign_c_520
                            executor = new UpdateExecutor<>(statementProxy, statementCallback, sqlRecognizer);
                        }
                        break;
                    case DELETE:
                        ...
                        else {
                            executor = new DeleteExecutor<>(statementProxy, statementCallback, sqlRecognizer);
                        }
                        break;
                    ... // case SELECT_FOR_UPDATE:
                    ... // case INSERT_ON_DUPLICATE_UPDATE:
                    ... // case UPDATE_JOIN:
                    ... // default:
                }
            } ... // else
        }

        T rs;
        try {
            rs = executor.execute(args); // ref: sign_m_540
        } ... // catch 
        return rs;
    }

}
```

- `io.seata.rm.datasource.exec.UpdateExecutor`
```java
// sign_c_520  修改执行器
public class UpdateExecutor<T, S extends Statement> extends AbstractDMLBaseExecutor<T, S> {

    // sign_c_520  创建前镜像
    @Override
    protected TableRecords beforeImage() throws SQLException {
        ArrayList<List<Object>> paramAppenderList = new ArrayList<>();
        TableMeta tmeta = getTableMeta();
        String selectSQL = buildBeforeImageSQL(tmeta, paramAppenderList);
        return buildTableRecords(tmeta, selectSQL, paramAppenderList);
    }

    // sign_c_521  创建后镜像
    @Override
    protected TableRecords afterImage(TableRecords beforeImage) throws SQLException {
        TableMeta tmeta = getTableMeta();
        ...

        String selectSQL = buildAfterImageSQL(tmeta, beforeImage);
        ResultSet rs = null;
        try (PreparedStatement pst = statementProxy.getConnection().prepareStatement(selectSQL)) {
            SqlGenerateUtils.setParamForPk(beforeImage.pkRows(), getTableMeta().getPrimaryKeyOnlyName(), pst);
            rs = pst.executeQuery();
            return TableRecords.buildRecords(tmeta, rs);
        } ... // finally
    }
}
```

- `io.seata.rm.datasource.exec.AbstractDMLBaseExecutor`
  - 暂存 undo 日志参考：[RM-undo-日志及操作-暂存 sign_m_110](./RM-undo-日志及操作.md#暂存)
```java
// sign_c_530
public abstract class AbstractDMLBaseExecutor<T, S extends Statement> extends BaseTransactionalExecutor<T, S> {

    // sign_m_530
    @Override
    public T doExecute(Object... args) throws Throwable {
        AbstractConnectionProxy connectionProxy = statementProxy.getConnectionProxy();
        if (connectionProxy.getAutoCommit()) {
            return executeAutoCommitTrue(args);  // ref: sign_m_531
        } else {
            return executeAutoCommitFalse(args); // ref: sign_m_532
        }
    }

    // sign_m_531
    protected T executeAutoCommitTrue(Object[] args) throws Throwable {
        ConnectionProxy connectionProxy = statementProxy.getConnectionProxy();
        try {
            connectionProxy.changeAutoCommit();
            return new LockRetryPolicy(connectionProxy).execute(() -> { // 重试执行
                T result = executeAutoCommitFalse(args); // ref: sign_m_532
                connectionProxy.commit(); // 提交
                return result;
            });
        } catch (Exception e) {
            ... // 判断是否回滚
            throw e;
        } ... // finally
    }

    // sign_m_532
    protected T executeAutoCommitFalse(Object[] args) throws Exception {
        try {
            TableRecords beforeImage = beforeImage();           // 前镜像，ref: sign_c_520
            T result = statementCallback.execute(statementProxy.getTargetStatement(), args); // ref: sign_cb_330
            TableRecords afterImage = afterImage(beforeImage);  // 后镜像，ref: sign_c_521
            // 暂存 undo 日志，参考：[RM-undo-日志及操作-暂存 sign_m_110]。
            // 保存到 DB 参考: sign_cb_312 
            prepareUndoLog(beforeImage, afterImage);
            return result;
        } ... // catch
    }
}
```

- `io.seata.rm.datasource.exec.BaseTransactionalExecutor`
```java
// sign_c_540
public abstract class BaseTransactionalExecutor<T, S extends Statement> implements Executor<T> {

    // sign_m_540  执行
    @Override
    public T execute(Object... args) throws Throwable {
        String xid = RootContext.getXID();
        if (xid != null) {
            statementProxy.getConnectionProxy().bind(xid);
        }

        statementProxy.getConnectionProxy().setGlobalLockRequire(RootContext.requireGlobalLock());
        return doExecute(args); // ref: sign_m_530
    }

}
```


---
## 总结
- 先记录 undo 日志，再一起提交