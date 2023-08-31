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

## 原理
- `org.springframework.context.annotation.ConfigurationClassParser`
  - 会递归循环解析处理
```java
    // 处理配置类
    protected void processConfigurationClass(ConfigurationClass configClass, Predicate<String> filter) throws IOException {
        ...

        // Recursively process the configuration class and its superclass hierarchy.
        SourceClass sourceClass = asSourceClass(configClass, filter);
        do {
            sourceClass = doProcessConfigurationClass(configClass, sourceClass, filter); // 递归 S1
        }
        while (sourceClass != null);

        this.configurationClasses.put(configClass, configClass);
    }

    // 处理配置类（几种关键的注解）
    @Nullable
    protected final SourceClass doProcessConfigurationClass(
            ConfigurationClass configClass, SourceClass sourceClass, Predicate<String> filter)
            throws IOException {

        if (configClass.getMetadata().isAnnotated(Component.class.getName())) {
            // Recursively process any member (nested) classes first
            processMemberClasses(configClass, sourceClass, filter);
        }

        // Process any @PropertySource annotations
        ...

        // Process any @ComponentScan annotations
        ...

        // 处理 @Import 注解。getImports() 返回要导入的类
        processImports(configClass, sourceClass, getImports(sourceClass), filter, true); // 递归 S2

        // Process any @ImportResource annotations
        ...

        // Process individual @Bean methods
        ...

        // No superclass -> processing is complete
        return null;
    }

    // 处理导入
    private void processImports(ConfigurationClass configClass, SourceClass currentSourceClass,
            Collection<SourceClass> importCandidates, Predicate<String> exclusionFilter,
            boolean checkForCircularImports) {

        new RuntimeException("栈跟踪").printStackTrace();

        ... // 省略校验
        else {
            this.importStack.push(configClass);
            try {
                for (SourceClass candidate : importCandidates) {
                    if (candidate.isAssignable(ImportSelector.class)) {
                        ... // 省略处理
                    }
                    else if (candidate.isAssignable(ImportBeanDefinitionRegistrar.class)) {
                        ... // 省略处理
                    }
                    else {
                        // Candidate class not an ImportSelector or ImportBeanDefinitionRegistrar ->
                        // process it as an @Configuration class
                        this.importStack.registerImport(
                                currentSourceClass.getMetadata(), candidate.getMetadata().getClassName());
                        processConfigurationClass(candidate.asConfigClass(configClass), exclusionFilter); // 递归 S3
                    }
                }
            }
            ... // 省略 catch 处理
        }
    }
```