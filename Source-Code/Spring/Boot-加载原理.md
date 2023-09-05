## Spring-Boot 原理

### Spring-Boot 条件注解
#### 单元测试
```java
public class MyPropertyTest {
    @Test
    void test() {
        ConfigurableEnvironment environment = new StandardEnvironment();
        TestPropertyValues.of(
                        "simple.my-property: test"
                )
                .applyTo(environment);
        ConfigurableApplicationContext context = new SpringApplicationBuilder(MyConfig.class)
                .environment(environment)
                .web(WebApplicationType.NONE)
                .run();
        System.out.println("contains-foo: " + context.containsBean("foo"));
        System.out.println("contains-foo1: " + context.containsBean("foo1"));
        System.out.println("contains-one: " + context.containsBean("one"));
        System.out.println("contains-two: " + context.containsBean("two"));
        System.out.println("contains-three: " + context.containsBean("three"));
        System.out.println("contains-three1: " + context.containsBean("three1"));
        System.out.println("contains-three2: " + context.containsBean("three2"));
    }

    @Configuration(proxyBeanMethods = false)
    static class MyConfig {
        @Bean // 配置值与 havingValue 值不匹配，不创建
        @ConditionalOnProperty(prefix = "simple", name = "my-property", havingValue = "1111", matchIfMissing = true)
        String foo() {
            return "foo";
        }

        @Bean // 配置值与 havingValue 值匹配，创建
        @ConditionalOnProperty(prefix = "simple", name = "my-property", havingValue = "test", matchIfMissing = true)
        String foo1() {
            return "foo1";
        }

        @Bean // 有 my-property 配置 key 且配置的值不为 false，创建。与 matchIfMissing 无关
        @ConditionalOnProperty(prefix = "simple", name = "my-property", matchIfMissing = false)
        String one() {
            return "one";
        }

        @Bean // 有 my-property 配置 key 且配置的值不为 false，创建。与 matchIfMissing 无关
        @ConditionalOnProperty(prefix = "simple", name = "my-property", matchIfMissing = true)
        String two() {
            return "two";
        }

        @Bean // 配置值与 havingValue 值匹配，创建
        @ConditionalOnProperty(prefix = "simple", name = "my-property", havingValue = "test")
        String three() {
            return "three";
        }

        @Bean // 没有 my-property2 配置 key 且 matchIfMissing 为 true，创建
        @ConditionalOnProperty(prefix = "simple", name = "my-property2", matchIfMissing = true)
        String three1() {
            return "three1";
        }

        @Bean // 没有 my-property2 配置 key 且 matchIfMissing 为 false，不创建
        @ConditionalOnProperty(prefix = "simple", name = "my-property2", matchIfMissing = false)
        String three2() {
            return "three2";
        }
    }
}
```

