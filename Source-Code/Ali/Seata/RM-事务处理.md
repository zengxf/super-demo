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

    // 对默认数据源 (如：HikariDataSource) 进行 AOP 处理
    @Bean(...)
    @ConditionalOnMissingBean(SeataAutoDataSourceProxyCreator.class)
    public static SeataAutoDataSourceProxyCreator seataAutoDataSourceProxyCreator(SeataProperties seataProperties) {
        return new SeataAutoDataSourceProxyCreator(...);
    }

}
```