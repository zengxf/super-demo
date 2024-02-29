## 总说明
- 源码仓库： https://github.com/mybatis/mybatis-3
- 克隆：`git clone https://github.com/mybatis/mybatis-3.git`
- 切分支（tag）：`git checkout master`
- JDK: `17`
- Mapper 测试在 `org.apache.ibatis.submitted.*` 包下面


## 单元测试
- 参考：`org.apache.ibatis.submitted.extend.ExtendTest`
```java
  @BeforeAll
  static void setUp() throws Exception {
    try (Reader reader = Resources.getResourceAsReader("org/apache/ibatis/submitted/extend/ExtendConfig.xml")) {
      sqlSessionFactory = new SqlSessionFactoryBuilder().build(reader); // ref: sign_m_110
    }
  }

  @Test
  void testExtend() {
    try (SqlSession sqlSession = sqlSessionFactory.openSession()) {     // ref: sign_m_210
      ExtendMapper mapper = sqlSession.getMapper(ExtendMapper.class);   // ref: sign_m_310
      Child answer = mapper.selectChild();                              // ref: sign_m_410
    }
  }
```


## 原理
### 创建 SqlSessionFactory
- `org.apache.ibatis.session.SqlSessionFactoryBuilder`
```java
  // sign_m_110 构建工厂
  public SqlSessionFactory build(Reader reader) {
    return build(reader, null, null); // ref: sign_m_111
  }

  // sign_m_111
  public SqlSessionFactory build(Reader reader, String environment, Properties properties) {
    try {
      XMLConfigBuilder parser = new XMLConfigBuilder(reader, environment, properties);
      return build(parser.parse());   // 使用解析的配置，构建工厂，ref: sign_m_112 | sign_m_120
    } ... // catch finally
  }

  // sign_m_112 创建默认的工厂
  public SqlSessionFactory build(Configuration config) {
    return new DefaultSqlSessionFactory(config);  // ref: sign_c_210
  }
```

- `org.apache.ibatis.builder.xml.XMLConfigBuilder`
```java
// 解析 <configuration> xml 配置文件
public class XMLConfigBuilder extends BaseBuilder {
  // sign_m_120 解析配置
  public Configuration parse() {
    ...
    parseConfiguration(parser.evalNode("/configuration"));  // ref: sign_m_121
    return configuration;
  }
  
  // sign_m_121
  private void parseConfiguration(XNode root) {
    try {
      // 先读取属性
      propertiesElement(root.evalNode("properties"));   // nop
      Properties settings = settingsAsProperties(root.evalNode("settings"));  // nop
      loadCustomVfsImpl(settings);                      // nop
      loadCustomLogImpl(settings);                      // nop
      typeAliasesElement(root.evalNode("typeAliases")); // nop
      pluginsElement(root.evalNode("plugins"));         // nop
      objectFactoryElement(root.evalNode("objectFactory"));               // nop
      objectWrapperFactoryElement(root.evalNode("objectWrapperFactory")); // nop
      reflectorFactoryElement(root.evalNode("reflectorFactory"));         // nop
      settingsElement(settings);                        // nop

      // 在 objectFactory 和 objectWrapperFactory 之后读取
      environmentsElement(root.evalNode("environments")); // 配置环境
      databaseIdProviderElement(root.evalNode("databaseIdProvider"));     // nop
      typeHandlersElement(root.evalNode("typeHandlers"));                 // nop
      mappersElement(root.evalNode("mappers"));           // 解析 mapper, ref: sign_m_122
    } ... // catch
  }

  // sign_m_122  解析 mapper
  private void mappersElement(XNode context) throws Exception {
    ...
    for (XNode child : context.getChildren()) {
      if ("package".equals(child.getName())) {
        ...
      } else {
        String resource = child.getStringAttribute("resource");
        String url = child.getStringAttribute("url");
        String mapperClass = child.getStringAttribute("class");
        if (resource != null && url == null && mapperClass == null) {
          ErrorContext.instance().resource(resource);
          try (InputStream inputStream = Resources.getResourceAsStream(resource)) {
            XMLMapperBuilder mapperParser = new XMLMapperBuilder(inputStream, configuration, resource,
                configuration.getSqlFragments());
            mapperParser.parse(); // ref: sign_m_130
          }
        } else if (resource == null && url != null && mapperClass == null) {
          ...
        } else if (resource == null && url == null && mapperClass != null) {
          ...
        } ... // else { throw new BuilderException }
      }
    }
  }
}
```

