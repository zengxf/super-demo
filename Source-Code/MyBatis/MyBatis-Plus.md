## 总说明
- 源码仓库： https://github.com/baomidou/mybatis-plus
- 克隆：`git clone https://github.com/baomidou/mybatis-plus.git`
- 切分支（tag）：`git checkout 3.0`
- JDK: `21`


## 单元测试
### 添加方法-UT
- 参考：`com.baomidou.mybatisplus.core.MybatisXMLConfigBuilderTest`
```java
    @Test
    void parse() throws IOException {
        ResourceLoader loader = new DefaultResourceLoader();
        Resource resource = loader.getResource("classpath:/MybatisXMLConfigBuilderTest.xml");
        MybatisXMLConfigBuilder builder = new MybatisXMLConfigBuilder(resource.getInputStream(), null); // ref: sign_c_110 | sign_cm_110
        Configuration configuration = builder.parse(); // ref: sign_m_110
        MappedStatement mappedStatement = configuration.getMappedStatement(..."EntityMapper.selectCount");
    }

    interface EntityMapper extends BaseMapper<Entity> { }

    @TableName(autoResultMap = true)
    static class Entity {
        private Long id;
        private String name;
    }
```

- `MybatisXMLConfigBuilderTest.xml`
```xml
<configuration>
    <mappers>
        <mapper class="com.baomidou.mybatisplus.core.MybatisXMLConfigBuilderTest$EntityMapper"/>
    </mappers>
</configuration>
```

### 完整测试
- 参考：`com.baomidou.mybatisplus.test.MybatisTest`
```java
    private static SqlSessionFactory sqlSessionFactory;

    @BeforeAll
    public static void init() throws IOException, SQLException {
        Reader reader = Resources.getResourceAsReader("mybatis-config.xml");
        sqlSessionFactory = new MybatisSqlSessionFactoryBuilder().build(reader);    // 关键部分

        Configuration configuration = sqlSessionFactory.getConfiguration();
        TypeHandlerRegistry typeHandlerRegistry = configuration.getTypeHandlerRegistry();
        typeHandlerRegistry.register(AgeEnum.class, MybatisEnumTypeHandler.class);  // 注册枚举类型处理器

        DataSource dataSource = sqlSessionFactory.getConfiguration().getEnvironment().getDataSource();
        Connection connection = dataSource.getConnection();                         // 获取连接执行脚本
        ScriptRunner scriptRunner = new ScriptRunner(connection);
        scriptRunner.runScript(Resources.getResourceAsReader("h2/user.ddl.sql"));
    }

    @Test
    void test() {
        try (SqlSession sqlSession = sqlSessionFactory.openSession(true)) {
            H2UserMapper mapper = sqlSession.getMapper(H2UserMapper.class); // 添加 Mapper, ref: sign_m_130
            mapper.myInsertWithNameVersion("test", 2);
            H2User h2User = new H2User(...);
            mapper.insert(h2User);
        }
    }
```

### Spring 测试
- 参考：`com.baomidou.mybatisplus.test.h2.H2StudentMapperTest`
```java
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
@ExtendWith(SpringExtension.class)
@ContextConfiguration(locations = {"classpath:h2/spring-test-h2.xml"})
class H2StudentMapperTest {
    @Resource
    protected H2StudentMapper studentMapper;

    @Test
    void testIn() {
        LambdaQueryWrapper<H2Student> wrapper = Wrappers.<H2Student>lambdaQuery()
            .in(H2Student::getName, Arrays.asList("a", "b"));
        List<H2Student> list = studentMapper.selectList(wrapper);
    }
}
```


