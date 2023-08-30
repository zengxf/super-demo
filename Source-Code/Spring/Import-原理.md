## 内容
- 介绍 `@Import` 原理
- 引子参考：[Configuration-加载原理](Configuration-加载原理.md)

## 单元测试
```java
// 参考：ImportTests
public class MyImportTest {
	@Test
	public void test() {
		DefaultListableBeanFactory beanFactory = new DefaultListableBeanFactory();
		beanFactory.registerBeanDefinition("config", new RootBeanDefinition(MainCfg.class));

		ConfigurationClassPostProcessor pp = new ConfigurationClassPostProcessor();
		pp.postProcessBeanFactory(beanFactory); // 这里处理 @Import

		System.out.println("bean-count: " + beanFactory.getBeanDefinitionCount());
		System.out.println("bean-one-v: " + beanFactory.getBean("one"));
		System.out.println("bean-two-v: " + beanFactory.getBean("two"));
	}

	@Configuration
	@Import(OtherCfg.class)
	static class MainCfg {
		@Bean
		Object one() {
			return "111111";
		}
	}

	@Configuration
	static class OtherCfg {
		@Bean
		Object two() {
			return "222222";
		}
	}
}
```

### 打印栈
- 在 `org.springframework.context.annotation.ConfigurationClassParser #processImports` 加点东西
```java
	private void processImports(ConfigurationClass configClass, SourceClass currentSourceClass,
			Collection<SourceClass> importCandidates, Predicate<String> exclusionFilter,
			boolean checkForCircularImports) {

		new RuntimeException("栈跟踪").printStackTrace(); // 输出栈信息
        ...
    }
```
- 栈输出：
```js
java.lang.RuntimeException: 栈跟踪
	at org.springframework.context.annotation.ConfigurationClassParser.processImports(ConfigurationClassParser.java:471)
	at org.springframework.context.annotation.ConfigurationClassParser.doProcessConfigurationClass(ConfigurationClassParser.java:304)
	at org.springframework.context.annotation.ConfigurationClassParser.processConfigurationClass(ConfigurationClassParser.java:243)
	at org.springframework.context.annotation.ConfigurationClassParser.parse(ConfigurationClassParser.java:192)
	at org.springframework.context.annotation.ConfigurationClassParser.parse(ConfigurationClassParser.java:167)
	at org.springframework.context.annotation.ConfigurationClassPostProcessor.processConfigBeanDefinitions(ConfigurationClassPostProcessor.java:415)
	at org.springframework.context.annotation.ConfigurationClassPostProcessor.postProcessBeanFactory(ConfigurationClassPostProcessor.java:305)
	at org.springframework.context.annotation.test_my.MyImportTest.test(MyImportTest.java:23)
```    