- `org.apache.ibatis.builder.xml.XMLMapperBuilder`
```java
// 解析 <mapper> xml 配置文件
public class XMLMapperBuilder extends BaseBuilder {
  // sign_m_130
  public void parse() {
    if (!configuration.isResourceLoaded(resource)) {
      configurationElement(parser.evalNode("/mapper")); // ref: sign_m_131
      configuration.addLoadedResource(resource);
      bindMapperForNamespace();
    }
    configuration.parsePendingResultMaps(false);
    configuration.parsePendingCacheRefs(false);
    configuration.parsePendingStatements(false);
  }
  
  // sign_m_131
  private void configurationElement(XNode context) {
    try {
      String namespace = context.getStringAttribute("namespace");
      ...
      builderAssistant.setCurrentNamespace(namespace);
      cacheRefElement(context.evalNode("cache-ref"));
      cacheElement(context.evalNode("cache"));
      parameterMapElement(context.evalNodes("/mapper/parameterMap"));
      resultMapElements(context.evalNodes("/mapper/resultMap"));                    // resultMap 映射
      sqlElement(context.evalNodes("/mapper/sql"));
      buildStatementFromContext(context.evalNodes("select|insert|update|delete"));  // 具体 SQL 方法处理，ref: sign_m_132
    } ... // catch
  }

  // sign_m_132
  private void buildStatementFromContext(List<XNode> list) {
    ...
    buildStatementFromContext(list, null);    // ref: sign_m_133
  }
  
  // sign_m_133
  private void buildStatementFromContext(List<XNode> list, String requiredDatabaseId) {
    for (XNode context : list) {
      // context 相当于 xml 里面的一个 select 方法声明
      final XMLStatementBuilder statementParser = new XMLStatementBuilder(
        configuration, builderAssistant, context, requiredDatabaseId
      );
      try {
        statementParser.parseStatementNode(); // ref: sign_m_140
      } ... // catch
    }
  }
}
```

- `org.apache.ibatis.builder.xml.XMLStatementBuilder`
```java
// 解析 <select> 等 xml 片段
public class XMLStatementBuilder extends BaseBuilder {
  // sign_m_140
  public void parseStatementNode() {
    ...

    String nodeName = context.getNode().getNodeName();
    SqlCommandType sqlCommandType = SqlCommandType.valueOf(nodeName.toUpperCase(Locale.ENGLISH));
    boolean isSelect = sqlCommandType == SqlCommandType.SELECT;
    ...

    String parameterType = context.getStringAttribute("parameterType");
    ...
    // Parse the SQL (pre: <selectKey> and <include> were parsed and removed)
    KeyGenerator keyGenerator;
    ...
    String parameterMap = context.getStringAttribute("parameterMap");
    String resultType = context.getStringAttribute("resultType");
    Class<?> resultTypeClass = resolveClass(resultType);
    String resultMap = context.getStringAttribute("resultMap");
    ...

    builderAssistant.addMappedStatement(...); // 将语句块添加到配置，ref: sign_m_150
  }
}
```

- `org.apache.ibatis.builder.MapperBuilderAssistant`
```java
public class MapperBuilderAssistant extends BaseBuilder {
  // sign_m_150
  public MappedStatement addMappedStatement(String id, SqlSource sqlSource, StatementType statementType, ...) {
    ...
    MappedStatement.Builder statementBuilder = ...; // 填充 builder
    ...
    MappedStatement statement = statementBuilder.build();
    configuration.addMappedStatement(statement);    // 将解析的语句块添加到配置
    return statement;
  }
}
```