## 原理
### 添加方法
- `com.baomidou.mybatisplus.core.MybatisXMLConfigBuilder`
  - 参考：[MyBatis-创建-SqlSessionFactory sign_m_121](MyBatis.md#创建SqlSessionFactory)
```java
// sign_c_110
// 从 MyBatis 的 XMLConfigBuilder 复制过来的, 使用自己的 MybatisConfiguration 而不是 Configuration
public class MybatisXMLConfigBuilder extends BaseBuilder {
    // sign_cm_110
    private MybatisXMLConfigBuilder(XPathParser parser, String environment, Properties props) {
        super(new MybatisConfiguration()); // 传自己的 MybatisConfiguration 实例，ref: sign_c_120
        ...
    }

    // sign_m_110
    public Configuration parse() {
        ...
        parseConfiguration(parser.evalNode("/configuration")); // ref: sign_m_111
        return configuration;
    }

    // sign_m_111
    private void parseConfiguration(XNode root) {
        try {
            // (类似的) 参考：[MyBatis-创建-SqlSessionFactory sign_m_121]
            ...
            mapperElement(root.evalNode("mappers")); // ref: sign_m_112
        } ... // catch
    }

    // sign_m_112  解析 Mapper 配置
    private void mapperElement(XNode parent) throws Exception {
        if (parent != null) {
            for (XNode child : parent.getChildren()) {
                if ("package".equals(child.getName())) {
                    ...
                } else {
                    String resource = child.getStringAttribute("resource");
                    String url = child.getStringAttribute("url");
                    String mapperClass = child.getStringAttribute("class");
                    if (resource != null && url == null && mapperClass == null) {
                        ...
                    } else if (resource == null && url != null && mapperClass == null) {
                        ...
                    } else if (resource == null && url == null && mapperClass != null) {
                        Class<?> mapperInterface = Resources.classForName(mapperClass);
                        configuration.addMapper(mapperInterface); // 注册 Mappger, ref: sign_m_120
                    } ... // else {}
                }
            }
        }
    }
}
```

- `com.baomidou.mybatisplus.core.MybatisConfiguration`
```java
// sign_c_120 替换默认的 Configuration 类
public class MybatisConfiguration extends Configuration {
    // Mapper 注册
    protected MybatisMapperRegistry mybatisMapperRegistry = new MybatisMapperRegistry(this); // ref: sign_c_130 | sign_cm_130

    // sign_m_120  注册 Mappger
    @Override
    public <T> void addMapper(Class<T> type) {
        mybatisMapperRegistry.addMapper(type); // ref: sign_m_130
    }
}
```

- `com.baomidou.mybatisplus.core.MybatisMapperRegistry`
  - 参考：[MyBatis-获取-Mapper sign_m_330](MyBatis.md#获取-Mapper)
```java
// sign_c_130  继承自 MapperRegistry
public class MybatisMapperRegistry extends MapperRegistry {
    private Configuration config; // 实际是 MybatisConfiguration 实例，ref: sign_c_120
    private Map<Class<?>, MybatisMapperProxyFactory<?>> knownMappers = new ConcurrentHashMap<>();

    // sign_cm_130
    public MybatisMapperRegistry(Configuration config) {
        super(config);
        this.config = config;
    }

    // sign_m_130
    @Override
    public <T> void addMapper(Class<T> type) {
        if (type.isInterface()) {
            ...
            try {
                knownMappers.put(type, new MybatisMapperProxyFactory<>(type)); // 会在 getMapper(T) 时调用，参考：[MyBatis-获取-Mapper sign_m_330]
                MybatisMapperAnnotationBuilder parser = new MybatisMapperAnnotationBuilder(config, type); // ref: sign_c_140 | sign_cm_140
                parser.parse(); // ref: sign_m_140
            } ... // finally {}
        }
    }
}
```

- `com.baomidou.mybatisplus.core.MybatisMapperAnnotationBuilder`
```java
// sign_c_140
public class MybatisMapperAnnotationBuilder extends MapperAnnotationBuilder {
    private static Set<Class<? extends Annotation>> statementAnnotationTypes = 
        Stream.of(
            Select.class, Update.class, Insert.class, Delete.class, 
            SelectProvider.class, UpdateProvider.class, InsertProvider.class, DeleteProvider.class
        ).collect(Collectors.toSet());
    
    // sign_cm_140
    public MybatisMapperAnnotationBuilder(Configuration configuration, Class<?> type) {
        super(configuration, type); // configuration 为 MybatisConfiguration 实例，ref: sign_c_120
        this.assistant = new MybatisMapperBuilderAssistant(configuration, resource);
        ...
    }

    // sign_m_140
    @Override
    public void parse() {
        String resource = type.toString();
        if (!configuration.isResourceLoaded(resource)) {
            ... // MyBatis 那套解析逻辑
            try {
                if (GlobalConfigUtils.isSupperMapperChildren(configuration, type)) { // 判断 type 是不是继承 Mapper 接口
                    // 自己继承 BaseMapper，就会进入此逻辑
                    parserInjector(); // 注入基础方法，ref: sign_m_141
                }
            } ... // catch
        }
        ...
    }

    // sign_m_141 注入基础方法
    void parserInjector() {
        GlobalConfigUtils.getSqlInjector(configuration) // 返回 DefaultSqlInjector 实例, ref: sign_c_150
            .inspectInject(assistant, type); // 解析 BaseMapper 基础方法，ref: sign_m_160
    }
}
```

- `com.baomidou.mybatisplus.core.injector.DefaultSqlInjector`
```java
// sign_c_150  SQL 默认注入器
public class DefaultSqlInjector extends AbstractSqlInjector {
    // sign_m_150
    @Override
    public List<AbstractMethod> getMethodList(Class<?> mapperClass, TableInfo tableInfo) {
        Stream.Builder<AbstractMethod> builder = Stream.<AbstractMethod>builder()
            .add(new Insert())
            .add(new Delete())
            .add(new Update())
            .add(new SelectCount()) // ref: sign_c_180
            .add(new SelectMaps())
            .add(new SelectObjs())
            .add(new SelectList());
        if (tableInfo.havePK()) {
            builder.add(new DeleteById())
                .add(new DeleteBatchByIds())
                .add(new UpdateById())
                .add(new SelectById())
                .add(new SelectBatchByIds());
        } ... // else
        return builder.build().collect(toList());
    }
}
```

- `com.baomidou.mybatisplus.core.injector.AbstractSqlInjector`
```java
// sign_c_160  SQL 自动注入器
public abstract class AbstractSqlInjector implements ISqlInjector {
    // sign_m_160  将 BaseMapper 的基础方法转成 SQL 语句注入到 configuration (MyBatis) 中去
    @Override
    public void inspectInject(MapperBuilderAssistant builderAssistant, Class<?> mapperClass) {
        Class<?> modelClass = ReflectionKit.getSuperClassGenericType(mapperClass, Mapper.class, 0); // 获取实体类
        if (modelClass != null) {
            ... // 是否已注册判断处理

                // 初始化表信息(读取：表名、主键、字段等)
                TableInfo tableInfo = TableInfoHelper.initTableInfo(builderAssistant, modelClass);
                List<AbstractMethod> methodList = this.getMethodList(mapperClass, tableInfo); // ref: sign_m_150
                if (CollectionUtils.isNotEmpty(methodList)) {
                    // 循环注入自定义方法
                    methodList.forEach(m -> m.inject(builderAssistant, mapperClass, modelClass, tableInfo)); // ref: sign_m_170
                } ... // else
        }
    }
}
```

- `com.baomidou.mybatisplus.core.injector.AbstractMethod`
  - 参考：[MyBatis-创建-SqlSessionFactory sign_m_150](MyBatis.md#创建SqlSessionFactory)
```java
public abstract class AbstractMethod implements Constants {
    // sign_m_170 注入自定义方法
    public void inject(MapperBuilderAssistant builderAssistant, Class<?> mapperClass, Class<?> modelClass, TableInfo tableInfo) {
        this.configuration = builderAssistant.getConfiguration();
        this.builderAssistant = builderAssistant;
        this.languageDriver = configuration.getDefaultScriptingLanguageInstance();
        /* 注入自定义方法 */
        injectMappedStatement(mapperClass, modelClass, tableInfo); // 以 SelectCount 为例，ref: sign_c_180 | sign_m_180
    }

    // sign_m_171
    protected MappedStatement addSelectMappedStatementForOther(Class<?> mapperClass, String id, SqlSource sqlSource,
                                                               Class<?> resultType) {
        return addMappedStatement( // ref: sign_m_172
            mapperClass, id, sqlSource, SqlCommandType.SELECT, ...
        ); 
    }

    // sign_m_172  添加 MappedStatement 到 Mybatis 容器
    protected MappedStatement addMappedStatement(
        Class<?> mapperClass, String id, SqlSource sqlSource,
        SqlCommandType sqlCommandType, ...
    ) {
        ... // 判断是否已添加处理
        // 构建 MappedStatement 并添加到 configuration
        return builderAssistant.addMappedStatement(...); // 参考：[MyBatis-创建-SqlSessionFactory sign_m_150]
    }
}
```

- `com.baomidou.mybatisplus.core.injector.methods.SelectCount`
  - SQL 格式化参考：[#SQL-格式化](#SQL-格式化)
```java
// sign_c_180
public class SelectCount extends AbstractMethod {
    // sign_m_180  拼接 SQL 语句注入到 configuration (MyBatis) 中去
    @Override
    public MappedStatement injectMappedStatement(Class<?> mapperClass, Class<?> modelClass, TableInfo tableInfo) {
        SqlMethod sqlMethod = SqlMethod.SELECT_COUNT;
        String sql = String.format(
            sqlMethod.getSql(), // "<script>%s SELECT COUNT(%s) AS total FROM %s %s %s\n</script>"
            /*
            <if test="ew != null and ew.sqlFirst != null">
                ${ew.sqlFirst}
            </if>
            */
            sqlFirst(),
            /*
            <choose>
                <when test="ew != null and ew.sqlSelect != null">
                    ${ew.sqlSelect}
                </when>
                <otherwise>*</otherwise>
            </choose>
            */
            sqlCount(), 
            tableInfo.getTableName(), // 表名：entity
            /*
            <if test="ew != null">
                <bind name="_sgEs_" value="ew.sqlSegment != null and ew.sqlSegment != ''"/>
                <where>
                    <if test="ew.entity != null">
                        <if test="ew.entity.id != null">id=#{ew.entity.id}</if>
                        <if test="ew.entity['name'] != null"> AND name=#{ew.entity.name}</if>
                    </if>
                    <if test="_sgEs_ and ew.nonEmptyOfNormal">
                        AND ${ew.sqlSegment}
                    </if>
                </where>
                <if test="_sgEs_ and ew.emptyOfNormal">
                    ${ew.sqlSegment}
                </if>
            </if>
            */
            sqlWhereEntityWrapper(true, tableInfo),
            /*
            <if test="ew != null and ew.sqlComment != null">
                ${ew.sqlComment}
            </if>
            */
            sqlComment()
        );
        SqlSource sqlSource = super.createSqlSource(configuration, sql, modelClass);
        return this.addSelectMappedStatementForOther(mapperClass, methodName, sqlSource, Long.class); // ref: sign_m_171
    }
}
```

- `com.baomidou.mybatisplus.core.injector.methods.SelectList`
  - SQL 格式化参考：[#SQL-格式化](#SQL-格式化)
```java
    public MappedStatement injectMappedStatement(Class<?> mapperClass, Class<?> modelClass, TableInfo tableInfo) {
        SqlMethod sqlMethod = SqlMethod.SELECT_COUNT;
        String.format(
            sqlMethod.getSql(), // "<script>%s SELECT %s FROM %s %s %s %s\n</script>"
            /*
            <if test="ew != null and ew.sqlFirst != null">
                ${ew.sqlFirst}
            </if>
            */
            sqlFirst(), 
            /*
            <choose>
                <when test="ew != null and ew.sqlSelect != null">
                    ${ew.sqlSelect}
                </when>
                <otherwise>test_id,name,age,price,test_type,`desc`,version,deleted,last_updated_dt</otherwise>
            </choose>
            */
            sqlSelectColumns(tableInfo, true), 
            tableInfo.getTableName(), // 表名：entity
            /*
            <where>
                deleted=0
                <if test="ew != null">
                    <bind name="_sgEs_" value="ew.sqlSegment != null and ew.sqlSegment != ''"/>
                    <if test="ew.entity != null">
                        <if test="ew.entity.testId != null"> AND test_id=#{ew.entity.testId}</if>
                        <if test="ew.entity['name'] != null"> AND name=#{ew.entity.name}</if>
                        <if test="ew.entity['age'] != null"> AND age=#{ew.entity.age}</if>
                        <if test="ew.entity['price'] != null"> AND price=#{ew.entity.price}</if>
                        <if test="ew.entity['testType'] != null"> AND test_type=#{ew.entity.testType}</if>
                        <if test="ew.entity['desc'] != null"> AND `desc`=#{ew.entity.desc}</if>
                        <if test="ew.entity['testDate'] != null"> AND test_date=#{ew.entity.testDate}</if>
                        <if test="ew.entity['version'] != null"> AND version=#{ew.entity.version}</if>
                        <if test="ew.entity['lastUpdatedDt'] != null"> AND last_updated_dt=#{ew.entity.lastUpdatedDt}</if>
                    </if>
                    <if test="_sgEs_ and ew.nonEmptyOfNormal">
                        AND ${ew.sqlSegment}
                    </if>
                    <if test="_sgEs_ and ew.emptyOfNormal">
                        ${ew.sqlSegment}
                    </if>
                </if>
            </where>
            */
            sqlWhereEntityWrapper(true, tableInfo), 
            sqlOrderBy(tableInfo), // 空
            /*
            <if test="ew != null and ew.sqlComment != null">
                ${ew.sqlComment}
            </if>
            */
            sqlComment()
        );
        SqlSource sqlSource = super.createSqlSource(configuration, sql, modelClass);
        return this.addSelectMappedStatementForOther(mapperClass, methodName, sqlSource, Long.class); // ref: sign_m_171
    }
```

#### 总结
- 大部分扩展自 MyBatis 已有类，扩展的类使用 `Mybatis` 前缀


### Spring 集成
- 单测关键类：
  - `com.baomidou.mybatisplus.test.h2.config.DBConfig`
  - `com.baomidou.mybatisplus.test.h2.config.MybatisPlusConfig`
- Spring-Boot 关键类:
  - `com.baomidou.mybatisplus.autoconfigure.MybatisPlusAutoConfiguration`
  - 数据源（连接池）通过 `# sqlSessionFactory(DataSource)` 方法设置
- 注解扫描：
  - 示例 `@MapperScan("com.baomidou.mybatisplus.test.h2.mapper")`
  - 参考：[MyBatis-Spring-集成](MyBatis.md#Spring-集成)


### SQL 格式化
- `org.apache.ibatis.executor.CachingExecutor #query(MS, p, RB, RH)` 调用
- `org.apache.ibatis.mapping.MappedStatement #getBoundSql` 主要逻辑在这里