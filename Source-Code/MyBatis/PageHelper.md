# MyBatis-PageHelper


---
## 总说明
- 源码仓库： https://github.com/pagehelper/Mybatis-PageHelper
- 克隆：`git clone https://github.com/pagehelper/Mybatis-PageHelper.git`
- 切分支（tag）：`git checkout master`
- JDK: `17`


---
## 单元测试
- 参考：`com.github.pagehelper.test.reasonable.PageTest`
```java
    @Test
    public void testMapperWithStartPage() {
        SqlSession sqlSession = MybatisReasonableHelper.getSqlSession();
        UserMapper userMapper = sqlSession.getMapper(UserMapper.class);
        try {
            // PageHelper.startPage(20, 50);    // 超出总页数时，会自动改为查询最后一页
            PageHelper.startPage(4, 50);                // 开启分页，ref: sign_m_110
            List<User> list = userMapper.selectAll();   // 分页拦截，ref: sign_m_210
            PageInfo<User> page = new PageInfo<User>(list);
        }
    }
```

- `hsqldb\mybatis-config-reasonable.xml`
```xml
<configuration>
    <plugins>
        <plugin interceptor="com.github.pagehelper.PageInterceptor">
            <property name="reasonable" value="true"/>
        </plugin>
    </plugins>
</configuration>
```

- `UserMapper.xml`
```xml
<mapper namespace="com.github.pagehelper.mapper.UserMapper">
    <select id="selectAll" resultType="User">
        select * from user order by id -- comment
    </select>
</mapper>
```


---
## 原理
### 开启分页
- `com.github.pagehelper.PageHelper`
```java
// sign_c_010
public class PageHelper extends PageMethod implements Dialect, BoundSqlInterceptor.Chain {

    // sign_m_010  后处理
    @Override
    public void afterAll() {
        // 这个方法即使不分页也会被执行，所以要判断 null
        AbstractHelperDialect delegate = autoDialect.getDelegate();
        if (delegate != null) {
            delegate.afterAll();
            autoDialect.clearDelegate();
        }
        clearPage();    // 移除本地变量，ref: sign_m_011
    }

    // sign_m_011  移除本地变量
    public static void clearPage() {
        LOCAL_PAGE.remove();
    }
}
```

- `com.github.pagehelper.page.PageMethod`
```java
public abstract class PageMethod {

    protected static final ThreadLocal<Page> LOCAL_PAGE    = new ThreadLocal<Page>();
    protected static       boolean           DEFAULT_COUNT = true;

    // sign_m_110 开启分页
    public static <E> Page<E> startPage(int pageNum, int pageSize) {
        return startPage(pageNum, pageSize, DEFAULT_COUNT); // 默认进行 COUNT(0) 查询
    }

    public static <E> Page<E> startPage(int pageNum, int pageSize, boolean count) {
        return startPage(pageNum, pageSize, count, null, null);
    }

    public static <E> Page<E> startPage(int pageNum, int pageSize, boolean count, Boolean reasonable, Boolean pageSizeZero) {
        Page<E> page = new Page<E>(pageNum, pageSize, count);
        page.setReasonable(reasonable);     // 分页合理化设置
        page.setPageSizeZero(pageSizeZero); // true 且 pageSize = 0 时返回全部结果，false 时分页
        ...
        setLocalPage(page);
        return page;
    }

    public static void setLocalPage(Page page) {
        LOCAL_PAGE.set(page);
    }
}
```

### 拦截器
- `com.github.pagehelper.PageInterceptor`
```java
@Intercepts({
    // 设置对目标接口和目标 (指定的方法名和参数类型) 方法进行拦截
    @Signature(type = Executor.class, method = "query", args = {
        MappedStatement.class, Object.class, RowBounds.class, ResultHandler.class
    }),
    @Signature(type = Executor.class, method = "query", args = {
        MappedStatement.class, Object.class, RowBounds.class, ResultHandler.class, CacheKey.class, BoundSql.class
    }),
})
public class PageInterceptor implements Interceptor {
    private volatile     Dialect    dialect;
    private              String     default_dialect_class = "com.github.pagehelper.PageHelper";

    @Override // 初始化 dialect
    public void setProperties(Properties properties) {
        ...
        String dialectClass = ... default_dialect_class;    // 用默认的
        Dialect tempDialect = ClassUtil.newInstance(dialectClass, properties);
        tempDialect.setProperties(properties);
        ...
        // 初始化完成后再设置值，保证 dialect 完成初始化。
        // 默认情况下，dialect 是 PageHelper 实例，ref: sign_c_010
        dialect = tempDialect;
    }

    // sign_m_210 分页拦截
    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        try {
            Object[] args = invocation.getArgs();
            MappedStatement ms = (MappedStatement) args[0];
            ...
            if (args.length == 4) { // 4 个参数时
                ...
            } else {                // 6 个参数时
                ...
            }
            ...
            List resultList;
            if (!dialect.skip(ms, parameter, rowBounds)) { // 需要分页
                ...
                // 判断是否需要进行 count 查询
                if (dialect.beforeCount(ms, parameter, rowBounds)) {
                    ... // 异步 Count 处理
                    else {
                        // 查询总数，将原接口改成 COUNT(0) 统计 SQL 再进行查询
                        Long count = count(executor, ms, parameter, rowBounds, null, boundSql);
                        // 处理查询总数，返回 true 时继续分页查询，false 时直接返回
                        if (!dialect.afterCount(count, parameter, rowBounds)) { // 将 count 设置到 Page 里面去
                            // 当查询总数为 0 时，直接返回空的结果
                            return dialect.afterPage(new ArrayList(), parameter, rowBounds);
                        }
                    }
                }
                resultList = ExecutorUtil.pageQuery( // 将原 SQL 改成分页 SQL，再执行查询
                    dialect, executor, ms, parameter, rowBounds, resultHandler, boundSql, cacheKey
                );
                ... // 异步 Count 处理
            } ... // else: 不分页，直接查询结果

            return dialect.afterPage(resultList, parameter, rowBounds); // 将 list 添加到 Page，并返回 Page 对象
        } finally {
            if (dialect != null) {
                dialect.afterAll(); // 清除线程变量。ref: sign_m_010
            }
        }
    }
}
```

### 总结
- 原理总体较简单
- 只在一个拦截器里处理（统计与数据查询）
- 最后返回 `Page<T>` 封装集合类