### 获取 SqlSession
- `org.apache.ibatis.session.defaults.DefaultSqlSessionFactory`
```java
// sign_c_210
public class DefaultSqlSessionFactory implements SqlSessionFactory {
  private final Configuration configuration;
  // sign_m_210
  @Override
  public SqlSession openSession() {
    return openSessionFromDataSource(configuration.getDefaultExecutorType(), null, false);  // ref: sign_m_211
  }
  
  // sign_m_211
  private SqlSession openSessionFromDataSource(ExecutorType execType, TransactionIsolationLevel level, boolean autoCommit) {
    Transaction tx = null;
    try {
      final Environment environment = configuration.getEnvironment();
      final TransactionFactory transactionFactory = getTransactionFactoryFromEnvironment(environment);
      tx = transactionFactory.newTransaction(environment.getDataSource(), level, autoCommit);
      final Executor executor = configuration.newExecutor(tx, execType);  // ref: sign_m_220
      return new DefaultSqlSession(configuration, executor, autoCommit);  // 返回默认的 session, ref: sign_c_310
    } ... // catch finally 
  }
}
```

- `org.apache.ibatis.session.Configuration`
```java
  // sign_m_220
  public Executor newExecutor(Transaction transaction, ExecutorType executorType) {
    executorType = executorType == null ? defaultExecutorType : executorType; // 最终值为: SIMPLE
    Executor executor;
    if (ExecutorType.BATCH == executorType) {
      executor = new BatchExecutor(this, transaction);
    } else if (ExecutorType.REUSE == executorType) {
      executor = new ReuseExecutor(this, transaction);
    } else {            // 进入此逻辑
      executor = new SimpleExecutor(this, transaction);
    }
    if (cacheEnabled) { // 进入此逻辑
      executor = new CachingExecutor(executor);
    }
    return (Executor) interceptorChain.pluginAll(executor); // 组装‘拦截链’
  }
```

### 获取 Mapper
- `org.apache.ibatis.session.defaults.DefaultSqlSession`
```java
// sign_c_310
public class DefaultSqlSession implements SqlSession {
  private final Configuration configuration;
  private final Executor executor;
  private final boolean autoCommit;

  // sign_m_310
  @Override
  public <T> T getMapper(Class<T> type) {
    return configuration.getMapper(type, this); // ref: sign_m_320
  }
}
```

- `org.apache.ibatis.session.Configuration`
```java
  // sign_m_320
  public <T> T getMapper(Class<T> type, SqlSession sqlSession) {
    return mapperRegistry.getMapper(type, sqlSession);  // ref: sign_m_330
  }
```

- `org.apache.ibatis.binding.MapperRegistry`
```java
  // sign_m_330
  public <T> T getMapper(Class<T> type, SqlSession sqlSession) {
    final MapperProxyFactory<T> mapperProxyFactory = (MapperProxyFactory<T>) knownMappers.get(type);
    ...
    try {
      return mapperProxyFactory.newInstance(sqlSession);  // 创建 Mapper 动态代理，ref: sign_m_340
    } ... // catch
  }
```

- `org.apache.ibatis.binding.MapperProxyFactory`
```java
  // sign_m_340  创建 Mapper 动态代理
  public T newInstance(SqlSession sqlSession) {
    // 创建 JDK 代理用的 InvocationHandler, ref: sign_c_410
    final MapperProxy<T> mapperProxy = new MapperProxy<>(sqlSession, mapperInterface, methodCache);
    return newInstance(mapperProxy);  // 创建 JDK 动态代理，ref: sign_m_341
  }

  // sign_m_341  创建 JDK 动态代理
  protected T newInstance(MapperProxy<T> mapperProxy) {
    return (T) Proxy.newProxyInstance(mapperInterface.getClassLoader(), new Class[] { mapperInterface }, mapperProxy);
  }
```

