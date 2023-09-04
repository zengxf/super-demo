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
- `org.springframework.boot.autoconfigure.condition.ConditionalOnProperty`
```java
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