#### 原理
- 参考：[Configuration-加载原理-条件解析](Configuration-加载原理.md#条件解析)
- `org.springframework.boot.autoconfigure.condition.ConditionalOnProperty`
```java
/*** 属性配置条件注解 */
@Retention(RetentionPolicy.RUNTIME)
@Target({ ElementType.TYPE, ElementType.METHOD })
@Conditional(OnPropertyCondition.class) // 设置条件解析类
public @interface ConditionalOnProperty {
    /*** 前缀 */
    String prefix() default "";
    /*** 名称（属性 key） */
    String[] name() default {};
    /*** 条件值（如果没设置，则配置值不能为 false，否则算为不匹配） */
    String havingValue() default "";
    /*** true: 没有设置对应的属性，也表示为匹配上 */
    boolean matchIfMissing() default false;
}
```

- `org.springframework.boot.autoconfigure.condition.OnPropertyCondition`
```java
/*** 属性配置条件注解解析类 */
@Order(Ordered.HIGHEST_PRECEDENCE + 40)
class OnPropertyCondition extends SpringBootCondition {
    /*** 实现父类的钩子函数 */
    @Override
    public ConditionOutcome getMatchOutcome(ConditionContext context, AnnotatedTypeMetadata metadata) {
        List<AnnotationAttributes> allAnnotationAttributes = metadata.getAnnotations()
            .stream(ConditionalOnProperty.class.getName()) // 只解析 @ConditionalOnProperty 注解
            .filter(MergedAnnotationPredicates.unique(MergedAnnotation::getMetaTypes)) // 去重
            .map(MergedAnnotation::asAnnotationAttributes)
            .toList();
        List<ConditionMessage> noMatch = new ArrayList<>();
        List<ConditionMessage> match = new ArrayList<>();
        for (AnnotationAttributes annotationAttributes : allAnnotationAttributes) {
            ConditionOutcome outcome = determineOutcome(annotationAttributes, context.getEnvironment()); // 获取单个匹配结果
            (outcome.isMatch() ? match : noMatch).add(outcome.getConditionMessage()); // 匹配上就加入到已匹配集合，否则就加入到未匹配集合
        }
        if (!noMatch.isEmpty()) { // 只要有一个没匹配上，就返回无匹配（noMatch）
            return ConditionOutcome.noMatch(ConditionMessage.of(noMatch));
        }
        return ConditionOutcome.match(ConditionMessage.of(match)); // 返回有匹配（match）
    }

    // 进行单个匹配
    private ConditionOutcome determineOutcome(AnnotationAttributes annotationAttributes, PropertyResolver resolver) {
        Spec spec = new Spec(annotationAttributes);
        List<String> missingProperties = new ArrayList<>();     // 缺失的属性
        List<String> nonMatchingProperties = new ArrayList<>(); // 未匹配到值的属性
        // 进行匹配计算处理
        spec.collectProperties(resolver, missingProperties, nonMatchingProperties);
        if (!missingProperties.isEmpty()) { // 存在“缺失的属性”，返回匹配失败
            return ConditionOutcome.noMatch(ConditionMessage.forCondition(ConditionalOnProperty.class, spec);
        }
        if (!nonMatchingProperties.isEmpty()) { // 存在“未匹配到值的属性”，返回匹配失败
            return ConditionOutcome.noMatch(ConditionMessage.forCondition(ConditionalOnProperty.class, spec);
        }
        // 以上条件都未满足（没有"缺失的属性"及"未匹配到值的属性"），就相当于匹配成功
        return ConditionOutcome
            .match(ConditionMessage.forCondition(ConditionalOnProperty.class, spec).because("matched"));
    }

    /*** 内部类封装注解属性 */
    private static class Spec {
        ...
        // 匹配计算
        private void collectProperties(PropertyResolver resolver, List<String> missing, List<String> nonMatching) {
            for (String name : this.names) {
                String key = this.prefix + name;
                if (resolver.containsProperty(key)) { // 存在属性值
                    if (!isMatch(resolver.getProperty(key), this.havingValue)) { // 进入匹配计算
                        nonMatching.add(name);     // 属性值不匹配
                    }
                }
                else {
                    if (!this.matchIfMissing) {    // 不存在属性，且 @ConditionalOnProperty 的 matchIfMissing 值为 false
                        missing.add(name);        // 属性值缺失
                    }
                }
            }
        }

        // 属性值匹配计算
        private boolean isMatch(String value, String requiredValue) {
            if (StringUtils.hasLength(requiredValue)) { // @ConditionalOnProperty 的 havingValue 值不为空
                return requiredValue.equalsIgnoreCase(value); // 进行值匹配
            }
            return !"false".equalsIgnoreCase(value); // 注解的 havingValue 值为空，且配置的值不为 false，表示匹配成功，否则匹配失败
        }
    }
}
```

- `org.springframework.boot.autoconfigure.condition.SpringBootCondition`
  - 参考：[Configuration-加载原理-条件解析](Configuration-加载原理.md#条件解析)
```java
/*** Spring-Boot 条件注解解析父类 */
public abstract class SpringBootCondition implements Condition {
    @Override
    public final boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata) {
        ...
        try {
            ConditionOutcome outcome = getMatchOutcome(context, metadata); // 调用子类钩子函数
            ...
            return outcome.isMatch(); // 返回是否匹配
        }
        ... // 省略 catch
    }

    /*** 获取匹配结果（具体匹配结果，由子类实现） */
    public abstract ConditionOutcome getMatchOutcome(ConditionContext context, AnnotatedTypeMetadata metadata);
}
```

- **其他条件注解都是这种逻辑**
  - `@ConditionalOnBean`
  - `@ConditionalOnClass`
  - `@ConditionalOnExpression`
  - `@ConditionalOnResource`
  - `@ConditionalOnWebApplication`