### 执行 Mapper 方法
- `org.apache.ibatis.binding.MapperProxy`
```java
// sign_c_410
public class MapperProxy<T> implements InvocationHandler, Serializable {
  private final SqlSession sqlSession;
  private final Class<T> mapperInterface;
  private final Map<Method, MapperMethodInvoker> methodCache;

  // sign_m_410  调用 Mapper 方法时，底层操作由此方法完成
  @Override
  public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
    try {
      ...
      return cachedInvoker(method)                      // ref: sign_m_411
             .invoke(proxy, method, args, sqlSession);  // ref: sign_m_412
    } ... // catch
  }

  // sign_m_411
  private MapperMethodInvoker cachedInvoker(Method method) throws Throwable {
    try {
      return MapUtil.computeIfAbsent(methodCache, method, m -> {
        if (!m.isDefault()) { // 不是 default 方法，进入此逻辑
          return new PlainMethodInvoker(  // ref: sign_c_411
            new MapperMethod(mapperInterface, method, sqlSession.getConfiguration())  // ref: sign_c_420 | sign_cm_420
          );
        }
        ... // default 方法处理
      });
    } ...   // catch
  }

  // sign_c_411
  private static class PlainMethodInvoker implements MapperMethodInvoker {
    private final MapperMethod mapperMethod;
    // sign_m_412
    @Override
    public Object invoke(Object proxy, Method method, Object[] args, SqlSession sqlSession) throws Throwable {
      return mapperMethod.execute(sqlSession, args);  // ref: sign_m_420
    }
  }
}
```

- `org.apache.ibatis.binding.MapperMethod`
```java
// sign_c_420
public class MapperMethod {
  private final SqlCommand command;
  private final MethodSignature method;

  // sign_cm_420
  public MapperMethod(Class<?> mapperInterface, Method method, Configuration config) {
    this.command = new SqlCommand(config, mapperInterface, method);
    this.method = new MethodSignature(config, mapperInterface, method);
  }

  // sign_m_420  执行 SQL
  public Object execute(SqlSession sqlSession, Object[] args) {
    Object result;
    switch (command.getType()) {
      case INSERT: // sqlSession.insert
      case UPDATE: // sqlSession.update
      case DELETE: // sqlSession.delete
      case SELECT:
        if (method.returnsVoid() && method.hasResultHandler()) {  // sqlSession.select
        } else if (method.returnsMany()) {    // sqlSession.selectList
        } else if (method.returnsMap()) {     // sqlSession.selectMap
        } else if (method.returnsCursor()) {  // sqlSession.selectCursor
        } else {
          Object param = method.convertArgsToSqlCommandParam(args);
          result = sqlSession.selectOne(command.getName(), param);  // ref: sign_m_430
          ...
        }
        break;
      ...
    }
    ...
    return result;
  }
}
```

- `org.apache.ibatis.session.defaults.DefaultSqlSession`
  - ref: `sign_c_310`
```java
  // sign_m_430
  @Override
  public <T> T selectOne(String statement, Object parameter) {
    // 0 个结果上返回 null，多个结果抛出异常。
    List<T> list = this.selectList(statement, parameter);
    if (list.size() == 1) {
      return list.get(0); // ref: sign_m_431
    }
    ...
  }
  
  // sign_m_431
  @Override
  public <E> List<E> selectList(String statement, Object parameter) {
    return this.selectList(statement, parameter, RowBounds.DEFAULT);  // ref: sign_m_432
  }  
  
  // sign_m_432
  @Override
  public <E> List<E> selectList(String statement, Object parameter, RowBounds rowBounds) {
    return selectList(statement, parameter, rowBounds, Executor.NO_RESULT_HANDLER); // ref: sign_m_433
  }

  // sign_m_433
  private <E> List<E> selectList(String statement, Object parameter, RowBounds rowBounds, ResultHandler handler) {
    try {
      MappedStatement ms = configuration.getMappedStatement(statement);
      dirty |= ms.isDirtySelect();
      return executor.query(ms, wrapCollection(parameter), rowBounds, handler); // ref: sign_m_440
    } ... // catch finally
  }
```

- `org.apache.ibatis.executor.CachingExecutor`
```java
public class CachingExecutor implements Executor {
  private final Executor delegate;
  private final TransactionalCacheManager tcm = new TransactionalCacheManager();  // 缓存管理器

  // sign_m_440
  @Override
  public <E> List<E> query(
    MappedStatement ms, Object parameterObject, RowBounds rowBounds, ResultHandler resultHandler
  ) throws SQLException {
    BoundSql boundSql = ms.getBoundSql(parameterObject);
    CacheKey key = createCacheKey(ms, parameterObject, rowBounds, boundSql);
    return query(ms, parameterObject, rowBounds, resultHandler, key, boundSql);           // ref: sign_m_441
  }

  // sign_m_441
  @Override
  public <E> List<E> query(
    MappedStatement ms, Object parameterObject, RowBounds rowBounds, ResultHandler resultHandler,
    CacheKey key, BoundSql boundSql
  ) throws SQLException {
    Cache cache = ms.getCache();
    if (cache != null) {
      ... // 有缓存，则处理缓存，未过期则返回
    }
    // delegate 为 SimpleExecutor 实例 (继承 BaseExecutor)
    return delegate.query(ms, parameterObject, rowBounds, resultHandler, key, boundSql);  // ref: sign_m_510
  }
}
```

#### 底层查询
- `org.apache.ibatis.executor.BaseExecutor`
```java
  // sign_m_510
  @Override
  public <E> List<E> query(
    MappedStatement ms, Object parameter, RowBounds rowBounds, ResultHandler resultHandler,
    CacheKey key, BoundSql boundSql
  ) throws SQLException {
    ...
    List<E> list;
    try {
      queryStack++;
      list = resultHandler == null ? (List<E>) localCache.getObject(key) : null;
      if (list != null) {
        handleLocallyCachedOutputParameters(ms, key, parameter, boundSql);
      } else {  // 没有缓存进入此逻辑
        list = queryFromDatabase(ms, parameter, rowBounds, resultHandler, key, boundSql); // ref: sign_m_511
      }
    } finally {
      queryStack--;
    }
    ...
    return list;
  }
  
  // sign_m_511
  private <E> List<E> queryFromDatabase(
    MappedStatement ms, Object parameter, RowBounds rowBounds,
    ResultHandler resultHandler, CacheKey key, BoundSql boundSql
  ) throws SQLException {
    List<E> list;
    localCache.putObject(key, EXECUTION_PLACEHOLDER);
    try {
      list = doQuery(ms, parameter, rowBounds, resultHandler, boundSql);  // ref: sign_m_520
    } finally {
      localCache.removeObject(key);
    }
    localCache.putObject(key, list);
    if (ms.getStatementType() == StatementType.CALLABLE) {
      localOutputParameterCache.putObject(key, parameter);
    }
    return list;
  }
```

- `org.apache.ibatis.executor.SimpleExecutor`
```java
  // sign_m_520
  @Override
  public <E> List<E> doQuery(
    MappedStatement ms, Object parameter, RowBounds rowBounds, ResultHandler resultHandler,
    BoundSql boundSql
  ) throws SQLException {
    Statement stmt = null;
    try {
      Configuration configuration = ms.getConfiguration();
      StatementHandler handler = configuration.newStatementHandler( // 创建处理器并设置‘拦截链’，ref: sign_m_530
        wrapper, ms, parameter, rowBounds, resultHandler, boundSql
      );
      stmt = prepareStatement(handler, ms.getStatementLog()); // ref: sign_m_521
      return handler.query(stmt, resultHandler);              // ref: sign_m_541
    } finally {
      closeStatement(stmt);
    }
  }

  // sign_m_521
  private Statement prepareStatement(StatementHandler handler, Log statementLog) throws SQLException {
    Statement stmt;
    Connection connection = getConnection(statementLog); // 获取 JDBC 连接
    stmt = handler.prepare(connection, transaction.getTimeout()); // 获取 JDBC Statement, ref: sign_m_540
    handler.parameterize(stmt); // 处理参数
    return stmt;
  }
```

- `org.apache.ibatis.session.Configuration`
```java
  // sign_m_530 创建处理器并设置‘拦截链’
  public StatementHandler newStatementHandler(
    Executor executor, MappedStatement mappedStatement,
    Object parameterObject, RowBounds rowBounds, ResultHandler resultHandler, BoundSql boundSql
  ) {
    StatementHandler statementHandler = new RoutingStatementHandler(executor, mappedStatement, parameterObject,
        rowBounds, resultHandler, boundSql);  // ref: sign_cm_540
    return (StatementHandler) interceptorChain.pluginAll(statementHandler); // 设置‘拦截链’
  }
```

- `org.apache.ibatis.executor.statement.RoutingStatementHandler`
```java
public class RoutingStatementHandler implements StatementHandler {

  private final StatementHandler delegate;

  // sign_cm_540
  public RoutingStatementHandler(
    Executor executor, MappedStatement ms, Object parameter, RowBounds rowBounds,
    ResultHandler resultHandler, BoundSql boundSql
  ) {
    switch (ms.getStatementType()) {
      case STATEMENT:
        delegate = new SimpleStatementHandler(executor, ms, parameter, rowBounds, resultHandler, boundSql);
      case PREPARED:  // 进入此逻辑，ref: sign_cm_550
        delegate = new PreparedStatementHandler(executor, ms, parameter, rowBounds, resultHandler, boundSql);
      case CALLABLE:
        delegate = new CallableStatementHandler(executor, ms, parameter, rowBounds, resultHandler, boundSql);
      ... // default Exception
    }
  }
  
  // sign_m_540  获取 JDBC Statement
  @Override
  public Statement prepare(Connection connection, Integer transactionTimeout) throws SQLException {
    return delegate.prepare(connection, transactionTimeout);  // ref: sign_m_550
  }
  
  // sign_m_541 查询
  @Override
  public <E> List<E> query(Statement statement, ResultHandler resultHandler) throws SQLException {
    return delegate.query(statement, resultHandler);  // ref: sign_m_561
  }
}
```

- `org.apache.ibatis.executor.statement.BaseStatementHandler`
```java
  // sign_cm_550
  protected BaseStatementHandler(Executor executor, MappedStatement mappedStatement, ..., BoundSql boundSql) {
    this.configuration = mappedStatement.getConfiguration();
    this.executor = executor;
    ....
    this.boundSql = boundSql;
    this.parameterHandler = configuration.newParameterHandler(...); // 创建参数处理器，并设置‘拦截链’
    this.resultSetHandler = configuration.newResultSetHandler(...); // 创建结果处理器，并设置‘拦截链’
  }

  // sign_m_550
  @Override
  public Statement prepare(Connection connection, Integer transactionTimeout) throws SQLException {
    ...
    Statement statement = null;
    try {
      statement = instantiateStatement(connection); // ref: sign_m_560
      setStatementTimeout(statement, transactionTimeout); // 设置超时
      setFetchSize(statement);  // 设置拉取行数
      return statement;
    } ... // catch
  }
```

- `org.apache.ibatis.executor.statement.PreparedStatementHandler`
```java
  // sign_m_560  底层 JDBC 创建 Statement
  @Override
  protected Statement instantiateStatement(Connection connection) throws SQLException {
    String sql = boundSql.getSql();
    ...
    if (mappedStatement.getResultSetType() == ResultSetType.DEFAULT) {  // 进入此逻辑
      return connection.prepareStatement(sql);  // JDBC 接口
    } else {
      return connection.prepareStatement(...);  // JDBC 接口
    }
  }
  
  // sign_m_561  底层 JDBC 执行查询
  @Override
  public <E> List<E> query(Statement statement, ResultHandler resultHandler) throws SQLException {
    PreparedStatement ps = (PreparedStatement) statement;
    ps.execute(); // 执行 SQL 查询
    return resultSetHandler.handleResultSets(ps); // 处理查询结果(封装返回)
  }
```